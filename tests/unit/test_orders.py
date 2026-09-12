"""Unit tests for storefront orders and the return policy (feature 014)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.order_seed import demo_orders
from app.adapters.storefront_memory import InMemoryStorefront
from app.adapters.storefront_sqlite import SqliteStorefront
from app.returns.policy import return_eligibility

NOW = datetime(2026, 9, 13, tzinfo=UTC)


def test_order_parity_between_providers(tmp_path: Path):
    memory = InMemoryStorefront(SEED_PRODUCTS)
    sqlite = SqliteStorefront(str(tmp_path / "store.sqlite"))

    for store in (memory, sqlite):
        orders = store.list_orders("c1")
        assert [order.id for order in orders] == ["O-1003", "O-1001", "O-1002"]  # newest first
        assert store.list_orders("c1") == orders  # idempotent seeding
        assert store.list_orders("") == []

        detail = store.get_order("c1", "O-1001")
        assert detail is not None
        assert detail.items[0].product_id == "P-101"
        assert store.get_order("c1", "O-9999") is None
        assert store.get_order("", "O-1001") is None


def test_seed_orders_can_be_disabled(tmp_path: Path):
    memory = InMemoryStorefront(SEED_PRODUCTS, seed_orders=False)
    sqlite = SqliteStorefront(str(tmp_path / "store.sqlite"), seed_orders=False)
    assert memory.list_orders("c1") == []
    assert sqlite.list_orders("c1") == []


def test_return_eligibility():
    orders = {order.id: order for order in demo_orders("c1", now=NOW)}

    ok, reason = return_eligibility(orders["O-1001"], "P-101", 30, now=NOW)
    assert ok and "30-day" in reason

    ok, reason = return_eligibility(orders["O-1002"], "P-104", 30, now=NOW)
    assert not ok and "return window" in reason

    ok, reason = return_eligibility(orders["O-1003"], "P-105", 30, now=NOW)
    assert not ok and "not delivered" in reason

    ok, _ = return_eligibility(orders["O-1001"], "P-999", 30, now=NOW)
    assert not ok
