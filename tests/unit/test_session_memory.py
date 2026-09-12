"""Unit tests for the in-memory session repository (feature 005)."""

from __future__ import annotations

from app.adapters.session_memory import InMemorySessionStore
from app.core.session import UserMessage


def test_create_get_and_get_or_create():
    store = InMemorySessionStore()
    session = store.create()
    assert store.get(session.id) is session
    assert store.get_or_create(session.id) is session

    other = store.get_or_create(None)
    assert other.id != session.id
    assert store.get("missing") is None


def test_save_keeps_the_session_retrievable():
    store = InMemorySessionStore()
    session = store.create()
    session.append(UserMessage("hello"))
    store.save(session)

    loaded = store.get(session.id)
    assert loaded is not None
    assert len(loaded.events) == 1
