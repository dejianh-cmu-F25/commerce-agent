"""Hybrid retriever: sparse + dense fused with Reciprocal Rank Fusion (feature 046).

The two benchmarks disagree on purpose: lexical queries favour the sparse
retriever, semantic queries favour the dense one. RRF combines their rankings
without a tuned score blend (``score = Σ 1 / (rrf_k + rank)``), so it is the
natural default for discovery.

Dependency-free and deterministic; it just composes two ``Retriever`` ports.
"""

from __future__ import annotations

from app.core.types import Chunk
from app.ports.retriever import Retriever


class HybridRetriever:
    def __init__(
        self,
        sparse: Retriever,
        dense: Retriever,
        *,
        rrf_k: int = 60,
        candidate_k: int = 20,
    ) -> None:
        self._sparse = sparse
        self._dense = dense
        self._rrf_k = rrf_k
        self._candidate_k = candidate_k

    def add(self, chunks: list[Chunk]) -> None:
        self._sparse.add(chunks)
        self._dense.add(chunks)

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        if not query.strip():
            return []
        sparse = self._sparse.retrieve(query, self._candidate_k)
        dense = self._dense.retrieve(query, self._candidate_k)
        scores: dict[str, float] = {}
        by_id: dict[str, Chunk] = {}
        for ranking in (sparse, dense):
            for rank, chunk in enumerate(ranking, start=1):
                scores[chunk.id] = scores.get(chunk.id, 0.0) + 1.0 / (self._rrf_k + rank)
                by_id[chunk.id] = chunk
        ordered = sorted(scores, key=lambda cid: (-scores[cid], cid))[: max(1, k)]
        return [
            Chunk(id=cid, text=by_id[cid].text, source=by_id[cid].source, score=scores[cid])
            for cid in ordered
        ]
