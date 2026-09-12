"""Integration tests for tracing (feature 007).

Proves the loop emits turn/llm/tool spans with a shared trace_id, and that the
read API returns them.
"""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.cli_sink import ListSink
from app.adapters.mock_llm import MockLLMClient, text_turn, tool_turn
from app.adapters.storefront_memory import InMemoryStorefront
from app.adapters.tracer_jsonl import JsonlTracer
from app.core.loop import Agent
from app.core.session import Session
from app.core.settings import (
    AgentSettings,
    BudgetSettings,
    LLMSettings,
    ObservabilitySettings,
    SessionSettings,
    Settings,
    StorefrontSettings,
)
from app.core.types import Span
from app.tools.catalog import register_catalog_tools
from app.tools.registry import ToolRegistry
from web.main import create_app


async def test_turn_writes_turn_llm_and_tool_spans(tmp_path: Path):
    tracer = JsonlTracer(str(tmp_path / "traces.jsonl"))
    registry = ToolRegistry()
    register_catalog_tools(registry, InMemoryStorefront(SEED_PRODUCTS))
    agent = Agent(
        llm=MockLLMClient(
            [
                tool_turn("search_products", '{"query": "tent"}'),
                text_turn("Here is a tent."),
            ]
        ),
        tools=registry,
        settings=AgentSettings(max_turns=6),
        system_prompt="sys",
        tracer=tracer,
    )

    await agent.stream_turn(Session(id="s1"), "I need a tent", ListSink())

    summaries = tracer.list_traces()
    assert len(summaries) == 1
    spans = tracer.get_spans(summaries[0].trace_id)
    names = [span.name for span in spans]

    assert names.count("turn") == 1
    assert names.count("llm") == 2  # tool step + final answer
    assert names.count("tool") == 1
    assert all(span.trace_id == summaries[0].trace_id for span in spans)

    tool_span = next(span for span in spans if span.name == "tool")
    assert tool_span.attributes["name"] == "search_products"
    assert tool_span.parent_id is not None


def _settings(tmp_path: Path, trace_file: str) -> Settings:
    return Settings(
        llm=LLMSettings(provider="mock"),
        storefront=StorefrontSettings(provider="memory"),
        session=SessionSettings(store="memory"),
        budget=BudgetSettings(enabled=False, state_file=str(tmp_path / "budget.json")),
        observability=ObservabilitySettings(trace_file=trace_file),
    )


def test_traces_api_lists_and_fetches(tmp_path: Path):
    path = str(tmp_path / "traces.jsonl")
    seed = JsonlTracer(path)
    seed.record(
        Span(trace_id="t1", span_id="s1", name="turn", start_ms=1.0, end_ms=5.0, attributes={})
    )

    client = TestClient(create_app(_settings(tmp_path, path)))

    listing = client.get("/traces").json()
    assert listing["traces"][0]["trace_id"] == "t1"

    detail = client.get("/traces/t1").json()
    assert detail["spans"][0]["name"] == "turn"

    assert client.get("/traces/nope").status_code == 404
