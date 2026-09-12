"""SQLite customer memory provider (Service Provider for
:class:`app.ports.memory.MemoryStore`).

Durable and file-based (DP-6). Facts are unique per
``(customer_id, kind, text)`` so re-stating a fact never duplicates it (RD-2);
forgetting is a delete, so it is traceable in the store's history.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.core.types import MemoryFact

_SCHEMA = """
CREATE TABLE IF NOT EXISTS memory_facts (
    seq         INTEGER PRIMARY KEY AUTOINCREMENT,
    id          TEXT NOT NULL UNIQUE,
    customer_id TEXT NOT NULL,
    kind        TEXT NOT NULL,
    text        TEXT NOT NULL,
    created_at  TEXT NOT NULL,
    UNIQUE (customer_id, kind, text)
)
"""


class SqliteMemoryStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute(_SCHEMA)
        self._conn.commit()

    @staticmethod
    def _to_fact(row: sqlite3.Row) -> MemoryFact:
        return MemoryFact(
            id=str(row["id"]),
            customer_id=str(row["customer_id"]),
            kind=str(row["kind"]),
            text=str(row["text"]),
            created_at=str(row["created_at"]),
        )

    def add(self, fact: MemoryFact) -> bool:
        cursor = self._conn.execute(
            "INSERT OR IGNORE INTO memory_facts (id, customer_id, kind, text, created_at)"
            " VALUES (?, ?, ?, ?, ?)",
            (fact.id, fact.customer_id, fact.kind, fact.text, fact.created_at),
        )
        self._conn.commit()
        return cursor.rowcount == 1

    def list(self, customer_id: str, limit: int = 50) -> list[MemoryFact]:
        rows = self._conn.execute(
            "SELECT id, customer_id, kind, text, created_at FROM memory_facts"
            " WHERE customer_id = ? ORDER BY seq LIMIT ?",
            (customer_id, max(1, limit)),
        ).fetchall()
        return [self._to_fact(row) for row in rows]

    def forget(self, customer_id: str, fact_id: str) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM memory_facts WHERE customer_id = ? AND id = ?",
            (customer_id, fact_id),
        )
        self._conn.commit()
        return cursor.rowcount == 1

    def forget_all(self, customer_id: str) -> int:
        cursor = self._conn.execute(
            "DELETE FROM memory_facts WHERE customer_id = ?", (customer_id,)
        )
        self._conn.commit()
        return cursor.rowcount
