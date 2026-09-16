"""Unit tests for the gate pipeline (feature 020)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.core.session import Session
from app.core.types import Order, OrderItem
from app.gates.base import ALL, GateContext, GateResult
from app.gates.pipeline import GatePipeline
from app.gates.provenance import ProvenanceGate
from app.gates.returns import ReturnEligibilityGate

NOW = datetime(2026, 9, 13, tzinfo=UTC)


def _order(delivered_at: str | None, status: str = "delivered") -> Order:
    return Order(
        id="O-1",
        customer_id="c",
        status=status,
        placed_at="2026-09-01T00:00:00+00:00",
        delivered_at=delivered_at,
        total=1.0,
        items=[OrderItem("P-101", "Tent", 1, 1.0)],
    )


def test_provenance_gate_allows_known_ids_and_blocks_unknown():
    session = Session(id="s")
    session.remember_ids(["P-101"])

    assert ProvenanceGate().check(GateContext(session=session, ids=["P-101"])).allowed
    assert ProvenanceGate().check(GateContext(session=session, ids=[])).allowed

    blocked = ProvenanceGate().check(GateContext(session=session, ids=["P-999"]))
    assert not blocked.allowed
    assert "P-999" in blocked.reason


def test_return_gate_uses_the_configured_window():
    session = Session(id="s")

    eligible = ReturnEligibilityGate().check(
        GateContext(
            session=session,
            order=_order("2026-09-01T00:00:00+00:00"),
            product_id="P-101",
            window_days=30,
            now=NOW,
        )
    )
    assert eligible.allowed

    expired = ReturnEligibilityGate().check(
        GateContext(
            session=session,
            order=_order("2026-01-01T00:00:00+00:00"),
            product_id="P-101",
            window_days=30,
            now=NOW,
        )
    )
    assert not expired.allowed
    assert "window" in expired.reason

    assert not ReturnEligibilityGate().check(GateContext(session=session)).allowed


def test_pipeline_short_circuits_on_the_first_block():
    calls: list[str] = []

    class Recording:
        applies_to = ALL
        priority = 0

        def __init__(self, name: str, allowed: bool) -> None:
            self.name = name
            self._allowed = allowed

        def check(self, context: GateContext) -> GateResult:
            calls.append(self.name)
            return GateResult.allow() if self._allowed else GateResult.block("no")

    pipeline = GatePipeline([Recording("a", False), Recording("b", True)])
    result = pipeline.run(GateContext(session=Session(id="s")))

    assert not result.allowed
    assert calls == ["a"]
