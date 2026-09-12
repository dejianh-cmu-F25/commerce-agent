"""Run the gold scenarios keylessly and report pass/fail (P7, TT-2).

Only the model is scripted (``MockLLMClient``); the loop, tools, and stores are
real. Assertions cover deterministic outcomes only (tool sequence, components,
cart) — never model prose.
"""

from __future__ import annotations

import asyncio
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.merchant_sqlite import SqliteMerchant
from app.adapters.mock_llm import MockLLMClient
from app.adapters.retriever_memory import InMemoryRetriever
from app.adapters.storefront_memory import InMemoryStorefront
from app.adapters.storefront_sqlite import SqliteStorefront
from app.core import events as ev
from app.core.loop import Agent
from app.core.session import Session
from app.core.settings import AgentSettings
from app.knowledge.ingest import load_chunks
from app.tools.cart import register_cart_tools
from app.tools.catalog import register_catalog_tools
from app.tools.knowledge import register_knowledge_tools
from app.tools.merchant import register_merchant_tools
from app.tools.registry import ToolRegistry
from evals.scenarios import SCENARIOS, Scenario

SYSTEM = "You are a commerce agent."
P101_PRICE = 189.0
KNOWLEDGE_DIR = str(Path(__file__).resolve().parents[1] / "config" / "knowledge")


@dataclass
class EvalResult:
    name: str
    ok: bool
    failures: list[str] = field(default_factory=list)


def _build_agent(scenario: Scenario, merchant: SqliteMerchant) -> Agent:
    registry = ToolRegistry()
    storefront = InMemoryStorefront(SEED_PRODUCTS)
    register_catalog_tools(registry, storefront)
    register_cart_tools(registry, storefront)
    retriever = InMemoryRetriever()
    retriever.add(load_chunks(KNOWLEDGE_DIR))
    register_knowledge_tools(registry, retriever)
    register_merchant_tools(registry, merchant)
    return Agent(
        llm=MockLLMClient(scenario.turns),
        tools=registry,
        settings=AgentSettings(max_turns=12),
        system_prompt=SYSTEM,
    )


async def _run_scenario(scenario: Scenario) -> EvalResult:
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "store.sqlite")
        SqliteStorefront(path)  # seed products for the merchant
        merchant = SqliteMerchant(path)
        agent = _build_agent(scenario, merchant)

        session = Session(id="eval")
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

        if scenario.name == "merchant_stage":
            # A staged change must not have modified the product (P3).
            price = merchant.list_products()[0].price
            if price != P101_PRICE:
                failures.append(f"merchant staged but applied: price {price} != {P101_PRICE}")

        return EvalResult(name=scenario.name, ok=not failures, failures=failures)


async def run_all() -> list[EvalResult]:
    return [await _run_scenario(scenario) for scenario in SCENARIOS]


def main() -> int:
    results = asyncio.run(run_all())
    width = max((len(result.name) for result in results), default=0)
    for result in results:
        print(f"{result.name:<{width}}  {'PASS' if result.ok else 'FAIL'}")
        for failure in result.failures:
            print(f"    - {failure}")
    failed = [result for result in results if not result.ok]
    print(f"\n{len(results) - len(failed)}/{len(results)} scenarios passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
