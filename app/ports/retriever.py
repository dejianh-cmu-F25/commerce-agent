"""Knowledge retrieval capability: Service Definition (constitution P4, PB-2).

Answers about store policy must come from retrieved documents, not from the
model. Providers live in ``app/adapters`` and are selected by configuration
(PB-1).
"""

from __future__ import annotations

from typing import Protocol

from app.core.types import Chunk


class Retriever(Protocol):
    def add(self, chunks: list[Chunk]) -> None:
        """Ingest chunks. Idempotent by chunk id (RD-2)."""
        ...

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        """Return at most ``k`` chunks with a positive score, best first.

        An empty query or no matches returns ``[]``.
        """
        ...
