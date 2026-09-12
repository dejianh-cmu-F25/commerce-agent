"""Unit tests for process metrics (feature 023)."""

from __future__ import annotations

from app.core.types import Span
from app.evaluation.agent_metrics import summarize


def _span(name: str, status: str = "ok", start: float = 0.0, end: float = 10.0, **attrs) -> Span:
    return Span(
        trace_id="t",
        span_id=f"{name}-{start}",
        name=name,
        start_ms=start,
        end_ms=end,
        status=status,
        attributes=attrs,
    )


def test_summarize_process_metrics():
    spans = [
        _span("turn", start=0, end=100),
        _span(
            "llm",
            start=0,
            end=80,
            prompt_tokens=100,
            completion_tokens=20,
            cache_hit_tokens=60,
            cache_miss_tokens=40,
            cost_cny=0.001,
        ),
        _span("tool", start=0, end=5),
        _span("tool", start=0, end=5, status="error", output='{"error": "unknown product id"}'),
    ]
    metrics = summarize(spans)

    assert metrics.steps == 2
    assert metrics.tool_ok == 1
    assert metrics.tool_error == 1
    assert metrics.ungrounded_attempts == 1
    assert metrics.latency_ms == 100.0
    assert metrics.prompt_tokens == 100
    assert metrics.completion_tokens == 20
    assert metrics.cache_hit_tokens == 60
    assert metrics.cost_cny == 0.001


def test_summarize_empty():
    metrics = summarize([])
    assert metrics.steps == 0
    assert metrics.cost_cny == 0.0
