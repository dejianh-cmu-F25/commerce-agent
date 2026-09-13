"""Paired significance for the evaluation report (feature 026, EV-2).

Deterministic, stdlib-only: an exact two-sided McNemar test on paired booleans
and a percentile bootstrap confidence interval of a mean. A raw delta on a small
set is not proof; EV-2 requires effect size, confidence, and sample size.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class PairedDelta:
    delta: float
    ci_low: float
    ci_high: float
    p_value: float
    n: int


def mcnemar_p(baseline: list[bool], candidate: list[bool]) -> float:
    """Two-sided exact McNemar p-value on paired booleans."""
    if len(baseline) != len(candidate):
        raise ValueError("baseline and candidate must have the same length")
    b = sum(1 for x, y in zip(baseline, candidate, strict=False) if x and not y)
    c = sum(1 for x, y in zip(baseline, candidate, strict=False) if not x and y)
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return round(min(1.0, 2 * tail), 4)


def bootstrap_ci(
    values: list[float], confidence: float = 0.95, resamples: int = 2000, seed: int = 0
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval of the mean (deterministic)."""
    if not values:
        return (0.0, 0.0)
    rng = random.Random(seed)
    n = len(values)
    means = sorted(sum(values[rng.randrange(n)] for _ in range(n)) / n for _ in range(resamples))
    low_index = int((1 - confidence) / 2 * resamples)
    high_index = min(resamples - 1, int((1 + confidence) / 2 * resamples))
    return (round(means[low_index], 4), round(means[high_index], 4))


def paired_delta(baseline: list[bool], candidate: list[bool]) -> PairedDelta:
    """Mean paired delta with a 95% CI and a McNemar p-value."""
    if len(baseline) != len(candidate):
        raise ValueError("baseline and candidate must have the same length")
    deltas = [float(int(c) - int(b)) for b, c in zip(baseline, candidate, strict=False)]
    if not deltas:
        return PairedDelta(0.0, 0.0, 0.0, 1.0, 0)
    mean = round(sum(deltas) / len(deltas), 4)
    ci_low, ci_high = bootstrap_ci(deltas)
    return PairedDelta(
        delta=mean,
        ci_low=ci_low,
        ci_high=ci_high,
        p_value=mcnemar_p(baseline, candidate),
        n=len(deltas),
    )
