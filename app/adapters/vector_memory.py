"""In-process cosine vector store (Service Provider for
:class:`app.ports.vector_store.VectorStore`).

Keyless and dependency-free (P8). Chunks are keyed by id, so re-upserting is
idempotent (RD-2). Suitable for the small policy corpus.
"""

from __future__ import annotations

import math

from app.core.types import Chunk


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._vectors: dict[str, list[float]] = {}

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings must have the same length")
        for chunk, vector in zip(chunks, embeddings, strict=False):
            self._chunks[chunk.id] = chunk
            self._vectors[chunk.id] = vector

    def size(self) -> int:
        return len(self._chunks)

    def query(self, embedding: list[float], k: int = 3) -> list[Chunk]:
        scored: list[tuple[float, Chunk]] = []
        for chunk_id, vector in self._vectors.items():
            score = _cosine(embedding, vector)
            if score > 0:
                scored.append((score, self._chunks[chunk_id]))
        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [
            Chunk(id=chunk.id, text=chunk.text, source=chunk.source, score=round(score, 6))
            for score, chunk in scored[: max(1, k)]
        ]
