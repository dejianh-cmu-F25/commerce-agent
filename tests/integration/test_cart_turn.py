"""Integration test: a turn that adds to the cart emits a cart component (009)."""

from __future__ import annotations

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.mock_llm import MockLLMClient, text_turn, tool_turn
from app.adapters.storefront_memory import InMemoryStorefront
from app.core import events as ev
from app.core.loop import Agent
from app.core.session import Session
from app.core.settings import AgentSettings
from app.tools.cart import register_cart_tools
from app.tools.catalog import register_catalog_tools
from app.tools.registry import ToolRegistry


async def test_turn_emits_cart_component():
    registry = ToolRegistry()
    storefront = InMemoryStorefront(SEED_PRODUCTS)
    register_catalog_tools(registry, storefront)
    register_cart_tools(registry, storefront)

    agent = Agent(
        llm=MockLLMClient(
            [
                tool_turn("search_products", '{"query": "tent"}'),
                tool_turn("add_to_cart", '{"product_id": "P-101"}'),
                text_turn("Added the tent to your cart."),
            ]
        ),
        tools=registry,
        settings=AgentSettings(max_turns=8),
        system_prompt="sys",
    )

    session = Session(id="s1")
    sink = ListSink()
    await agent.stream_turn(session, "add the tent to my cart", sink)

    components = [event for event in sink.of_type(ev.UIComponent) if event.component == "cart"]
    assert components and components[0].payload["total"] == 189.0
    assert session.cart and session.cart[0].product_id == "P-101"
