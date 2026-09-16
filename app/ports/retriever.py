"""Knowledge retrieval capability: Service Definition (constitution P4, PB-2).

Answers about store policy must come from retrieved documents, not from the
model. Providers live in ``app/adapters`` and are selected by configuration
(PB-1).
"""

from __future__ import annotations

from typing import Any, Protocol

from app.core.types import Chunk


class Retriever(Protocol):
    def add(self, chunks: list[Chunk]) -> None:
        """Ingest chunks. Idempotent by chunk id (RD-2)."""
        ...

    def retrieve(self, query: str, k: int = 3, where: dict[str, Any] | None = None) -> list[Chunk]:
        """Return at most ``k`` chunks with a positive score, best first.

        ``where`` restricts the candidates to chunks whose ``metadata`` matches
        every condition (feature 047); ``None`` means no filter. An empty query or
        no matches returns ``[]``.
        """
        ...
