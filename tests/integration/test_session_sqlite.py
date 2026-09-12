"""Integration tests for the SQLite session repository (feature 005).

Uses a real SQLite file (tier: integration) to prove the log round-trips exactly
(SL-1) and that saving is idempotent (RD-2).
"""

from __future__ import annotations

from pathlib import Path

from app.adapters.session_sqlite import SqliteSessionStore
from app.core.session import (
    AssistantMessage,
    Session,
    ToolResultEvent,
    UserMessage,
    derive_messages,
)
from app.core.types import ToolCall

SYSTEM = "You are a test assistant."


def _sample(session: Session) -> None:
    session.append(UserMessage("I need a tent"))
    session.append(
        AssistantMessage(
            text="Let me look.",
            tool_calls=[ToolCall(id="c1", name="search_products", arguments='{"query": "tent"}')],
        )
    )
    session.append(
        ToolResultEvent(
            call_id="c1", name="search_products", content='{"results": []}', status="ok"
        )
    )
    session.append(AssistantMessage(text="Nothing matched."))
    session.remember_ids(["P-101"])


def test_roundtrip_derive_messages_identical(tmp_path: Path):
    store = SqliteSessionStore(str(tmp_path / "sessions.sqlite"))
    session = store.create()
    _sample(session)
    store.save(session)

    loaded = store.get(session.id)
    assert loaded is not None
    assert derive_messages(loaded, SYSTEM) == derive_messages(session, SYSTEM)
    assert loaded.provenance == {"P-101"}


def test_save_is_idempotent(tmp_path: Path):
    store = SqliteSessionStore(str(tmp_path / "sessions.sqlite"))
    session = store.create()
    _sample(session)
    store.save(session)
    store.save(session)  # no new events

    loaded = store.get(session.id)
    assert loaded is not None
    assert len(loaded.events) == len(session.events)


def test_persistence_across_store_instances(tmp_path: Path):
    path = str(tmp_path / "sessions.sqlite")
    store = SqliteSessionStore(path)
    session = store.create()
    session.append(UserMessage("hello"))
    store.save(session)

    reopened = SqliteSessionStore(path)
    loaded = reopened.get(session.id)
    assert loaded is not None
    assert len(loaded.events) == 1


def test_unknown_session_returns_none(tmp_path: Path):
    store = SqliteSessionStore(str(tmp_path / "sessions.sqlite"))
    assert store.get("does-not-exist") is None
