"""Process metrics from a run's spans (feature 023, book ch.7).

White-box metrics: steps, tool calls and their success, ungrounded-id attempts,
latency, tokens, and cost. Read from the trace spans and the LLM span
attributes; no model needed.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.types import Span


@dataclass
class RunMetrics:
    steps: int
    tool_calls: int
    tool_ok: int
    tool_error: int
    ungrounded_attempts: int
    latency_ms: float
    prompt_tokens: int
    completion_tokens: int
    cache_hit_tokens: int
    cache_miss_tokens: int
    cost_cny: float


def _number(attributes: dict, key: str) -> float:
    value = attributes.get(key, 0)
    return float(value) if isinstance(value, (int, float)) else 0.0


def summarize(spans: list[Span]) -> RunMetrics:
    tool_spans = [span for span in spans if span.name == "tool"]
    turn_spans = [span for span in spans if span.name == "turn"]
    llm_spans = [span for span in spans if span.name == "llm"]

    ungrounded = 0
    for span in tool_spans:
        output = str(span.attributes.get("output", "")).lower()
        if "unknown product id" in output or "unknown order id" in output:
            ungrounded += 1

    return RunMetrics(
        steps=len(tool_spans),
        tool_calls=len(tool_spans),
        tool_ok=sum(1 for span in tool_spans if span.status == "ok"),
        tool_error=sum(1 for span in tool_spans if span.status != "ok"),
        ungrounded_attempts=ungrounded,
        latency_ms=round(sum(max(0.0, s.end_ms - s.start_ms) for s in turn_spans), 2),
        prompt_tokens=sum(int(_number(s.attributes, "prompt_tokens")) for s in llm_spans),
        completion_tokens=sum(int(_number(s.attributes, "completion_tokens")) for s in llm_spans),
        cache_hit_tokens=sum(int(_number(s.attributes, "cache_hit_tokens")) for s in llm_spans),
        cache_miss_tokens=sum(int(_number(s.attributes, "cache_miss_tokens")) for s in llm_spans),
        cost_cny=round(sum(_number(s.attributes, "cost_cny") for s in llm_spans), 6),
    )
