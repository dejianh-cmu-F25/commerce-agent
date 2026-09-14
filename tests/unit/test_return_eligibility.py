"""Deterministic return-eligibility decision (feature 045)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.returns.clauses import load_policy
from app.returns.eligibility import (
    ELIGIBLE,
    ESCALATE,
    INELIGIBLE,
    ReturnRequestFacts,
    decide_return,
)

NOW = datetime(2026, 3, 1, tzinfo=UTC)
POLICY = load_policy("config/policies/policies.yaml")


def _facts(
    *,
    reason: str = "unwanted",
    delivered_at: str | None = "2026-02-20T00:00:00Z",
    item_tags: tuple[str, ...] = (),
    on_order: bool = True,
) -> ReturnRequestFacts:
    return ReturnRequestFacts(
        order_id="gid://shopify/Order/1",
        fulfillment_line_item_id="gid://shopify/FulfillmentLineItem/21",
        reason=reason,
        delivered_at=delivered_at,
        item_tags=item_tags,
        on_order=on_order,
    )


def test_policy_loads_active_v2() -> None:
    assert POLICY.active_version == "v2"
    window = POLICY.by_id("returns#window")
    assert window is not None and window.window_days == 30


def test_within_window_is_eligible_without_fee() -> None:
    decision = decide_return(_facts(), POLICY, now=NOW)
    assert decision.decision == ELIGIBLE
    assert decision.cited_clauses == ["returns#window"]
    assert decision.restocking_fee_pct is None


def test_large_item_gets_restocking_fee() -> None:
    decision = decide_return(_facts(item_tags=("large",)), POLICY, now=NOW)
    assert decision.decision == ELIGIBLE
    assert decision.restocking_fee_pct == 15
    assert "returns#restocking-fee" in decision.cited_clauses


def test_outside_window_is_ineligible() -> None:
    decision = decide_return(_facts(delivered_at="2026-01-01T00:00:00Z"), POLICY, now=NOW)
    assert decision.decision == INELIGIBLE
    assert decision.cited_clauses == ["returns#window"]


def test_final_sale_is_ineligible() -> None:
    decision = decide_return(_facts(item_tags=("final_sale",)), POLICY, now=NOW)
    assert decision.decision == INELIGIBLE
    assert decision.cited_clauses == ["returns#non-returnable"]


def test_damaged_is_an_exception_even_outside_the_window() -> None:
    decision = decide_return(
        _facts(reason="damaged", delivered_at="2025-06-01T00:00:00Z"), POLICY, now=NOW
    )
    assert decision.decision == ELIGIBLE
    assert decision.cited_clauses == ["returns#exception"]
    assert decision.restocking_fee_pct is None


def test_missing_delivery_date_escalates() -> None:
    decision = decide_return(_facts(delivered_at=None), POLICY, now=NOW)
    assert decision.decision == ESCALATE
    assert decision.cited_clauses == ["returns#window"]


def test_item_not_on_order_escalates() -> None:
    decision = decide_return(_facts(on_order=False), POLICY, now=NOW)
    assert decision.decision == ESCALATE
