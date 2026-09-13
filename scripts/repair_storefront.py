#!/usr/bin/env python3
"""Repair a storefront: normalize or remove dirty rows (feature 027, RW-2).

Reads the products and orders from the SQLite storefront, rewrites fixable rows to
their normalized form, removes rows that cannot be salvaged, and reports the
counts. Idempotent: a second run reports zero changes (RD-2).
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

from app.core.settings import load_settings
from app.data.quality import normalize_order, normalize_product


def _product_state(row: sqlite3.Row) -> tuple:
    return (row["title"], row["price"], row["stock"], row["tags"])


def _clean_product_state(product) -> tuple:
    return (product.title, product.price, product.stock, ",".join(product.tags))


def repair(path: str) -> dict[str, int]:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    counts = {
        "products_repaired": 0,
        "products_removed": 0,
        "orders_repaired": 0,
        "orders_removed": 0,
    }

    for row in conn.execute("SELECT id, title, price, stock, tags FROM products").fetchall():
        product = normalize_product(dict(row))
        if product is None:
            conn.execute("DELETE FROM products WHERE id = ?", (row["id"],))
            counts["products_removed"] += 1
        elif _clean_product_state(product) != _product_state(row):
            conn.execute(
                "UPDATE products SET title = ?, price = ?, stock = ?, tags = ? WHERE id = ?",
                (product.title, product.price, product.stock, ",".join(product.tags), product.id),
            )
            counts["products_repaired"] += 1

    order_rows = conn.execute(
        "SELECT customer_id, id, status, placed_at, delivered_at, total FROM orders"
    ).fetchall()
    for row in order_rows:
        items = conn.execute(
            "SELECT product_id, title, quantity, unit_price FROM order_items"
            " WHERE customer_id = ? AND order_id = ?",
            (row["customer_id"], row["id"]),
        ).fetchall()
        order = normalize_order(row["customer_id"], dict(row), [dict(item) for item in items])
        if order is None:
            conn.execute(
                "DELETE FROM orders WHERE customer_id = ? AND id = ?",
                (row["customer_id"], row["id"]),
            )
            conn.execute(
                "DELETE FROM order_items WHERE customer_id = ? AND order_id = ?",
                (row["customer_id"], row["id"]),
            )
            counts["orders_removed"] += 1
            continue
        raw_items = [(i["product_id"], i["title"], i["quantity"], i["unit_price"]) for i in items]
        clean_items = [(i.product_id, i.title, i.quantity, i.unit_price) for i in order.items]
        if order.status != row["status"] or order.total != row["total"] or clean_items != raw_items:
            conn.execute(
                "UPDATE orders SET status = ?, placed_at = ?, delivered_at = ?, total = ?"
                " WHERE customer_id = ? AND id = ?",
                (
                    order.status,
                    order.placed_at,
                    order.delivered_at,
                    order.total,
                    order.customer_id,
                    order.id,
                ),
            )
            conn.execute(
                "DELETE FROM order_items WHERE customer_id = ? AND order_id = ?",
                (order.customer_id, order.id),
            )
            conn.executemany(
                "INSERT INTO order_items"
                " (customer_id, order_id, product_id, title, quantity, unit_price)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (order.customer_id, order.id, i.product_id, i.title, i.quantity, i.unit_price)
                    for i in order.items
                ],
            )
            counts["orders_repaired"] += 1

    conn.commit()
    conn.close()
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize/remove dirty storefront rows.")
    parser.add_argument("--path", default=None, help="storefront sqlite path")
    args = parser.parse_args()
    path = args.path or load_settings().storefront.sqlite_path
    if not Path(path).exists():
        print(f"no storefront at {path}")
        return 1
    counts = repair(path)
    print(f"repaired {path}: {json.dumps(counts)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
