"""Unit tests for the in-memory retriever (feature 012)."""

from __future__ import annotations

from app.adapters.retriever_memory import InMemoryRetriever
from app.core.types import Chunk


def _chunks() -> list[Chunk]:
    return [
        Chunk(
            id="amazon-returns.md#0",
            text="You may return most items within 30 days of delivery for a full refund.",
            source="amazon-returns.md",
        ),
        Chunk(
            id="shipping.md#0",
            text="Standard shipping takes 3 to 5 business days and costs 6 dollars.",
            source="shipping.md",
        ),
        Chunk(
            id="warranty.md#0",
            text="All outdoor gear carries a one-year manufacturer warranty against defects.",
            source="warranty.md",
        ),
    ]


def test_ranking_prefers_the_right_document():
    retriever = InMemoryRetriever()
    retriever.add(_chunks())
    hits = retriever.retrieve("what is your return policy?", 3)
    assert hits and hits[0].source == "amazon-returns.md"


def test_add_is_idempotent():
    retriever = InMemoryRetriever()
    retriever.add(_chunks())
    retriever.add(_chunks())
    assert retriever.size() == 3


def test_empty_query_and_no_match():
    retriever = InMemoryRetriever()
    retriever.add(_chunks())
    assert retriever.retrieve("") == []
    assert retriever.retrieve("zzzz") == []
