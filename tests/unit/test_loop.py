"""Unit tests for the agent loop and the session log (feature 001)."""

from __future__ import annotations

from app.adapters.cli_sink import ListSink
from app.adapters.mock_llm import MockLLMClient, text_turn, tool_turn
from app.core import events as ev
from app.core.loop import Agent
from app.core.session import AssistantMessage, Session, ToolResultEvent, derive_messages
from app.core.settings import AgentSettings
from app.tools.catalog import register_catalog_tools
from app.tools.registry import ToolRegistry

SYSTEM = "You are a test assistant."


def make_agent(turns) -> Agent:
    registry = ToolRegistry()
    register_catalog_tools(registry)
    return Agent(
        llm=MockLLMClient(turns),
        tools=registry,
        settings=AgentSettings(max_turns=6),
        system_prompt=SYSTEM,
    )


async def test_loop_calls_tool_then_replies():
    agent = make_agent(
        [
            tool_turn("search_products", '{"query": "tent"}'),
            text_turn("Here is a tent."),
        ]
    )
    session = Session(id="s1")
    sink = ListSink()

    await agent.stream_turn(session, "I need a tent", sink)

    # The assistant requested a tool, then answered.
    assert any(isinstance(e, AssistantMessage) and e.tool_calls for e in session.events)
    assert any(isinstance(e, ToolResultEvent) and e.status == "ok" for e in session.events)
    assert isinstance(session.events[-1], AssistantMessage)
    assert session.events[-1].text == "Here is a tent."

    # Provenance only holds server-issued ids.
    assert "P-101" in session.provenance

    # Events reached the sink.
    assert sink.of_type(ev.ToolCallStarted)
    assert sink.of_type(ev.TurnEnd)[-1].reason == "stop"


async def test_unknown_tool_returns_error_without_ending_turn():
    agent = make_agent(
        [
            tool_turn("does_not_exist", "{}"),
            text_turn("Let me try something else."),
        ]
    )
    session = Session(id="s2")
    sink = ListSink()

    await agent.stream_turn(session, "do something odd", sink)

    blocked = [e for e in session.events if isinstance(e, ToolResultEvent)]
    assert blocked and blocked[0].status == "error"
    assert isinstance(session.events[-1], AssistantMessage)


async def test_max_turns_is_bounded():
    # The model keeps asking for a tool and never answers.
    agent = make_agent([tool_turn("search_products", '{"query": "tent"}')])
    agent._settings.max_turns = 3  # noqa: SLF001 - deliberate bound test
    session = Session(id="s3")
    sink = ListSink()

    await agent.stream_turn(session, "loop forever", sink)

    assert sink.of_type(ev.TurnEnd)[-1].reason == "max_turns"
    assert len([e for e in session.events if isinstance(e, AssistantMessage)]) == 3


def test_derive_messages_is_deterministic():
    session = Session(id="s4")
    from app.core.session import UserMessage

    session.append(UserMessage("hello"))
    first = derive_messages(session, SYSTEM)
    second = derive_messages(session, SYSTEM)
    assert first == second
    assert first[0].role == "system"
    assert first[1].role == "user"


async def test_tool_can_declare_a_ui_component():
    agent = make_agent(
        [
            tool_turn("search_products", '{"query": "tent"}'),
            text_turn("Here is a tent."),
        ]
    )
    session = Session(id="s5")
    sink = ListSink()

    await agent.stream_turn(session, "I need a tent", sink)

    # The loop forwards the tool-declared component without interpreting it.
    components = sink.of_type(ev.UIComponent)
    assert components and components[0].component == "products"
    assert components[0].payload["items"][0]["id"] == "P-101"
