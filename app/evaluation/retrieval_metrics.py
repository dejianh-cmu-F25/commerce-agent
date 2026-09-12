"""Pure retrieval metrics (feature 022).

Definitions (per query, then averaged):
- ``hit-rate@k``: 1 if at least one expected id is in the top ``k``, else 0.
- ``recall@k``: fraction of the expected ids found in the top ``k``.
- ``MRR``: reciprocal rank of the first expected id (0 if none).

Deterministic and model-free, so results are reproducible (TT-2).
"""

from __future__ import annotations

from dataclasses import dataclass


def hit_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    return 1.0 if any(identifier in relevant for identifier in retrieved[:k]) else 0.0


def recall_at_k(retrieved: list[str], relevant: set[str], k: int) -> float:
    if not relevant:
        return 0.0
    found = len(set(retrieved[:k]) & relevant)  # dedupe: ids may repeat
    return found / len(relevant)


def reciprocal_rank(retrieved: list[str], relevant: set[str]) -> float:
    for rank, identifier in enumerate(retrieved, start=1):
        if identifier in relevant:
            return 1.0 / rank
    return 0.0


@dataclass
class RetrievalMetrics:
    cases: int
    hit_rate: float
    recall: float
    mrr: float


def evaluate_retrieval(results: list[tuple[list[str], set[str]]], k: int = 3) -> RetrievalMetrics:
    """Average the metrics over ``(retrieved_ids, relevant_ids)`` pairs."""
    if not results:
        return RetrievalMetrics(cases=0, hit_rate=0.0, recall=0.0, mrr=0.0)
    count = len(results)
    hits = sum(hit_at_k(retrieved, relevant, k) for retrieved, relevant in results)
    recalls = sum(recall_at_k(retrieved, relevant, k) for retrieved, relevant in results)
    rrs = sum(reciprocal_rank(retrieved, relevant) for retrieved, relevant in results)
    return RetrievalMetrics(
        cases=count,
        hit_rate=round(hits / count, 4),
        recall=round(recalls / count, 4),
        mrr=round(rrs / count, 4),
    )
