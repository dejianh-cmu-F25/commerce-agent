"""Amazon policy SoT: loader, engine, versioning, gate, renderer (feature 046)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.core.session import Session
from app.gates.base import GateContext
from app.gates.policy import PolicyGate
from app.returns.amazon_policy import (
    ELIGIBLE,
    ESCALATE,
    INELIGIBLE,
    ReturnFacts,
    decide_return,
    load_amazon_policy,
    select_version,
)
from app.returns.render import render_policy

NOW = datetime(2026, 9, 15, tzinfo=UTC)
POLICY = load_amazon_policy()


def _facts(
    days_ago: int | None = 5,
    reason: str = "unwanted",
    category: str = "all",
    tags: tuple[str, ...] = (),
    on_order: bool = True,
) -> ReturnFacts:
    delivered = (NOW - timedelta(days=days_ago)).isoformat() if days_ago is not None else None
    return ReturnFacts(
        order_id="o1",
        fulfillment_line_item_id="f1",
        reason=reason,
        delivered_at=delivered,
        category=category,
        tags=tags,
        on_order=on_order,
    )


def test_default_window_30_days() -> None:
    assert decide_return(_facts(days_ago=9), POLICY, now=NOW).decision == ELIGIBLE
    assert decide_return(_facts(days_ago=30), POLICY, now=NOW).decision == ELIGIBLE
    assert decide_return(_facts(days_ago=31), POLICY, now=NOW).decision == INELIGIBLE


def test_category_windows() -> None:
    short = decide_return(_facts(days_ago=20, category="digital_book"), POLICY, now=NOW)
    assert short.decision == INELIGIBLE
    long = decide_return(_facts(days_ago=45, category="renewed_premium"), POLICY, now=NOW)
    assert long.decision == ELIGIBLE
    apple = decide_return(_facts(days_ago=20, category="apple_brand"), POLICY, now=NOW)
    assert apple.decision == INELIGIBLE  # 15-day window


def test_non_returnable_and_final_sale() -> None:
    assert decide_return(_facts(category="perishable"), POLICY, now=NOW).decision == INELIGIBLE
    assert decide_return(_facts(tags=("final_sale",)), POLICY, now=NOW).decision == INELIGIBLE
    # a damaged non-returnable item is handled by Customer Service
    damaged = decide_return(_facts(reason="damaged", category="perishable"), POLICY, now=NOW)
    assert damaged.decision == ESCALATE


def test_exception_waives_window_and_fee() -> None:
    decision = decide_return(_facts(days_ago=90, reason="damaged"), POLICY, now=NOW)
    assert decision.decision == ELIGIBLE
    assert decision.fee_pct is None


def test_restocking_fee() -> None:
    decision = decide_return(_facts(category="opened_software"), POLICY, now=NOW)
    assert decision.decision == ELIGIBLE
    assert decision.fee_pct == 100
    assert "returns#fee-restocking" in decision.cited_clauses


def test_escalates_on_missing_facts() -> None:
    assert decide_return(_facts(on_order=False), POLICY, now=NOW).decision == ESCALATE
    assert decide_return(_facts(days_ago=None), POLICY, now=NOW).decision == ESCALATE


def test_version_selection_is_real() -> None:
    assert select_version(POLICY, at=NOW) == "2026-09"
    assert select_version(POLICY, at=datetime(2021, 1, 1, tzinfo=UTC)) == "2020-06"
    # the 2020 version has no category-window clause; a 45-day renewed item would
    # be ineligible under 2020 but eligible under 2026.
    old = decide_return(
        _facts(days_ago=45, category="renewed_premium"), POLICY, now=NOW, version="2020-06"
    )
    assert old.decision == INELIGIBLE
    # the 2026 restocking clause is not applied under the 2020 version
    old_fee = decide_return(_facts(category="opened_software"), POLICY, now=NOW, version="2020-06")
    assert old_fee.fee_pct is None


def test_gate_blocks_and_allows() -> None:
    gate = PolicyGate(POLICY)
    session = Session(id="t")
    assert gate.check(GateContext(session=session, now=NOW, facts=_facts(days_ago=9))).allowed
    block = gate.check(GateContext(session=session, now=NOW, facts=_facts(days_ago=99)))
    assert not block.allowed
    assert "ineligible" in block.reason
    assert not gate.check(GateContext(session=session, now=NOW)).allowed


def test_render_is_derived_from_sot() -> None:
    prose = render_policy(POLICY, "2026-09")
    assert "returns#window-default" in prose
    assert "30 days of delivery" in prose
    assert "amazon-returns-2026" in prose  # the source id
    old = render_policy(POLICY, "2020-06")
    assert "temporary extension" in old or "temporary-covid" in old


def test_rendered_prose_matches_sot() -> None:
    """The committed prose is a build artifact; it must equal the rendered SoT."""
    from pathlib import Path

    path = Path("config/knowledge/amazon-returns.md")
    assert path.exists(), f"missing rendered prose: {path} (run python -m app.returns.render)"
    assert path.read_text() == render_policy(POLICY, POLICY.active_version)
