"""Integration tests for dense knowledge retrieval (feature 018)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.vector_chroma import ChromaVectorStore
from app.core.settings import (
    EmbeddingSettings,
    KnowledgeSettings,
    Settings,
    VectorStoreSettings,
)
from web.main import build_embedding, build_retriever, build_vector_store


def test_dense_retriever_answers_from_the_returns_document():
    settings = Settings(
        knowledge=KnowledgeSettings(provider="dense"),
        embedding=EmbeddingSettings(provider="hash", dimensions=256),
    )
    retriever = build_retriever(settings)

    hits = retriever.retrieve("what is the return policy and refund process?", 3)
    assert hits
    assert hits[0].source.endswith("amazon-returns.md")


def test_keyless_dense_needs_no_key():
    settings = Settings(
        knowledge=KnowledgeSettings(provider="dense"),
        embedding=EmbeddingSettings(provider="hash"),
    )
    provider = build_embedding(settings)
    assert len(provider.embed(["hello"])[0]) == settings.embedding.dimensions


def test_unimplemented_embedding_provider_fails_loud():
    with pytest.raises(ValueError):
        build_embedding(Settings(embedding=EmbeddingSettings(provider="ollama")))


def test_chroma_vector_store_builds(tmp_path: Path):
    settings = Settings(
        vector_store=VectorStoreSettings(
            provider="chroma", persist_directory=str(tmp_path / "chroma")
        )
    )
    assert isinstance(build_vector_store(settings), ChromaVectorStore)
