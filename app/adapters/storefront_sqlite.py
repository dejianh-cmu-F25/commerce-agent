"""SQLite storefront provider (Service Provider for
:class:`app.ports.storefront.StorefrontBackend`).

Embedded and file-based (DP-6). Seeding is idempotent: ``INSERT OR IGNORE`` keyed
on the product id, so restarts never duplicate rows (RD-2).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.order_seed import demo_orders
from app.adapters.storefront_common import clamp_limit, rank_products
from app.core.types import Order, Product
from app.data.quality import normalize_order, normalize_product

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id    TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    tags  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS orders (
    customer_id  TEXT NOT NULL,
    id           TEXT NOT NULL,
    status       TEXT NOT NULL,
    placed_at    TEXT NOT NULL,
    delivered_at TEXT,
    total        REAL NOT NULL,
    PRIMARY KEY (customer_id, id)
);
CREATE TABLE IF NOT EXISTS order_items (
    customer_id TEXT NOT NULL,
    order_id    TEXT NOT NULL,
    product_id  TEXT NOT NULL,
    title       TEXT NOT NULL,
    quantity    INTEGER NOT NULL,
    unit_price  REAL NOT NULL,
    PRIMARY KEY (customer_id, order_id, product_id)
)
"""


class SqliteStorefront:
    def __init__(
        self,
        path: str,
        seed: list[Product] | None = None,
        seed_orders: bool = True,
        quality: str = "repair",
    ) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._seed_orders = seed_orders
        self._quality = quality
        self._skipped = 0
        self._seed(SEED_PRODUCTS if seed is None else seed)

    def _seed(self, products: list[Product]) -> None:
        self._conn.executemany(
            "INSERT OR IGNORE INTO products (id, title, price, stock, tags) VALUES (?, ?, ?, ?, ?)",
            [(p.id, p.title, p.price, p.stock, ",".join(p.tags)) for p in products],
        )
        self._conn.commit()

    def _to_product(self, row: sqlite3.Row) -> Product | None:
        """Normalize a catalog row at the boundary (feature 027, RW-2)."""
        product = normalize_product(dict(row))
        if product is None:
            self._skipped += 1
            if self._quality == "strict":
                raise ValueError(f"invalid product row: {dict(row)!r}")
        return product

    def _all(self) -> list[Product]:
        rows = self._conn.execute("SELECT id, title, price, stock, tags FROM products").fetchall()
        products = [self._to_product(row) for row in rows]
        return [product for product in products if product is not None]

    def skipped(self) -> int:
        """Number of unusable rows skipped since construction (repair mode)."""
        return self._skipped

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM products").fetchone()[0])

    def search(self, query: str, limit: int, *, evidence: bool = False) -> list[Product]:
        # One index, so the query class does not change the answer.
        del evidence
        return rank_products(self._all(), query)[: clamp_limit(limit)]

    def get(self, product_id: str) -> Product | None:
        row = self._conn.execute(
            "SELECT id, title, price, stock, tags FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return self._to_product(row) if row is not None else None

    def _seed_demo_orders(self, customer_id: str) -> None:
        for order in demo_orders(customer_id):
            self._conn.execute(
                "INSERT OR IGNORE INTO orders"
                " (customer_id, id, status, placed_at, delivered_at, total)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (
                    customer_id,
                    order.id,
                    order.status,
                    order.placed_at,
                    order.delivered_at,
                    order.total,
                ),
            )
            self._conn.executemany(
                "INSERT OR IGNORE INTO order_items"
                " (customer_id, order_id, product_id, title, quantity, unit_price)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        customer_id,
                        order.id,
                        item.product_id,
                        item.title,
                        item.quantity,
                        item.unit_price,
                    )
                    for item in order.items
                ],
            )
        self._conn.commit()

    def _order_rows(self, customer_id: str) -> list[sqlite3.Row]:
        return self._conn.execute(
            "SELECT id, status, placed_at, delivered_at, total FROM orders"
            " WHERE customer_id = ? ORDER BY placed_at DESC",
            (customer_id,),
        ).fetchall()

    def _to_order(self, customer_id: str, row: sqlite3.Row) -> Order | None:
        """Normalize an order row (and its items) at the boundary (RW-2)."""
        items = self._conn.execute(
            "SELECT product_id, title, quantity, unit_price FROM order_items"
            " WHERE customer_id = ? AND order_id = ?",
            (customer_id, row["id"]),
        ).fetchall()
        order = normalize_order(customer_id, dict(row), [dict(item) for item in items])
        if order is None:
            self._skipped += 1
            if self._quality == "strict":
                raise ValueError(f"invalid order row: {dict(row)!r}")
        return order

    def list_orders(self, customer_id: str) -> list[Order]:
        if not customer_id:
            return []
        rows = self._order_rows(customer_id)
        if not rows and self._seed_orders:
            self._seed_demo_orders(customer_id)
            rows = self._order_rows(customer_id)
        orders = [self._to_order(customer_id, row) for row in rows]
        return [order for order in orders if order is not None]

    def get_order(self, customer_id: str, order_id: str) -> Order | None:
        if not customer_id:
            return None
        row = self._conn.execute(
            "SELECT id, status, placed_at, delivered_at, total FROM orders"
            " WHERE customer_id = ? AND id = ?",
            (customer_id, order_id),
        ).fetchone()
        if row is None and self._seed_orders:
            self._seed_demo_orders(customer_id)
            row = self._conn.execute(
                "SELECT id, status, placed_at, delivered_at, total FROM orders"
                " WHERE customer_id = ? AND id = ?",
                (customer_id, order_id),
            ).fetchone()
        return self._to_order(customer_id, row) if row is not None else None
