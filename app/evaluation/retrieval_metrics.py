"""Pure retrieval metrics (feature 022).

Definitions (per query, then averaged):
- ``hit-rate@k``: 1 if at least one expected id is in the top ``k``, else 0.
- ``recall@k``: fraction of the expected ids found in the top ``k``.
- ``MRR``: reciprocal rank of the first expected id (0 if none).

Deterministic and model-free, so results are reproducible (TT-2).
"""

from __future__ import annotations

import math
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


def _dcg(gains: list[float], k: int) -> float:
    return sum(gain / math.log2(rank + 2) for rank, gain in enumerate(gains[:k]))


def ndcg_at_k(retrieved_gains: list[float], all_gains: list[float], k: int) -> float:
    """Graded nDCG@k (feature 046, discovery): gains in retrieval order vs the ideal."""
    ideal = _dcg(sorted(all_gains, reverse=True), k)
    return _dcg(retrieved_gains, k) / ideal if ideal > 0 else 0.0


@dataclass
class GradedMetrics:
    cases: int
    ndcg: float
    hit_rate: float
    mrr: float


def evaluate_graded(results: list[tuple[list[float], list[float]]], k: int = 10) -> GradedMetrics:
    """Average nDCG@k, hit@k and MRR over ``(retrieved_gains, all_gains)`` pairs."""
    if not results:
        return GradedMetrics(cases=0, ndcg=0.0, hit_rate=0.0, mrr=0.0)
    ndcgs = [ndcg_at_k(retrieved, all_gains, k) for retrieved, all_gains in results]
    hits = [1.0 if any(g > 0 for g in retrieved[:k]) else 0.0 for retrieved, _ in results]
    rrs = [
        1.0 / next((rank for rank, g in enumerate(retrieved, start=1) if g > 0), 0)
        if any(g > 0 for g in retrieved)
        else 0.0
        for retrieved, _ in results
    ]
    count = len(results)
    return GradedMetrics(
        cases=count,
        ndcg=round(sum(ndcgs) / count, 4),
        hit_rate=round(sum(hits) / count, 4),
        mrr=round(sum(rrs) / count, 4),
    )


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
