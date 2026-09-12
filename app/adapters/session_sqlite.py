"""SQLite session repository (Service Provider for
:class:`app.ports.session_store.SessionRepository`).

Events are **append-only**, keyed by ``(session_id, seq)``, so re-saving is
idempotent and the log round-trips exactly (SL-1, RD-2). Provenance and cart are
derived state and are replaced on each save.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.core.session import (
    AssistantMessage,
    CartLine,
    MemoryNote,
    Session,
    SessionEvent,
    ToolResultEvent,
    UserMessage,
)
from app.core.types import ToolCall

_SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
    id          TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS session_events (
    session_id TEXT NOT NULL,
    seq        INTEGER NOT NULL,
    kind       TEXT NOT NULL,
    payload    TEXT NOT NULL,
    PRIMARY KEY (session_id, seq)
);
CREATE TABLE IF NOT EXISTS session_provenance (
    session_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    PRIMARY KEY (session_id, product_id)
);
CREATE TABLE IF NOT EXISTS session_cart (
    session_id TEXT NOT NULL,
    product_id TEXT NOT NULL,
    title      TEXT NOT NULL,
    quantity   INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    PRIMARY KEY (session_id, product_id)
);
"""


def encode_event(event: SessionEvent) -> tuple[str, str]:
    if isinstance(event, UserMessage):
        return "user", json.dumps({"text": event.text})
    if isinstance(event, AssistantMessage):
        return "assistant", json.dumps(
            {
                "text": event.text,
                "tool_calls": [
                    {"id": c.id, "name": c.name, "arguments": c.arguments} for c in event.tool_calls
                ],
            }
        )
    if isinstance(event, ToolResultEvent):
        return "tool_result", json.dumps(
            {
                "call_id": event.call_id,
                "name": event.name,
                "content": event.content,
                "status": event.status,
            }
        )
    if isinstance(event, MemoryNote):
        return "memory", json.dumps({"facts": list(event.facts)})
    raise ValueError(f"Unsupported session event: {type(event).__name__}")


def decode_event(kind: str, payload: str) -> SessionEvent:
    data = json.loads(payload)
    if kind == "user":
        return UserMessage(text=str(data["text"]))
    if kind == "assistant":
        return AssistantMessage(
            text=str(data["text"]),
            tool_calls=[
                ToolCall(id=str(c["id"]), name=str(c["name"]), arguments=str(c["arguments"]))
                for c in data.get("tool_calls", [])
            ],
        )
    if kind == "tool_result":
        return ToolResultEvent(
            call_id=str(data["call_id"]),
            name=str(data["name"]),
            content=str(data["content"]),
            status=str(data.get("status", "ok")),
        )
    if kind == "memory":
        return MemoryNote(facts=[str(fact) for fact in data.get("facts", [])])
    raise ValueError(f"Unknown session event kind: {kind!r}")


class SqliteSessionStore:
    def __init__(self, path: str) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        # FastAPI may run endpoints on a different thread than the one that built
        # the app; SQLite serializes access itself, so allow cross-thread use.
        self._conn = sqlite3.connect(self._path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_SCHEMA)
        self._migrate()

    def _migrate(self) -> None:
        """Add ``customer_id`` to databases created before feature 013."""
        columns = {row["name"] for row in self._conn.execute("PRAGMA table_info(sessions)")}
        if "customer_id" not in columns:
            self._conn.execute(
                "ALTER TABLE sessions ADD COLUMN customer_id TEXT NOT NULL DEFAULT ''"
            )
            self._conn.commit()

    def create(self, customer_id: str = "") -> Session:
        session = Session(id=uuid4().hex, customer_id=customer_id)
        self.save(session)
        return session

    def get(self, session_id: str) -> Session | None:
        row = self._conn.execute("SELECT id FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return None if row is None else self._load(session_id)

    def get_or_create(self, session_id: str | None, customer_id: str = "") -> Session:
        if session_id:
            existing = self.get(session_id)
            if existing is not None:
                if customer_id and not existing.customer_id:
                    existing.customer_id = customer_id
                return existing
        return self.create(customer_id)

    def save(self, session: Session) -> None:
        now = datetime.now(UTC).isoformat()
        self._conn.execute(
            "INSERT OR IGNORE INTO sessions (id, customer_id, created_at) VALUES (?, ?, ?)",
            (session.id, session.customer_id, now),
        )
        if session.customer_id:
            self._conn.execute(
                "UPDATE sessions SET customer_id = ? WHERE id = ? AND customer_id = ''",
                (session.customer_id, session.id),
            )
        self._conn.executemany(
            "INSERT OR IGNORE INTO session_events (session_id, seq, kind, payload)"
            " VALUES (?, ?, ?, ?)",
            [(session.id, i, *encode_event(e)) for i, e in enumerate(session.events)],
        )
        self._conn.execute("DELETE FROM session_provenance WHERE session_id = ?", (session.id,))
        self._conn.executemany(
            "INSERT OR IGNORE INTO session_provenance (session_id, product_id) VALUES (?, ?)",
            [(session.id, pid) for pid in sorted(session.provenance)],
        )
        self._conn.execute("DELETE FROM session_cart WHERE session_id = ?", (session.id,))
        self._conn.executemany(
            "INSERT OR IGNORE INTO session_cart"
            " (session_id, product_id, title, quantity, unit_price) VALUES (?, ?, ?, ?, ?)",
            [
                (session.id, line.product_id, line.title, line.quantity, line.unit_price)
                for line in session.cart
            ],
        )
        self._conn.commit()

    def _load(self, session_id: str) -> Session:
        row = self._conn.execute(
            "SELECT customer_id FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        session = Session(id=session_id, customer_id=str(row["customer_id"]) if row else "")
        session.events = [
            decode_event(row["kind"], row["payload"])
            for row in self._conn.execute(
                "SELECT kind, payload FROM session_events WHERE session_id = ? ORDER BY seq",
                (session_id,),
            )
        ]
        session.provenance = {
            row["product_id"]
            for row in self._conn.execute(
                "SELECT product_id FROM session_provenance WHERE session_id = ?", (session_id,)
            )
        }
        session.cart = [
            CartLine(
                product_id=row["product_id"],
                title=row["title"],
                quantity=row["quantity"],
                unit_price=row["unit_price"],
            )
            for row in self._conn.execute(
                "SELECT product_id, title, quantity, unit_price FROM session_cart"
                " WHERE session_id = ?",
                (session_id,),
            )
        ]
        return session
