"""Dense retriever (Service Provider for
:class:`app.ports.retriever.Retriever`).

Wires an :class:`~app.ports.embedding.EmbeddingProvider` to a
:class:`~app.ports.vector_store.VectorStore`. Ingestion embeds and upserts each
chunk once (idempotent by id, RD-2); retrieval embeds the query and asks the
store for the nearest chunks.
"""

from __future__ import annotations

from typing import Any

from app.core.types import Chunk
from app.ports.embedding import EmbeddingProvider
from app.ports.vector_store import VectorStore


class DenseRetriever:
    def __init__(self, embedding: EmbeddingProvider, store: VectorStore) -> None:
        self._embedding = embedding
        self._store = store
        self._ids: set[str] = set()

    def add(self, chunks: list[Chunk]) -> None:
        fresh = [chunk for chunk in chunks if chunk.id not in self._ids]
        if not fresh:
            return
        vectors = self._embedding.embed([chunk.text for chunk in fresh])
        self._store.upsert(fresh, vectors)
        self._ids.update(chunk.id for chunk in fresh)

    def size(self) -> int:
        return self._store.size()

    def retrieve(self, query: str, k: int = 3, where: dict[str, Any] | None = None) -> list[Chunk]:
        if not query.strip():
            return []
        vector = self._embedding.embed([query])[0]
        return self._store.query(vector, k, where)
