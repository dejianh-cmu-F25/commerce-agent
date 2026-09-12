"""Unit tests for the merchant backend and tools (feature 010)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.adapters.merchant_sqlite import SqliteMerchant
from app.adapters.storefront_sqlite import SqliteStorefront
from app.tools.merchant import register_merchant_tools
from app.tools.registry import ToolRegistry


def make(tmp_path: Path) -> SqliteMerchant:
    path = str(tmp_path / "store.sqlite")
    SqliteStorefront(path)  # seeds the catalog
    return SqliteMerchant(path)


def test_stage_does_not_apply(tmp_path: Path):
    merchant = make(tmp_path)
    change = merchant.stage_change("P-101", "price", 199.0)

    assert change.status == "pending"
    products = {p.id: p for p in merchant.list_products()}
    assert products["P-101"].price == 189.0  # unchanged until approval (P3)
    assert [c.id for c in merchant.pending()] == [change.id]


def test_apply_updates_once(tmp_path: Path):
    merchant = make(tmp_path)
    change = merchant.stage_change("P-101", "price", 199.0)

    applied = merchant.apply(change.id)
    assert applied is not None and applied.status == "applied"
    products = {p.id: p for p in merchant.list_products()}
    assert products["P-101"].price == 199.0
    assert merchant.pending() == []

    assert merchant.apply(change.id) is None  # no double-apply (RD-2)


def test_validation_rejects_bad_input(tmp_path: Path):
    merchant = make(tmp_path)
    with pytest.raises(ValueError):
        merchant.stage_change("P-999", "price", 10.0)  # unknown product
    with pytest.raises(ValueError):
        merchant.stage_change("P-101", "price", 0)  # price <= 0
    with pytest.raises(ValueError):
        merchant.stage_change("P-101", "stock", -1)  # stock < 0
    with pytest.raises(ValueError):
        merchant.stage_change("P-101", "bogus", 1)  # unknown kind


def test_agent_has_no_approval_tool(tmp_path: Path):
    registry = ToolRegistry()
    register_merchant_tools(registry, make(tmp_path))
    names = {spec.name for spec in registry.specs()}

    assert "apply_change" not in names  # approval is human-only (P3)
    assert {"list_inventory", "propose_price_change", "propose_stock_change"} <= names
