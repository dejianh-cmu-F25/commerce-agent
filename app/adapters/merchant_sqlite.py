"""SQLite merchant provider (Service Provider for
:class:`app.ports.merchant.MerchantBackend`).

Shares the storefront's SQLite file. Changes are **staged** in
``pending_changes`` and only written to ``products`` on ``apply`` (P3). Applying
twice is a no-op (RD-2).
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.types import Change, Product

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pending_changes (
    id         TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    kind       TEXT NOT NULL,
    old_value  REAL NOT NULL,
    new_value  REAL NOT NULL,
    status     TEXT NOT NULL,
    created_at TEXT NOT NULL
)
"""


class SqliteMerchant:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
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

    def _get(self, product_id: str) -> Product | None:
        row = self._conn.execute(
            "SELECT id, title, price, stock, tags FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return self._to_product(row) if row is not None else None

    def list_products(self, limit: int = 100) -> list[Product]:
        rows = self._conn.execute(
            "SELECT id, title, price, stock, tags FROM products ORDER BY id LIMIT ?",
            (max(1, limit),),
        ).fetchall()
        return [self._to_product(row) for row in rows]

    def stage_change(self, product_id: str, kind: str, new_value: float) -> Change:
        if kind not in ("price", "stock"):
            raise ValueError(f"unknown change kind: {kind!r}")
        product = self._get(product_id)
        if product is None:
            raise ValueError(f"unknown product id: {product_id!r}")
        if kind == "price" and new_value <= 0:
            raise ValueError("price must be greater than 0")
        if kind == "stock" and new_value < 0:
            raise ValueError("stock must be 0 or greater")

        old_value = product.price if kind == "price" else float(product.stock)
        change = Change(
            id=uuid4().hex[:12],
            product_id=product_id,
            kind=kind,
            old_value=old_value,
            new_value=float(new_value),
            status="pending",
            created_at=datetime.now(UTC).isoformat(),
        )
        self._conn.execute(
            "INSERT INTO pending_changes (id, product_id, kind, old_value, new_value, status,"
            " created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                change.id,
                change.product_id,
                change.kind,
                change.old_value,
                change.new_value,
                change.status,
                change.created_at,
            ),
        )
        self._conn.commit()
        return change

    def pending(self) -> list[Change]:
        rows = self._conn.execute(
            "SELECT id, product_id, kind, old_value, new_value, status, created_at"
            " FROM pending_changes WHERE status = 'pending' ORDER BY created_at"
        ).fetchall()
        return [
            Change(
                id=str(row["id"]),
                product_id=str(row["product_id"]),
                kind=str(row["kind"]),
                old_value=float(row["old_value"]),
                new_value=float(row["new_value"]),
                status=str(row["status"]),
                created_at=str(row["created_at"]),
            )
            for row in rows
        ]

    def apply(self, change_id: str) -> Change | None:
        row = self._conn.execute(
            "SELECT id, product_id, kind, old_value, new_value, status, created_at"
            " FROM pending_changes WHERE id = ? AND status = 'pending'",
            (change_id,),
        ).fetchone()
        if row is None:
            return None  # unknown or already applied (no double-apply)

        column = "price" if str(row["kind"]) == "price" else "stock"
        self._conn.execute(
            f"UPDATE products SET {column} = ? WHERE id = ?",  # noqa: S608 - fixed column set
            (float(row["new_value"]), str(row["product_id"])),
        )
        self._conn.execute(
            "UPDATE pending_changes SET status = 'applied' WHERE id = ?", (change_id,)
        )
        self._conn.commit()
        return Change(
            id=str(row["id"]),
            product_id=str(row["product_id"]),
            kind=str(row["kind"]),
            old_value=float(row["old_value"]),
            new_value=float(row["new_value"]),
            status="applied",
            created_at=str(row["created_at"]),
        )
