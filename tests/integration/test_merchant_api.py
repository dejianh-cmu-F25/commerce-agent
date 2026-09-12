"""Integration tests for the merchant HTTP surface (feature 010)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.adapters.merchant_sqlite import SqliteMerchant
from app.adapters.storefront_sqlite import SqliteStorefront
from app.core.settings import (
    BudgetSettings,
    LLMSettings,
    SessionSettings,
    Settings,
    StorefrontSettings,
)
from web.main import create_app


def _settings(tmp_path: Path, path: str) -> Settings:
    return Settings(
        llm=LLMSettings(provider="mock"),
        storefront=StorefrontSettings(provider="sqlite", sqlite_path=path),
        session=SessionSettings(store="memory"),
        budget=BudgetSettings(enabled=False, state_file=str(tmp_path / "budget.json")),
    )


def test_merchant_inventory_changes_and_apply(tmp_path: Path):
    path = str(tmp_path / "store.sqlite")
    SqliteStorefront(path)  # seed
    merchant = SqliteMerchant(path)
    change = merchant.stage_change("P-101", "price", 199.0)

    client = TestClient(create_app(_settings(tmp_path, path)))

    inventory = client.get("/merchant/inventory").json()["items"]
    assert next(item for item in inventory if item["id"] == "P-101")["price"] == 189.0

    changes = client.get("/merchant/changes").json()["changes"]
    assert any(c["id"] == change.id for c in changes)

    applied = client.post(f"/merchant/changes/{change.id}/apply").json()["change"]
    assert applied["status"] == "applied"

    inventory_after = client.get("/merchant/inventory").json()["items"]
    assert next(item for item in inventory_after if item["id"] == "P-101")["price"] == 199.0
    assert client.get("/merchant/changes").json()["changes"] == []

    assert client.post("/merchant/changes/unknown/apply").status_code == 404
