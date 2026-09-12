"""Reliability metrics (feature 023, book ch.7).

- **Pass@1**: mean single-run success rate.
- **Pass@k**: fraction of tasks with at least one success in ``k`` runs
  (capability ceiling).
- **Best@k**: identical to Pass@k for binary outcomes (kept for the vocabulary).
- **Pass^k**: fraction of tasks where all ``k`` runs succeed (business
  reliability).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Reliability:
    runs: int
    successes: int
    tasks: int
    pass_at_1: float
    pass_at_k: float
    best_at_k: float
    pass_pow_k: float


def aggregate(tasks: list[list[bool]], k: int) -> Reliability:
    """Aggregate per-task run outcomes into the reliability metrics."""
    runs = sum(len(task) for task in tasks)
    successes = sum(sum(1 for outcome in task if outcome) for task in tasks)
    if not tasks or runs == 0:
        return Reliability(0, 0, 0, 0.0, 0.0, 0.0, 0.0)

    pass_at_k = sum(1 for task in tasks if any(task[:k])) / len(tasks)
    pass_pow_k = sum(1 for task in tasks if len(task[:k]) == k and all(task[:k])) / len(tasks)
    return Reliability(
        runs=runs,
        successes=successes,
        tasks=len(tasks),
        pass_at_1=round(successes / runs, 4),
        pass_at_k=round(pass_at_k, 4),
        best_at_k=round(pass_at_k, 4),
        pass_pow_k=round(pass_pow_k, 4),
    )
