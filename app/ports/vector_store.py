"""Vector store capability: Service Definition (constitution PB-2).

Stores chunk vectors and answers nearest-neighbour queries. Providers live in
``app/adapters`` and are selected by configuration (PB-1). Upsert is keyed by
chunk id, so re-ingestion does not duplicate vectors (RD-2).
"""

from __future__ import annotations

from typing import Protocol

from app.core.types import Chunk


class VectorStore(Protocol):
    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Insert or replace chunks and their vectors, keyed by chunk id."""
        ...

    def query(self, embedding: list[float], k: int = 3) -> list[Chunk]:
        """Return at most ``k`` chunks with a positive similarity, best first."""
        ...

    def size(self) -> int:
        """Return the number of stored chunks."""
        ...
