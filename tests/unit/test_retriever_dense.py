"""Unit tests for the dense retriever (feature 018)."""

from __future__ import annotations

from app.adapters.embedding_hash import HashEmbeddingProvider
from app.adapters.retriever_dense import DenseRetriever
from app.adapters.vector_memory import InMemoryVectorStore
from app.core.types import Chunk


def _retriever() -> DenseRetriever:
    return DenseRetriever(HashEmbeddingProvider(128), InMemoryVectorStore())


def test_add_is_idempotent_and_retrieve_ranks_by_source():
    retriever = _retriever()
    chunks = [
        Chunk(
            id="returns",
            text="Returns: a 30 day return policy and the refund process",
            source="amazon-returns.md",
        ),
        Chunk(id="shipping", text="Shipping: delivery times and carriers", source="shipping.md"),
    ]
    retriever.add(chunks)
    retriever.add(chunks)  # idempotent

    assert retriever.size() == 2
    hits = retriever.retrieve("return refund policy", 2)
    assert hits and hits[0].source == "amazon-returns.md"
    assert retriever.retrieve("   ") == []


def test_empty_corpus_returns_nothing():
    assert _retriever().retrieve("anything") == []
