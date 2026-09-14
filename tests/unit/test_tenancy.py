"""Tenancy gate and simulated auth (feature 046, INV-7)."""

from __future__ import annotations

from app.adapters.auth_memory import InMemoryAuth
from app.core.session import Session
from app.core.types import Order, OrderItem
from app.gates.base import GateContext
from app.gates.tenancy import TenancyGate
from app.ports.auth import Principal


def _order(customer_id: str) -> Order:
    return Order(
        id="o1",
        customer_id=customer_id,
        status="delivered",
        placed_at="2026-09-01T00:00:00Z",
        total=10.0,
        items=[OrderItem(product_id="p1", title="t", quantity=1, unit_price=10.0)],
    )


def test_gate_allows_own_order() -> None:
    context = GateContext(session=Session(id="s", customer_id="c1"), order=_order("c1"))
    assert TenancyGate().check(context).allowed


def test_gate_blocks_another_customers_order() -> None:
    context = GateContext(session=Session(id="s", customer_id="c1"), order=_order("c2"))
    result = TenancyGate().check(context)
    assert not result.allowed
    assert "another customer" in result.reason


def test_gate_blocks_without_a_customer() -> None:
    context = GateContext(session=Session(id="s"), order=_order("c1"))
    assert not TenancyGate().check(context).allowed


def test_gate_allows_when_no_order() -> None:
    assert TenancyGate().check(GateContext(session=Session(id="s"))).allowed


def test_auth_resolves_a_principal() -> None:
    auth = InMemoryAuth()
    auth.issue("tok", Principal(customer_id="c1", name="Ada"))
    assert auth.authenticate("tok") == Principal(customer_id="c1", name="Ada")
    assert auth.authenticate("bad") is None
