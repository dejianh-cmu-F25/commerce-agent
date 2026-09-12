"""Integration tests for the skills tool and catalog (feature 019)."""

from __future__ import annotations

from app.adapters.cli_sink import ListSink
from app.adapters.mock_llm import MockLLMClient, text_turn, tool_turn
from app.core import events as ev
from app.core.loop import Agent
from app.core.session import Session, ToolResultEvent
from app.core.settings import (
    AgentSettings,
    BudgetSettings,
    LLMSettings,
    SessionSettings,
    Settings,
    StorefrontSettings,
)
from app.skills.loader import Skill, SkillLibrary
from app.tools.registry import ToolRegistry
from app.tools.skills import register_skill_tools
from web.main import build_agent


def _library() -> SkillLibrary:
    return SkillLibrary([Skill("trip-planning", "Plan a trip", "Step 1. Step 2.")])


def _agent(turns) -> Agent:
    registry = ToolRegistry()
    register_skill_tools(registry, _library())
    return Agent(
        llm=MockLLMClient(turns),
        tools=registry,
        settings=AgentSettings(max_turns=4),
        system_prompt="You are a test assistant.",
    )


async def test_use_skill_returns_the_body():
    agent = _agent(
        [
            tool_turn("use_skill", '{"name": "trip-planning"}', call_id="s1"),
            text_turn("Done."),
        ]
    )
    session = Session(id="s1")
    await agent.stream_turn(session, "plan a trip", ListSink())

    contents = [event.content for event in session.events if isinstance(event, ToolResultEvent)]
    assert any("Step 1" in content for content in contents)


async def test_unknown_skill_is_an_error():
    agent = _agent(
        [
            tool_turn("use_skill", '{"name": "nope"}', call_id="s1"),
            text_turn("Let me try something else."),
        ]
    )
    session = Session(id="s2")
    sink = ListSink()
    await agent.stream_turn(session, "load nope", sink)

    results = sink.of_type(ev.ToolResult)
    assert results and results[0].status == "error"


def test_build_agent_advertises_skills_in_the_system_prompt():
    settings = Settings(
        llm=LLMSettings(provider="mock"),
        storefront=StorefrontSettings(provider="memory"),
        session=SessionSettings(store="memory"),
        budget=BudgetSettings(enabled=False),
    )
    agent = build_agent(settings)
    system = agent.build_request(Session(id="s"))[0].content
    assert "## Available skills" in system
    assert "trip-planning" in system
