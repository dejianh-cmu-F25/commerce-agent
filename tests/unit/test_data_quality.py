"""Data-quality normalizers and the labeled benchmark (feature 027, RW-2)."""

from __future__ import annotations

import sqlite3

from app.adapters.storefront_sqlite import SqliteStorefront
from app.data.quality import (
    clean_text,
    normalize_order,
    normalize_product,
    parse_price,
    parse_stock,
)
from evals.data_quality import run_data_quality
from scripts.repair_storefront import repair


def test_clean_text_strips_control_and_padding() -> None:
    assert clean_text("  Wireless\tHeadphones  ") == "Wireless Headphones"
    assert clean_text("a\x00b") == "a b"
    assert clean_text(None) == ""


def test_parse_price() -> None:
    assert parse_price("$1,299.00") == 1299.00
    assert parse_price("  USD 45.5 ") == 45.50
    assert parse_price(19.999) == 20.00
    assert parse_price("free") is None
    assert parse_price(-5) is None


def test_parse_stock() -> None:
    assert parse_stock("12") == 12
    assert parse_stock("out of stock") == 0
    assert parse_stock("n/a") is None
    assert parse_stock(-3) is None


def test_normalize_product_rejects_unsalvageable() -> None:
    assert normalize_product({"id": "", "title": "x", "price": 1.0, "stock": 1}) is None
    assert normalize_product({"id": "P", "title": "y", "price": "free", "stock": 1}) is None
    product = normalize_product(
        {"id": "P1", "title": "  Tent ", "price": "$120.00", "stock": "out of stock"}
    )
    assert product is not None
    assert (product.id, product.title, product.price, product.stock) == ("P1", "Tent", 120.0, 0)


def test_normalize_order_drops_bad_items() -> None:
    order = normalize_order(
        "c1",
        {"id": "O1", "status": "SHIPPED", "placed_at": "2026-01-01", "total": "$10.00"},
        [
            {"product_id": "P1", "title": "  Widget ", "quantity": "2", "unit_price": "$5.00"},
            {"product_id": "", "title": "junk", "quantity": 1, "unit_price": 1.0},
        ],
    )
    assert order is not None
    assert order.status == "shipped" and order.total == 10.0
    assert [i.title for i in order.items] == ["Widget"]


def test_labeled_benchmark_passes() -> None:
    result = run_data_quality()
    assert result["accuracy"] == 1.0, result["failures"]
    assert result["baseline_accuracy"] < result["accuracy"]


def test_storefront_repair_normalizes_and_skips(tmp_path) -> None:
    path = str(tmp_path / "store.sqlite")
    store = SqliteStorefront(path)
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO products (id, title, price, stock, tags)"
        " VALUES ('P9', '  Tent  ', '$120.00', 'out of stock', 'camping, camping')"
    )
    conn.execute(
        "INSERT OR REPLACE INTO products (id, title, price, stock, tags)"
        " VALUES ('P8', '', 'free', '3', '')"
    )
    conn.commit()
    conn.close()

    fixed = store.get("P9")
    assert fixed is not None
    assert (fixed.title, fixed.price, fixed.stock, fixed.tags) == ("Tent", 120.0, 0, ["camping"])
    assert store.get("P8") is None
    assert store.skipped() >= 1


def test_storefront_strict_fails_loud(tmp_path) -> None:
    path = str(tmp_path / "store.sqlite")
    SqliteStorefront(path)
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO products (id, title, price, stock, tags)"
        " VALUES ('P8', '', 'free', '3', '')"
    )
    conn.commit()
    conn.close()

    strict = SqliteStorefront(path, quality="strict")
    try:
        strict.search("anything", 5)
    except ValueError:
        return
    raise AssertionError("strict mode should raise on an invalid row")


def test_repair_script_is_idempotent(tmp_path) -> None:
    path = str(tmp_path / "store.sqlite")
    SqliteStorefront(path)
    conn = sqlite3.connect(path)
    conn.execute(
        "INSERT OR REPLACE INTO products (id, title, price, stock, tags)"
        " VALUES ('P9', '  Tent  ', '$120.00', 'out of stock', 'camping')"
    )
    conn.commit()
    conn.close()

    first = repair(path)
    assert first["products_repaired"] == 1
    second = repair(path)
    assert second["products_repaired"] == 0 and second["products_removed"] == 0
