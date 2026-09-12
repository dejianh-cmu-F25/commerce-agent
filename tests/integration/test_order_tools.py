"""Integration tests for the post-purchase tools over the loop (feature 014)."""

from __future__ import annotations

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.mock_llm import MockLLMClient, text_turn, tool_turn
from app.adapters.storefront_memory import InMemoryStorefront
from app.core import events as ev
from app.core.loop import Agent
from app.core.session import Session
from app.core.settings import AgentSettings
from app.tools.orders import register_order_tools
from app.tools.registry import ToolRegistry

SYSTEM = "You are a test assistant."


def _agent(turns) -> Agent:
    registry = ToolRegistry()
    register_order_tools(registry, InMemoryStorefront(SEED_PRODUCTS), 30)
    return Agent(
        llm=MockLLMClient(turns),
        tools=registry,
        settings=AgentSettings(max_turns=8),
        system_prompt=SYSTEM,
    )


async def test_status_then_return_renders_cards():
    agent = _agent(
        [
            tool_turn("list_orders", "{}", call_id="o1"),
            tool_turn("get_order_status", '{"order_id": "O-1001"}', call_id="o2"),
            tool_turn(
                "start_return", '{"order_id": "O-1001", "product_id": "P-101"}', call_id="o3"
            ),
            text_turn("Done."),
        ]
    )
    session = Session(id="s1", customer_id="c1")
    sink = ListSink()

    await agent.stream_turn(session, "where is my order? I want to return the tent", sink)

    assert [event.component for event in sink.of_type(ev.UIComponent)] == [
        "orders",
        "order",
        "return",
    ]
    assert "O-1001" in session.provenance  # server-issued id remembered


async def test_unknown_order_id_is_rejected():
    agent = _agent(
        [
            tool_turn("get_order_status", '{"order_id": "O-9999"}', call_id="o1"),
            text_turn("Let me list your orders first."),
        ]
    )
    session = Session(id="s2", customer_id="c1")
    sink = ListSink()

    await agent.stream_turn(session, "status of O-9999", sink)

    results = sink.of_type(ev.ToolResult)
    assert results and results[0].status == "error"
    assert not sink.of_type(ev.UIComponent)


async def test_out_of_window_return_is_refused():
    agent = _agent(
        [
            tool_turn("list_orders", "{}", call_id="o1"),
            tool_turn(
                "start_return", '{"order_id": "O-1002", "product_id": "P-104"}', call_id="o2"
            ),
            text_turn("That order is outside the return window."),
        ]
    )
    session = Session(id="s3", customer_id="c1")
    sink = ListSink()

    await agent.stream_turn(session, "return the backpack", sink)

    components = [event.component for event in sink.of_type(ev.UIComponent)]
    assert components == ["orders"]  # no return card
    assert any(event.status == "error" for event in sink.of_type(ev.ToolResult))
