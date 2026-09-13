"""FastAPI application: SSE chat, health checks, and static assets.

The web layer is a surface: it provides an EventSink and renders events. It
never builds model messages or calls the LLM directly (SL-1, HR-11).
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cost_meter import UsageCostMeter
from app.adapters.deepseek_client import DeepSeekClient
from app.adapters.embedding_hash import HashEmbeddingProvider
from app.adapters.embedding_openai import OpenAIEmbeddingProvider
from app.adapters.memory_memory import InMemoryMemoryStore
from app.adapters.memory_sqlite import SqliteMemoryStore
from app.adapters.merchant_sqlite import SqliteMerchant
from app.adapters.mock_llm import MockLLMClient, text_turn
from app.adapters.retriever_dense import DenseRetriever
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.session_memory import InMemorySessionStore
from app.adapters.session_sqlite import SqliteSessionStore
from app.adapters.storefront_memory import InMemoryStorefront
from app.adapters.storefront_sqlite import SqliteStorefront
from app.adapters.tracer_jsonl import JsonlTracer, NullTracer
from app.adapters.vector_chroma import ChromaVectorStore
from app.adapters.vector_memory import InMemoryVectorStore
from app.core import events as ev
from app.core.loop import Agent
from app.core.metrics import summarize
from app.core.prompts import load_prompt
from app.core.resilience import FallbackLLM, FallbackRetriever
from app.core.session import derive_messages
from app.core.settings import Settings, load_settings
from app.core.types import Message
from app.knowledge.ingest import load_chunks
from app.ports.memory import MemoryStore
from app.ports.merchant import MerchantBackend
from app.ports.retriever import Retriever
from app.ports.session_store import SessionRepository
from app.ports.storefront import StorefrontBackend
from app.ports.tracer import Tracer
from app.skills.loader import SkillLibrary, load_skills
from app.tools.cart import register_cart_tools
from app.tools.catalog import register_catalog_tools
from app.tools.knowledge import register_knowledge_tools
from app.tools.merchant import register_merchant_tools
from app.tools.orders import register_order_tools
from app.tools.registry import ToolRegistry
from app.tools.skills import register_skill_tools
from evals.runner import run_scenarios
from evals.scenarios import SCENARIOS

STATIC_DIR = Path(__file__).parent / "static"
APP_DIR = STATIC_DIR / "app"
REPORT_PATH = Path(__file__).resolve().parents[1] / "evals" / "report.md"


def _build_llm_client(
    settings: Settings, *, provider: str, model: str, base_url: str, api_key: str
):
    if provider == "mock":
        return MockLLMClient(
            [
                text_turn(
                    "I can help you find products. (Running in mock mode — "
                    "set LLM_API_KEY to use DeepSeek.)"
                )
            ]
        )
    llm = settings.llm.model_copy(
        update={
            "provider": provider,
            "model": model or settings.llm.model,
            "base_url": base_url or settings.llm.base_url,
            "api_key": api_key or settings.llm.api_key,
        }
    )
    return DeepSeekClient(llm)


def build_llm(settings: Settings):
    """Resolve the LLM client, optionally wrapped with a fallback (feature 039)."""
    primary = _build_llm_client(
        settings,
        provider=settings.llm.provider,
        model=settings.llm.model,
        base_url=settings.llm.base_url,
        api_key=settings.llm.api_key,
    )
    if not settings.llm.fallback_provider:
        return primary
    secondary = _build_llm_client(
        settings,
        provider=settings.llm.fallback_provider,
        model=settings.llm.fallback_model,
        base_url=settings.llm.fallback_base_url,
        api_key=settings.llm.fallback_api_key,
    )
    return FallbackLLM(primary, secondary)


def build_storefront(settings: Settings) -> StorefrontBackend:
    """Resolve the storefront provider from configuration (PB-1, PB-3)."""
    if settings.storefront.provider == "memory":
        return InMemoryStorefront(SEED_PRODUCTS, seed_orders=settings.storefront.seed_orders)
    return SqliteStorefront(
        settings.storefront.sqlite_path,
        seed_orders=settings.storefront.seed_orders,
        quality=settings.data.quality,
    )


def build_session_store(settings: Settings) -> SessionRepository:
    """Resolve the session store from configuration (PB-1, PB-3)."""
    if settings.session.store == "memory":
        return InMemorySessionStore()
    return SqliteSessionStore(settings.session.sqlite_path)


def _product_dict(product) -> dict:
    return {
        "id": product.id,
        "title": product.title,
        "price": product.price,
        "stock": product.stock,
        "in_stock": product.in_stock,
    }


def _message_to_dict(message: Message) -> dict:
    data: dict = {"role": message.role, "content": message.content}
    if message.tool_calls:
        data["tool_calls"] = [
            {"id": c.id, "name": c.name, "arguments": c.arguments} for c in message.tool_calls
        ]
    if message.tool_call_id:
        data["tool_call_id"] = message.tool_call_id
    if message.name:
        data["name"] = message.name
    return data


def build_tracer(settings: Settings) -> Tracer:
    """Resolve the tracer from configuration (PB-1, PB-3)."""
    if not settings.observability.trace_enabled:
        return NullTracer()
    return JsonlTracer(settings.observability.trace_file, settings.observability.trace_max_attr_len)


def build_merchant(settings: Settings) -> MerchantBackend | None:
    """Resolve the merchant backend (PB-1). Requires the SQLite storefront."""
    if settings.storefront.provider != "sqlite":
        return None
    return SqliteMerchant(settings.storefront.sqlite_path)


def build_embedding(settings: Settings):
    """Resolve the embedding provider (PB-1). Keyless `hash` is the default."""
    provider = settings.embedding.provider
    if provider in ("hash", "mock"):
        return HashEmbeddingProvider(settings.embedding.dimensions)
    if provider == "openai":
        return OpenAIEmbeddingProvider(
            model=settings.embedding.model,
            api_key=settings.embedding.api_key,
            base_url=settings.embedding.base_url,
        )
    raise ValueError(f"Unknown embedding provider: {provider!r}")


def build_vector_store(settings: Settings):
    """Resolve the vector store provider (PB-1)."""
    provider = settings.vector_store.provider
    if provider == "memory":
        return InMemoryVectorStore()
    if provider == "chroma":
        return ChromaVectorStore(
            settings.vector_store.persist_directory, settings.vector_store.collection_name
        )
    raise ValueError(f"Unknown vector store provider: {provider!r}")


def build_retriever(settings: Settings) -> Retriever:
    """Load knowledge documents into the configured retriever (PB-1)."""
    chunks = load_chunks(settings.knowledge.path, settings.knowledge.min_chars)
    retriever: Retriever
    if settings.knowledge.provider == "dense":
        primary = DenseRetriever(build_embedding(settings), build_vector_store(settings))
        # Dense retrieval degrades to the keyless lexical retriever on an
        # embedding/vector-store outage (feature 031, RD-1).
        if settings.resilience.fallback_enabled:
            retriever = FallbackRetriever(primary, InMemoryRetriever())
        else:
            retriever = primary
    else:
        retriever = InMemoryRetriever()
    retriever.add(chunks)
    return retriever


def build_memory(settings: Settings) -> MemoryStore:
    """Resolve the customer memory provider from configuration (PB-1, PB-3)."""
    if settings.memory.provider == "memory":
        return InMemoryMemoryStore()
    return SqliteMemoryStore(settings.memory.sqlite_path)


def build_skill_library(settings: Settings) -> SkillLibrary:
    """Load skills from configuration (PB-1); disabled or missing yields none."""
    if not settings.skills.enabled:
        return SkillLibrary()
    return load_skills(settings.skills.path)


def build_agent(
    settings: Settings,
    tracer: Tracer | None = None,
    merchant: MerchantBackend | None = None,
    memory: MemoryStore | None = None,
) -> Agent:
    registry = ToolRegistry()
    storefront = build_storefront(settings)
    register_catalog_tools(registry, storefront)
    register_cart_tools(registry, storefront)
    register_order_tools(registry, storefront, settings.returns.window_days)
    register_knowledge_tools(registry, build_retriever(settings))
    if merchant is not None:
        register_merchant_tools(registry, merchant)

    system_prompt = load_prompt("system")
    skills = build_skill_library(settings)
    if len(skills) > 0:
        register_skill_tools(registry, skills)
        system_prompt += (
            "\n\n## Available skills\n"
            + skills.catalog()
            + "\n\nLoad a skill with the use_skill tool when it matches the request."
        )

    return Agent(
        llm=build_llm(settings),
        tools=registry,
        settings=settings.agent,
        system_prompt=system_prompt,
        cost_meter=UsageCostMeter(settings.budget),
        tracer=tracer,
        memory=memory,
        safety=settings.safety,
    )


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    customer_id: str | None = None


def _fact_dict(fact) -> dict:
    return {
        "id": fact.id,
        "kind": fact.kind,
        "text": fact.text,
        "created_at": fact.created_at,
    }


class QueueSink:
    """An EventSink that hands events to an SSE generator."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[ev.AgentEvent] = asyncio.Queue()

    async def emit(self, event: ev.AgentEvent) -> None:
        await self.queue.put(event)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Commerce Agent", version="0.1.0")
    store = build_session_store(settings)
    tracer = build_tracer(settings)
    merchant = build_merchant(settings)
    memory = build_memory(settings)
    agent = build_agent(settings, tracer, merchant, memory)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict:
        return {
            "status": "ready",
            "storefront": settings.storefront.provider,
            "memory": settings.memory.provider,
        }

    @app.get("/budget")
    async def budget() -> dict:
        meter = UsageCostMeter(settings.budget)
        return {
            "currency": settings.budget.currency,
            "spent": round(meter.spent_cny(), 4),
            "limit": meter.limit_cny(),
            "remaining": round(meter.remaining_cny(), 4),
        }

    @app.get("/sessions/{session_id}")
    async def get_session(session_id: str) -> dict:
        session = store.get(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="session not found")
        messages = derive_messages(session, "")
        return {
            "session_id": session.id,
            "messages": [_message_to_dict(m) for m in messages if m.role != "system"],
        }

    @app.get("/traces")
    async def list_traces(limit: int = 50) -> dict:
        return {"traces": [asdict(summary) for summary in tracer.list_traces(limit)]}

    @app.get("/metrics")
    async def metrics(limit: int = 2000) -> dict:
        window = max(1, min(limit, 20000))
        summary = summarize(tracer.recent_spans(window))
        meter = UsageCostMeter(settings.budget)
        return {
            "window": {"spans": summary.span_count, "limit": window},
            "spans": [asdict(stat) for stat in summary.spans],
            "tokens": {
                "prompt": summary.prompt_tokens,
                "completion": summary.completion_tokens,
                "cache_hit": summary.cache_hit_tokens,
                "cache_miss": summary.cache_miss_tokens,
            },
            "cost_cny": summary.cost_cny,
            "tools": {"ok": summary.tool_ok, "error": summary.tool_error},
            "budget": {
                "currency": settings.budget.currency,
                "spent": round(meter.spent_cny(), 4),
                "limit": meter.limit_cny(),
                "remaining": round(meter.remaining_cny(), 4),
            },
        }

    @app.get("/traces/{trace_id}")
    async def get_trace(trace_id: str) -> dict:
        spans = tracer.get_spans(trace_id)
        if not spans:
            raise HTTPException(status_code=404, detail="trace not found")
        return {"trace_id": trace_id, "spans": [asdict(span) for span in spans]}

    @app.get("/merchant/inventory")
    async def merchant_inventory() -> dict:
        if merchant is None:
            raise HTTPException(status_code=503, detail="merchant requires the sqlite storefront")
        return {"items": [_product_dict(product) for product in merchant.list_products()]}

    @app.get("/merchant/changes")
    async def merchant_changes() -> dict:
        if merchant is None:
            raise HTTPException(status_code=503, detail="merchant requires the sqlite storefront")
        return {"changes": [asdict(change) for change in merchant.pending()]}

    @app.post("/merchant/changes/{change_id}/apply")
    async def merchant_apply(change_id: str) -> dict:
        if merchant is None:
            raise HTTPException(status_code=503, detail="merchant requires the sqlite storefront")
        change = merchant.apply(change_id)
        if change is None:
            raise HTTPException(status_code=404, detail="change not found or already applied")
        return {"change": asdict(change)}

    @app.get("/report")
    async def report() -> dict:
        if not REPORT_PATH.exists():
            return {"markdown": ""}
        return {"markdown": REPORT_PATH.read_text(encoding="utf-8")}

    @app.get("/scenarios")
    async def list_scenarios() -> dict:
        return {
            "scenarios": [
                {
                    "name": scenario.name,
                    "user_text": scenario.user_text,
                    "expect_tools": scenario.expect_tools,
                    "expect_components": scenario.expect_components,
                }
                for scenario in SCENARIOS
            ]
        }

    @app.post("/scenarios/run")
    async def run_scenarios_endpoint() -> dict:
        results = await run_scenarios()
        return {"results": [asdict(result) for result in results]}

    @app.get("/memory/{customer_id}")
    async def memory_list(customer_id: str) -> dict:
        return {"facts": [_fact_dict(fact) for fact in memory.list(customer_id)]}

    @app.delete("/memory/{customer_id}/facts/{fact_id}")
    async def memory_forget(customer_id: str, fact_id: str) -> dict:
        if not memory.forget(customer_id, fact_id):
            raise HTTPException(status_code=404, detail="fact not found")
        return {"forgotten": fact_id}

    @app.delete("/memory/{customer_id}")
    async def memory_forget_all(customer_id: str) -> dict:
        return {"removed": memory.forget_all(customer_id)}

    @app.post("/chat")
    async def chat(request: ChatRequest) -> EventSourceResponse:
        session = store.get_or_create(request.session_id, request.customer_id or "")
        sink = QueueSink()

        async def event_stream() -> AsyncIterator[dict]:
            yield {
                "data": json.dumps({"type": "SessionStarted", "data": {"session_id": session.id}})
            }
            task = asyncio.create_task(agent.stream_turn(session, request.message, sink))
            try:
                while True:
                    event = await sink.queue.get()
                    yield {"data": json.dumps(ev.to_wire(event))}
                    if isinstance(event, ev.TurnEnd):
                        break
            finally:
                await task
                # Persist after the turn completes (one write per turn).
                store.save(session)

        return EventSourceResponse(event_stream())

    @app.get("/")
    async def index() -> FileResponse:
        return FileResponse(APP_DIR / "index.html")

    @app.get("/favicon.svg")
    async def favicon() -> FileResponse:
        return FileResponse(APP_DIR / "favicon.svg")

    # Hashed Vite assets; mounted only when a build is present so the app can be
    # imported (e.g. in unit tests) without a frontend build.
    assets_dir = APP_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
    return app


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    _settings = load_settings()
    uvicorn.run(create_app(_settings), host=_settings.web.host, port=_settings.web.port)
