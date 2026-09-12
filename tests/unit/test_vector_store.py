"""Unit tests for the in-process vector store (feature 018)."""

from __future__ import annotations

import pytest

from app.adapters.vector_memory import InMemoryVectorStore
from app.core.types import Chunk


def _chunks() -> list[Chunk]:
    return [
        Chunk(id="a", text="alpha", source="a.md"),
        Chunk(id="b", text="beta", source="b.md"),
    ]


def test_upsert_is_idempotent_and_query_ranks():
    store = InMemoryVectorStore()
    store.upsert(_chunks(), [[1.0, 0.0], [0.0, 1.0]])
    store.upsert(_chunks(), [[1.0, 0.0], [0.0, 1.0]])  # idempotent by id

    assert store.size() == 2
    hits = store.query([1.0, 0.0], 1)
    assert hits and hits[0].id == "a"
    assert store.query([0.0, 0.0]) == []  # no positive similarity


def test_mismatched_lengths_raise():
    store = InMemoryVectorStore()
    with pytest.raises(ValueError):
        store.upsert(_chunks(), [[1.0, 0.0]])
