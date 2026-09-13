"""Segment run results so a failure can be localized (feature 030, SC-2).

Aggregate pass rates hide which slice is failing. These pure functions group
result-like objects by intent and by tool, so a team can localize a problem
under load. Stdlib only.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol


class SegmentedResult(Protocol):
    """The minimal shape the segmenters need."""

    ok: bool
    intent: str
    tool_results: list[tuple[str, str]]


def by_intent(results: Sequence[SegmentedResult]) -> dict[str, dict[str, float]]:
    """Pass rate per intent (the customer job the scenario exercises)."""
    buckets: dict[str, list[bool]] = {}
    for result in results:
        buckets.setdefault(result.intent, []).append(result.ok)
    return {
        intent: {
            "passed": float(sum(outcomes)),
            "total": float(len(outcomes)),
            "pass_rate": round(sum(outcomes) / len(outcomes), 4),
        }
        for intent, outcomes in sorted(buckets.items())
    }


def by_tool(results: Sequence[SegmentedResult]) -> dict[str, dict[str, float]]:
    """Calls and error rate per tool name."""
    buckets: dict[str, list[str]] = {}
    for result in results:
        for name, status in result.tool_results:
            buckets.setdefault(name, []).append(status)
    segments: dict[str, dict[str, float]] = {}
    for name, statuses in sorted(buckets.items()):
        errors = sum(1 for status in statuses if status != "ok")
        segments[name] = {
            "calls": float(len(statuses)),
            "errors": float(errors),
            "error_rate": round(errors / len(statuses), 4),
        }
    return segments
