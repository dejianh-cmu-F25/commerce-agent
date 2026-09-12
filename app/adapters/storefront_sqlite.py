"""SQLite storefront provider (Service Provider for
:class:`app.ports.storefront.StorefrontBackend`).

Embedded and file-based (DP-6). Seeding is idempotent: ``INSERT OR IGNORE`` keyed
on the product id, so restarts never duplicate rows (RD-2).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.adapters.catalog_seed import SEED_PRODUCTS
from app.adapters.storefront_common import clamp_limit, rank_products
from app.core.types import Product

_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id    TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL,
    tags  TEXT NOT NULL
)
"""


class SqliteStorefront:
    def __init__(self, path: str, seed: list[Product] | None = None) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._seed(SEED_PRODUCTS if seed is None else seed)

    def _seed(self, products: list[Product]) -> None:
        self._conn.executemany(
            "INSERT OR IGNORE INTO products (id, title, price, stock, tags) VALUES (?, ?, ?, ?, ?)",
            [(p.id, p.title, p.price, p.stock, ",".join(p.tags)) for p in products],
        )
        self._conn.commit()

    @staticmethod
    def _to_product(row: sqlite3.Row) -> Product:
        return Product(
            id=str(row["id"]),
            title=str(row["title"]),
            price=float(row["price"]),
            stock=int(row["stock"]),
            tags=[t for t in str(row["tags"]).split(",") if t],
        )

    def _all(self) -> list[Product]:
        rows = self._conn.execute("SELECT id, title, price, stock, tags FROM products").fetchall()
        return [self._to_product(row) for row in rows]

    def count(self) -> int:
        return int(self._conn.execute("SELECT COUNT(*) FROM products").fetchone()[0])

    def search(self, query: str, limit: int) -> list[Product]:
        return rank_products(self._all(), query)[: clamp_limit(limit)]

    def get(self, product_id: str) -> Product | None:
        row = self._conn.execute(
            "SELECT id, title, price, stock, tags FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return self._to_product(row) if row is not None else None
