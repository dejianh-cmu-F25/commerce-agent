"""FastAPI application: SSE chat, health checks, and static assets.

The web layer is a surface: it provides an EventSink and renders events. It
never builds model messages or calls the LLM directly (SL-1, HR-11).
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cost_meter import UsageCostMeter
from app.adapters.deepseek_client import DeepSeekClient
from app.adapters.mock_llm import MockLLMClient, text_turn
from app.adapters.storefront_memory import InMemoryStorefront
from app.adapters.storefront_sqlite import SqliteStorefront
from app.core import events as ev
from app.core.loop import Agent
from app.core.prompts import load_prompt
from app.core.settings import Settings, load_settings
from app.ports.storefront import StorefrontBackend
from app.tools.catalog import register_catalog_tools
from app.tools.registry import ToolRegistry
from web.sessions import SessionStore

STATIC_DIR = Path(__file__).parent / "static"
APP_DIR = STATIC_DIR / "app"


def build_llm(settings: Settings):
    provider = settings.llm.provider
    if provider == "mock":
        return MockLLMClient(
            [
                text_turn(
                    "I can help you find products. (Running in mock mode — "
                    "set LLM_API_KEY to use DeepSeek.)"
                )
            ]
        )
    return DeepSeekClient(settings.llm)


def build_storefront(settings: Settings) -> StorefrontBackend:
    """Resolve the storefront provider from configuration (PB-1, PB-3)."""
    if settings.storefront.provider == "memory":
        return InMemoryStorefront(SEED_PRODUCTS)
    return SqliteStorefront(settings.storefront.sqlite_path)


def build_agent(settings: Settings) -> Agent:
    registry = ToolRegistry()
    register_catalog_tools(registry, build_storefront(settings))
    return Agent(
        llm=build_llm(settings),
        tools=registry,
        settings=settings.agent,
        system_prompt=load_prompt("system"),
        cost_meter=UsageCostMeter(settings.budget),
    )


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class QueueSink:
    """An EventSink that hands events to an SSE generator."""

    def __init__(self) -> None:
        self.queue: asyncio.Queue[ev.AgentEvent] = asyncio.Queue()

    async def emit(self, event: ev.AgentEvent) -> None:
        await self.queue.put(event)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    app = FastAPI(title="Commerce Agent", version="0.1.0")
    store = SessionStore()
    agent = build_agent(settings)

    @app.get("/healthz")
    async def healthz() -> dict:
        return {"status": "ok"}

    @app.get("/readyz")
    async def readyz() -> dict:
        return {"status": "ready", "storefront": settings.storefront.provider}

    @app.get("/budget")
    async def budget() -> dict:
        meter = UsageCostMeter(settings.budget)
        return {
            "currency": settings.budget.currency,
            "spent": round(meter.spent_cny(), 4),
            "limit": meter.limit_cny(),
            "remaining": round(meter.remaining_cny(), 4),
        }

    @app.post("/chat")
    async def chat(request: ChatRequest) -> EventSourceResponse:
        session = store.get_or_create(request.session_id)
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


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    settings = load_settings()
    uvicorn.run(app, host=settings.web.host, port=settings.web.port)
