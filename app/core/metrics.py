"""Pure span aggregation for the Metrics view (feature 017, OB-3).

No I/O: ``summarize`` is a pure function over spans, so it is unit-testable and
the web layer stays a thin wrapper.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from app.core.types import Span


@dataclass
class SpanStats:
    name: str
    count: int
    errors: int
    avg_ms: float
    p95_ms: float


@dataclass
class MetricsSummary:
    span_count: int
    spans: list[SpanStats] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cache_hit_tokens: int = 0
    cache_miss_tokens: int = 0
    cost_cny: float = 0.0
    tool_ok: int = 0
    tool_error: int = 0


def _p95(values: list[float]) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(0.95 * len(ordered)) - 1))
    return round(ordered[index], 2)


def _number(attributes: dict, key: str) -> float:
    value = attributes.get(key, 0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def summarize(spans: list[Span]) -> MetricsSummary:
    """Aggregate spans into per-span latency stats, tokens, cost, and tools."""
    summary = MetricsSummary(span_count=len(spans))
    by_name: dict[str, list[Span]] = {}
    for span in spans:
        by_name.setdefault(span.name, []).append(span)
        if span.name == "llm":
            summary.prompt_tokens += int(_number(span.attributes, "prompt_tokens"))
            summary.completion_tokens += int(_number(span.attributes, "completion_tokens"))
            summary.cache_hit_tokens += int(_number(span.attributes, "cache_hit_tokens"))
            summary.cache_miss_tokens += int(_number(span.attributes, "cache_miss_tokens"))
            summary.cost_cny += _number(span.attributes, "cost_cny")
        elif span.name == "tool":
            if span.status == "ok":
                summary.tool_ok += 1
            else:
                summary.tool_error += 1

    for name, group in sorted(by_name.items()):
        durations = [max(0.0, span.end_ms - span.start_ms) for span in group]
        summary.spans.append(
            SpanStats(
                name=name,
                count=len(group),
                errors=sum(1 for span in group if span.status == "error"),
                avg_ms=round(sum(durations) / len(durations), 2),
                p95_ms=_p95(durations),
            )
        )
    summary.cost_cny = round(summary.cost_cny, 6)
    return summary
