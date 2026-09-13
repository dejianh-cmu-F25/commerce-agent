"""Reusable keyless scenario runner (features 011, 016, 023).

The gate CLI (``evals/run.py``), the web Scenario Runner, and the ablation all
call ``run_scenarios`` so their results cannot drift. Only the model is scripted
(``MockLLMClient``); the loop, tools, and stores are real. Assertions cover
deterministic outcomes only (tool sequence, components, cart, memory) — never
model prose. Each scenario runs on fresh in-memory/temporary resources, so a run
never touches live state (P3, RD-2).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.embedding_hash import HashEmbeddingProvider
from app.adapters.memory_memory import InMemoryMemoryStore
from app.adapters.merchant_sqlite import SqliteMerchant
from app.adapters.mock_llm import MockLLMClient
from app.adapters.retriever_dense import DenseRetriever
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.storefront_memory import InMemoryStorefront
from app.adapters.storefront_sqlite import SqliteStorefront
from app.adapters.vector_chroma import ChromaVectorStore
from app.adapters.vector_memory import InMemoryVectorStore
from app.core import events as ev
from app.core.loop import Agent
from app.core.session import MemoryNote, Session
from app.core.settings import AgentSettings
from app.core.types import MemoryFact
from app.knowledge.ingest import load_chunks
from app.ports.retriever import Retriever
from app.skills.loader import load_skills
from app.tools.cart import register_cart_tools
from app.tools.catalog import register_catalog_tools
from app.tools.knowledge import register_knowledge_tools
from app.tools.merchant import register_merchant_tools
from app.tools.orders import register_order_tools
from app.tools.registry import ToolRegistry
from app.tools.skills import register_skill_tools
from evals.scenarios import SCENARIOS, Scenario

SYSTEM = "You are a commerce agent."
P101_PRICE = 189.0
EVAL_CUSTOMER = "eval"
KNOWLEDGE_DIR = str(Path(__file__).resolve().parents[1] / "config" / "knowledge")
SKILLS_DIR = str(Path(__file__).resolve().parents[1] / "skills")
EMBEDDING_DIMS = 256
# Scenarios that intentionally produce a tool error.
EXPECT_ERROR_SCENARIOS = {"ungrounded_add_rejected", "return_out_of_window"}


@dataclass
class RunConfig:
    use_memory: bool = True
    use_skills: bool = True
    knowledge: str = "memory"  # memory | dense-hash | dense-chroma


@dataclass
class ScenarioResult:
    name: str
    ok: bool
    intent: str = ""
    failures: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    components: list[str] = field(default_factory=list)
    tool_results: list[tuple[str, str]] = field(default_factory=list)


def _build_retriever(knowledge: str, tmp_dir: str) -> Retriever:
    chunks = load_chunks(KNOWLEDGE_DIR)
    retriever: Retriever
    if knowledge == "memory":
        retriever = InMemoryRetriever()
    elif knowledge == "dense-hash":
        retriever = DenseRetriever(HashEmbeddingProvider(EMBEDDING_DIMS), InMemoryVectorStore())
    elif knowledge == "dense-chroma":
        retriever = DenseRetriever(
            HashEmbeddingProvider(EMBEDDING_DIMS),
            ChromaVectorStore(tmp_dir, "knowledge-eval"),
        )
    else:
        raise ValueError(f"unknown knowledge config: {knowledge}")
    retriever.add(chunks)
    return retriever


def _build_agent(
    scenario: Scenario,
    merchant: SqliteMerchant,
    memory: InMemoryMemoryStore | None,
    config: RunConfig,
    tmp_dir: str,
) -> Agent:
    registry = ToolRegistry()
    storefront = InMemoryStorefront(SEED_PRODUCTS)
    register_catalog_tools(registry, storefront)
    register_cart_tools(registry, storefront)
    register_order_tools(registry, storefront, 30)
    register_knowledge_tools(registry, _build_retriever(config.knowledge, tmp_dir))
    if config.use_skills:
        register_skill_tools(registry, load_skills(SKILLS_DIR))
    register_merchant_tools(registry, merchant)
    return Agent(
        llm=MockLLMClient(scenario.turns),
        tools=registry,
        settings=AgentSettings(max_turns=12),
        system_prompt=SYSTEM,
        memory=memory,
    )


def _seed_memory(memory: InMemoryMemoryStore, scenario: Scenario) -> None:
    for kind, text in scenario.seed_memory:
        memory.add(
            MemoryFact(
                id=uuid4().hex[:12],
                customer_id=EVAL_CUSTOMER,
                kind=kind,
                text=text,
                created_at=datetime.now(UTC).isoformat(),
            )
        )


async def _run_scenario(scenario: Scenario, config: RunConfig) -> ScenarioResult:
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "store.sqlite")
        SqliteStorefront(path)  # seed products for the merchant
        merchant = SqliteMerchant(path)
        memory = InMemoryMemoryStore() if config.use_memory else None
        if memory is not None:
            _seed_memory(memory, scenario)
        agent = _build_agent(scenario, merchant, memory, config, tmp)

        session = Session(id="eval", customer_id=EVAL_CUSTOMER)
        sink = ListSink()
        await agent.stream_turn(session, scenario.user_text, sink)

        failures: list[str] = []
        tools = [event.name for event in sink.of_type(ev.ToolCallStarted)]
        if tools != scenario.expect_tools:
            failures.append(f"tools {tools!r} != {scenario.expect_tools!r}")

        components = [event.component for event in sink.of_type(ev.UIComponent)]
        if components != scenario.expect_components:
            failures.append(f"components {components!r} != {scenario.expect_components!r}")

        cart = [(line.product_id, line.quantity) for line in session.cart]
        if cart != scenario.expect_cart:
            failures.append(f"cart {cart!r} != {scenario.expect_cart!r}")

        errors = [event for event in sink.of_type(ev.ToolResult) if event.status == "error"]
        if errors and scenario.name not in EXPECT_ERROR_SCENARIOS:
            failures.append(f"unexpected tool error: {errors[0].summary}")

        stored = [fact.text for fact in memory.list(EVAL_CUSTOMER)] if memory else []
        for text in scenario.expect_memory:
            if text not in stored:
                failures.append(f"memory {text!r} not stored (have {stored!r})")
        recalled = [
            fact for note in session.events if isinstance(note, MemoryNote) for fact in note.facts
        ]
        for text in scenario.expect_recall:
            if text not in recalled:
                failures.append(f"memory {text!r} not recalled (have {recalled!r})")

        if scenario.name == "merchant_stage":
            # A staged change must not have modified the product (P3).
            price = merchant.list_products()[0].price
            if price != P101_PRICE:
                failures.append(f"merchant staged but applied: price {price} != {P101_PRICE}")

        return ScenarioResult(
            name=scenario.name,
            ok=not failures,
            intent=scenario.intent,
            failures=failures,
            tools=tools,
            components=components,
            tool_results=[(event.name, event.status) for event in sink.of_type(ev.ToolResult)],
        )


async def run_scenarios(config: RunConfig | None = None) -> list[ScenarioResult]:
    config = config or RunConfig()
    return [await _run_scenario(scenario, config) for scenario in SCENARIOS]
