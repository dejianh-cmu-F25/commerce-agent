"""Failure attribution: locate the first error in a trajectory (feature 023).

The book's rule: attribute the **first** error that caused the deviation, not
the last symptom. Deterministic and rule-based.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.session import Session, ToolResultEvent

CATEGORIES = (
    "unknown_tool",
    "ungrounded_id",
    "out_of_policy",
    "tool_error",
    "budget",
    "max_turns",
)


@dataclass
class FailureAttribution:
    category: str
    step: int
    evidence: str


def _classify(content: str) -> str:
    lowered = content.lower()
    if "unknown tool" in lowered:
        return "unknown_tool"
    if "unknown product id" in lowered or "unknown order id" in lowered:
        return "ungrounded_id"
    if '"eligible": false' in lowered or "not delivered" in lowered:
        return "out_of_policy"
    return "tool_error"


def attribute(session: Session, turn_reason: str = "stop") -> FailureAttribution | None:
    """Return the first error's attribution, or ``None`` if the run is clean."""
    step = 0
    for event in session.events:
        if not isinstance(event, ToolResultEvent):
            continue
        step += 1
        if event.status != "ok":
            return FailureAttribution(
                category=_classify(event.content),
                step=step,
                evidence=event.content[:160],
            )
    if turn_reason == "budget":
        return FailureAttribution("budget", step + 1, "budget exceeded")
    if turn_reason == "max_turns":
        return FailureAttribution("max_turns", step + 1, "max turns reached")
    return None
