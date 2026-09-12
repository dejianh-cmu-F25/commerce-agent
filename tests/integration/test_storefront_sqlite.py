"""Integration tests for the SQLite storefront provider (feature 004).

Uses a real SQLite file (tier: integration) to prove persistence and idempotent
seeding (RD-2).
"""

from __future__ import annotations

from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.storefront_sqlite import SqliteStorefront


def test_seed_and_search(tmp_path: Path):
    store = SqliteStorefront(str(tmp_path / "store.sqlite"))
    assert store.count() == len(SEED_PRODUCTS)

    results = store.search("tent", 5)
    assert [p.id for p in results] == ["P-101"]
    assert results[0].in_stock is True


def test_get_roundtrips_fields(tmp_path: Path):
    store = SqliteStorefront(str(tmp_path / "store.sqlite"))
    product = store.get("P-103")
    assert product is not None
    assert product.title == "Camp Stove"
    assert product.stock == 0
    assert product.in_stock is False
    assert "cook" in product.tags


def test_seeding_is_idempotent(tmp_path: Path):
    path = str(tmp_path / "store.sqlite")
    first = SqliteStorefront(path)
    before = first.count()

    # Re-open the same file (as a restart would) and confirm no duplicates.
    second = SqliteStorefront(path)
    assert second.count() == before == len(SEED_PRODUCTS)


def test_missing_product_returns_none(tmp_path: Path):
    store = SqliteStorefront(str(tmp_path / "store.sqlite"))
    assert store.get("does-not-exist") is None
