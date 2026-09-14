"""Integration tests for the search_knowledge tool (feature 012)."""

from __future__ import annotations

from pathlib import Path

from app.adapters.retriever_memory import InMemoryRetriever
from app.core.session import Session
from app.knowledge.ingest import load_chunks
from app.tools.knowledge import register_knowledge_tools
from app.tools.registry import ToolRegistry

KNOWLEDGE_DIR = str(Path(__file__).resolve().parents[2] / "config" / "knowledge")


def _registry() -> ToolRegistry:
    retriever = InMemoryRetriever()
    retriever.add(load_chunks(KNOWLEDGE_DIR))
    registry = ToolRegistry()
    register_knowledge_tools(registry, retriever)
    return registry


async def test_search_knowledge_returns_sources():
    result = await _registry().execute(
        "search_knowledge", {"query": "return window"}, Session(id="s1")
    )
    assert result.status == "ok"
    assert "amazon-returns.md" in result.content


async def test_search_knowledge_no_match():
    result = await _registry().execute(
        "search_knowledge", {"query": "quantum flux capacitor"}, Session(id="s1")
    )
    assert result.content == "No relevant knowledge found."
