"""Hybrid (RRF) retriever (feature 046)."""

from __future__ import annotations

from app.adapters.retriever_hybrid import HybridRetriever
from app.core.types import Chunk


class _FakeRetriever:
    def __init__(self, order: list[str]) -> None:
        self._order = order

    def add(self, chunks: list[Chunk]) -> None:  # pragma: no cover - not used
        pass

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        return [Chunk(id=cid, text=cid, source=cid) for cid in self._order[:k]]


def test_rrf_fuses_both_rankings() -> None:
    sparse = _FakeRetriever(["a", "b", "c"])
    dense = _FakeRetriever(["c", "a", "d"])
    hybrid = HybridRetriever(sparse, dense, rrf_k=60, candidate_k=3)
    ids = [chunk.id for chunk in hybrid.retrieve("q", 3)]
    # 'a' is ranked highly by both -> first; 'c' second
    assert ids[0] == "a"
    assert set(ids) == {"a", "b", "c"} or ids[:2] == ["a", "c"]


def test_empty_query() -> None:
    hybrid = HybridRetriever(_FakeRetriever([]), _FakeRetriever([]))
    assert hybrid.retrieve("  ", 3) == []
