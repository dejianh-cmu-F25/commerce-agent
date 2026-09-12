"""Unit tests for the customer memory providers (feature 013)."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.adapters.memory_memory import InMemoryMemoryStore
from app.adapters.memory_sqlite import SqliteMemoryStore
from app.core.types import MemoryFact


def _fact(
    customer: str = "c1", kind: str = "preference", text: str = "Prefers tents"
) -> MemoryFact:
    return MemoryFact(
        id=uuid4().hex[:12],
        customer_id=customer,
        kind=kind,
        text=text,
        created_at=datetime.now(UTC).isoformat(),
    )


def _contract(store) -> None:
    assert store.add(_fact()) is True
    assert store.add(_fact()) is False  # idempotent per (customer, kind, text)
    assert store.add(_fact(text="Prefers boots")) is True

    facts = store.list("c1")
    assert [fact.text for fact in facts] == ["Prefers tents", "Prefers boots"]
    assert store.list("other") == []

    target = facts[0].id
    assert store.forget("c1", target) is True
    assert store.forget("c1", target) is False
    assert [fact.text for fact in store.list("c1")] == ["Prefers boots"]

    assert store.forget_all("c1") == 1
    assert store.list("c1") == []


def test_in_memory_store_contract():
    _contract(InMemoryMemoryStore())


def test_sqlite_store_contract(tmp_path: Path):
    _contract(SqliteMemoryStore(str(tmp_path / "memory.sqlite")))


def test_facts_are_isolated_by_customer():
    store = InMemoryMemoryStore()
    store.add(_fact(customer="a", text="Prefers tents"))
    store.add(_fact(customer="b", text="Prefers boots"))
    assert [f.text for f in store.list("a")] == ["Prefers tents"]
    assert [f.text for f in store.list("b")] == ["Prefers boots"]
