"""Unit tests for span aggregation (feature 017)."""

from __future__ import annotations

from app.core.metrics import summarize
from app.core.types import Span


def _span(name: str, start: float, end: float, status: str = "ok", **attributes) -> Span:
    return Span(
        trace_id="t",
        span_id=f"{name}-{start}",
        name=name,
        start_ms=start,
        end_ms=end,
        status=status,
        attributes=attributes,
    )


def test_summarize_latency_tokens_cost_and_tools():
    spans = [
        _span("turn", 0, 100),
        _span(
            "llm",
            0,
            80,
            prompt_tokens=100,
            completion_tokens=20,
            cache_hit_tokens=60,
            cache_miss_tokens=40,
            cost_cny=0.001,
        ),
        _span("tool", 0, 10),
        _span("tool", 0, 30, status="error"),
    ]
    summary = summarize(spans)

    assert summary.span_count == 4
    by_name = {stat.name: stat for stat in summary.spans}
    assert by_name["tool"].count == 2
    assert by_name["tool"].errors == 1
    assert by_name["turn"].avg_ms == 100.0
    assert summary.prompt_tokens == 100
    assert summary.completion_tokens == 20
    assert summary.cache_hit_tokens == 60
    assert summary.cache_miss_tokens == 40
    assert summary.cost_cny == 0.001
    assert summary.tool_ok == 1
    assert summary.tool_error == 1


def test_summarize_empty_is_zeroed():
    summary = summarize([])
    assert summary.span_count == 0
    assert summary.spans == []
    assert summary.tool_ok == 0


def test_p95_is_the_upper_tail():
    spans = [_span("llm", 0, duration) for duration in (10, 20, 30, 40, 50, 60, 70, 80, 90, 100)]
    summary = summarize(spans)
    assert summary.spans[0].p95_ms == 100.0
