"""In-memory BM25 retriever (Service Provider for
:class:`app.ports.retriever.Retriever`).

A second lexical leg next to the TF-IDF :class:`InMemoryRetriever`. BM25 adds what
TF-IDF lacks: **term-frequency saturation** (a term repeated ten times is not ten
times as important) and **document-length normalisation** (a long document is not
automatically more relevant). Whether that helps *here* is an open question the
benchmarks answer — our documents are short and near-uniform, which is exactly the
regime where length normalisation has little to do.

Keyless and dependency-free (P8), idempotent by chunk id (RD-2), same contract as
the other retrievers.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any

from app.core.filters import metadata_matches
from app.core.types import Chunk

_TOKEN = re.compile(r"[a-z0-9]+")

# Okapi BM25 defaults: k1 controls saturation, b controls length normalisation.
DEFAULT_K1 = 1.5
DEFAULT_B = 0.75


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text.lower())


class Bm25Retriever:
    def __init__(self, *, k1: float = DEFAULT_K1, b: float = DEFAULT_B) -> None:
        self._k1 = k1
        self._b = b
        self._chunks: dict[str, Chunk] = {}
        self._term_counts: dict[str, Counter[str]] = {}
        self._lengths: dict[str, int] = {}
        self._doc_freq: Counter[str] = Counter()
        self._total_length = 0

    def add(self, chunks: list[Chunk]) -> None:
        for chunk in chunks:
            if chunk.id in self._chunks:
                continue  # idempotent (RD-2)
            tokens = _tokens(chunk.text)
            counts = Counter(tokens)
            self._chunks[chunk.id] = chunk
            self._term_counts[chunk.id] = counts
            self._lengths[chunk.id] = max(1, len(tokens))
            self._total_length += max(1, len(tokens))
            for term in counts:
                self._doc_freq[term] += 1

    def size(self) -> int:
        return len(self._chunks)

    def _idf(self, term: str) -> float:
        total = len(self._chunks)
        freq = self._doc_freq.get(term, 0)
        # The +0.5 smoothed form, floored at 0 so a term in every document adds nothing.
        return max(0.0, math.log(1.0 + (total - freq + 0.5) / (freq + 0.5)))

    def retrieve(self, query: str, k: int = 3, where: dict[str, Any] | None = None) -> list[Chunk]:
        terms = set(_tokens(query))
        if not terms or not self._chunks:
            return []

        average_length = self._total_length / len(self._chunks)
        scored: list[tuple[float, Chunk]] = []
        for chunk_id, counts in self._term_counts.items():
            chunk = self._chunks[chunk_id]
            if not metadata_matches(chunk.metadata, where):
                continue
            length = self._lengths[chunk_id]
            normaliser = self._k1 * (1.0 - self._b + self._b * length / average_length)
            score = 0.0
            for term in terms:
                tf = counts.get(term, 0)
                if tf == 0:
                    continue
                score += self._idf(term) * (tf * (self._k1 + 1.0)) / (tf + normaliser)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda pair: (-pair[0], pair[1].id))
        return [
            Chunk(
                id=chunk.id,
                text=chunk.text,
                source=chunk.source,
                score=round(score, 6),
                metadata=chunk.metadata,
            )
            for score, chunk in scored[: max(1, k)]
        ]
