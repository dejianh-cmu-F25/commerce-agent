"""Pass^k and fault attribution (feature 046, SC-009).

Pass^k measures **consistency**: the fraction of tasks solved on *all* k
independent attempts (from tau-bench). Fault attribution names who is responsible
and what went wrong, so a failure is actionable rather than just a number.
"""

from __future__ import annotations

from dataclasses import dataclass

FAULT_ENTITIES = ("user", "agent", "environment")
FAULT_TYPES = (
    "no_failure",
    "goal_partially_completed",
    "used_wrong_tool",
    "used_wrong_tool_argument",
    "took_unintended_action",
)


def pass_k(attempts: list[list[bool]]) -> float:
    """``attempts[i]`` is the outcome of each of k runs for task ``i``."""
    if not attempts:
        return 0.0
    return sum(1 for row in attempts if row and all(row)) / len(attempts)


@dataclass(frozen=True)
class Fault:
    entity: str
    type: str
    detail: str = ""


def attribute(
    *,
    passed: bool,
    tool_calls: tuple[str, ...] = (),
    expected_tools: tuple[str, ...] = (),
    error: bool = False,
) -> Fault:
    """Assign a fault to an entity and a type (tau-bench taxonomy)."""
    if passed:
        return Fault("agent", "no_failure")
    if error:
        return Fault("environment", "took_unintended_action", "the turn errored")
    missing = [name for name in expected_tools if name not in tool_calls]
    if missing:
        return Fault("agent", "used_wrong_tool", f"missing tools: {missing}")
    extra = [name for name in tool_calls if name not in expected_tools]
    if extra:
        return Fault("agent", "used_wrong_tool", f"unexpected tools: {extra}")
    return Fault("agent", "goal_partially_completed")
