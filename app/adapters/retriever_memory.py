"""In-memory TF-IDF retriever (Service Provider for
:class:`app.ports.retriever.Retriever`).

Keyless and dependency-free (P8). Adding a chunk id that already exists is a
no-op, so re-ingestion does not duplicate chunks (RD-2).
"""

from __future__ import annotations

import math
import re
from collections import Counter

from app.core.types import Chunk

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class InMemoryRetriever:
    def __init__(self) -> None:
        self._chunks: dict[str, Chunk] = {}
        self._term_counts: dict[str, Counter[str]] = {}
        self._doc_freq: Counter[str] = Counter()

    def add(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            if chunk.id in self._chunks:
                continue  # idempotent (RD-2)
            counts = Counter(_tokens(chunk.text))
            self._chunks[chunk.id] = chunk
            self._term_counts[chunk.id] = counts
            for term in counts:
                self._doc_freq[term] += 1

    def size(self) -> int:
        return len(self._chunks)

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        terms = set(_tokens(query))
        if not terms or not self._chunks:
            return []

        total = len(self._chunks)
        scored: list[tuple[float, Chunk]] = []
        for chunk_id, counts in self._term_counts.items():
            score = 0.0
            for term in terms:
                tf = counts.get(term, 0)
                if tf == 0:
                    continue
                idf = math.log((1 + total) / (1 + self._doc_freq[term])) + 1.0
                score += (1.0 + math.log(tf)) * idf
            if score > 0:
                scored.append((score, self._chunks[chunk_id]))

        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [
            Chunk(id=chunk.id, text=chunk.text, source=chunk.source, score=round(score, 6))
            for score, chunk in scored[: max(1, k)]
        ]
