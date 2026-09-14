"""Integration tests for the Chroma vector store (feature 021)."""

from __future__ import annotations

from pathlib import Path

from app.adapters.embedding_hash import HashEmbeddingProvider
from app.adapters.vector_chroma import ChromaVectorStore
from app.adapters.vector_memory import InMemoryVectorStore
from app.core.types import Chunk


def _chunks() -> list[Chunk]:
    return [
        Chunk(id="returns", text="returns policy refund window", source="amazon-returns.md"),
        Chunk(id="shipping", text="shipping delivery carriers", source="shipping.md"),
        Chunk(id="warranty", text="warranty defects coverage", source="warranty.md"),
    ]


def _vectors(chunks: list[Chunk]) -> list[list[float]]:
    return HashEmbeddingProvider(128).embed([chunk.text for chunk in chunks])


def test_parity_with_in_memory_store(tmp_path: Path):
    chunks = _chunks()
    vectors = _vectors(chunks)

    memory = InMemoryVectorStore()
    chroma = ChromaVectorStore(str(tmp_path / "chroma"), "knowledge-test")
    memory.upsert(chunks, vectors)
    chroma.upsert(chunks, vectors)

    query = HashEmbeddingProvider(128).embed(["return refund policy"])[0]
    memory_hits = memory.query(query, 3)
    chroma_hits = chroma.query(query, 3)

    assert memory_hits and chroma_hits
    assert memory_hits[0].id == chroma_hits[0].id == "returns"
    assert {hit.id for hit in memory_hits} == {hit.id for hit in chroma_hits}


def test_upsert_is_idempotent_and_persists(tmp_path: Path):
    chunks = _chunks()
    vectors = _vectors(chunks)
    directory = str(tmp_path / "chroma")

    store = ChromaVectorStore(directory, "knowledge-test")
    store.upsert(chunks, vectors)
    store.upsert(chunks, vectors)  # idempotent by chunk id (RD-2)
    assert store.size() == 3

    reopened = ChromaVectorStore(directory, "knowledge-test")
    assert reopened.size() == 3  # persisted (DP-6)


def test_empty_store_returns_nothing(tmp_path: Path):
    store = ChromaVectorStore(str(tmp_path / "chroma"), "knowledge-test")
    assert store.size() == 0
    assert store.query([1.0, 0.0]) == []
