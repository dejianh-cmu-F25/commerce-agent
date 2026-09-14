"""Deterministic return-eligibility decision (feature 045).

The model proposes; this decides. Given the request facts and the policy clauses,
it returns a decision (``eligible`` / ``ineligible`` / ``escalate``), the reasons,
and the clause ids cited. It **escalates rather than guessing** when a required
fact is missing (RW-1: never act on ambiguity).

This is the harness's "dispose" half: the LLM's proposal is checked against hard
facts here, so a wrong or unsupported proposal cannot become a refund.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.returns.clauses import Policy

ELIGIBLE = "eligible"
INELIGIBLE = "ineligible"
ESCALATE = "escalate"


@dataclass(frozen=True)
class ReturnRequestFacts:
    """The hard facts of one return request (from the order record + the item)."""

    order_id: str
    fulfillment_line_item_id: str
    reason: str  # unwanted | size_too_small | damaged | defective | wrong_item | missing
    delivered_at: str | None
    item_tags: tuple[str, ...] = ()
    on_order: bool = True


@dataclass(frozen=True)
class ReturnDecision:
    decision: str
    reasons: list[str] = field(default_factory=list)
    cited_clauses: list[str] = field(default_factory=list)
    restocking_fee_pct: float | None = None


def _parse(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)


def decide_return(
    facts: ReturnRequestFacts, policy: Policy, now: datetime | None = None
) -> ReturnDecision:
    """Return the deterministic decision for one request."""
    now = now or datetime.now(UTC)

    if not facts.on_order:
        return ReturnDecision(
            ESCALATE,
            [f"item {facts.fulfillment_line_item_id} is not on order {facts.order_id}"],
        )

    non_returnable = next((c for c in policy.clauses if c.non_returnable_tags), None)
    if non_returnable and any(tag in non_returnable.non_returnable_tags for tag in facts.item_tags):
        return ReturnDecision(
            INELIGIBLE,
            ["item is final-sale or otherwise non-returnable"],
            [non_returnable.id],
        )

    exception = next((c for c in policy.clauses if c.exception_reasons), None)
    if exception is not None and facts.reason in exception.exception_reasons:
        return ReturnDecision(
            ELIGIBLE,
            [f"reason '{facts.reason}' is a policy exception (no window, no fee)"],
            [exception.id],
        )

    window = next((c for c in policy.clauses if c.window_days is not None), None)
    if window is None or window.window_days is None:
        return ReturnDecision(ESCALATE, ["no return window in the active policy"])

    delivered = _parse(facts.delivered_at)
    if delivered is None:
        return ReturnDecision(
            ESCALATE,
            ["order has no delivery date; cannot compute the return window"],
            [window.id],
        )

    age_days = max(0, (now - delivered).days)
    if age_days > window.window_days:
        return ReturnDecision(
            INELIGIBLE,
            [f"delivered {age_days} days ago; the window is {window.window_days} days"],
            [window.id],
        )

    fee_clause = next(
        (
            c
            for c in policy.clauses
            if c.restocking_fee_pct is not None
            and any(tag in c.applies_to_tags for tag in facts.item_tags)
        ),
        None,
    )
    if fee_clause is not None:
        return ReturnDecision(
            ELIGIBLE,
            [
                f"within the {window.window_days}-day window",
                f"a {fee_clause.restocking_fee_pct:g}% restocking fee applies",
            ],
            [window.id, fee_clause.id],
            fee_clause.restocking_fee_pct,
        )
    return ReturnDecision(ELIGIBLE, [f"within the {window.window_days}-day window"], [window.id])
