"""Integration tests for the customer memory HTTP surface (feature 013)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient

from app.adapters.memory_sqlite import SqliteMemoryStore
from app.core.settings import (
    BudgetSettings,
    LLMSettings,
    MemorySettings,
    ObservabilitySettings,
    SessionSettings,
    Settings,
    StorefrontSettings,
)
from app.core.types import MemoryFact
from web.main import create_app


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        llm=LLMSettings(provider="mock"),
        storefront=StorefrontSettings(provider="memory"),
        session=SessionSettings(store="memory"),
        memory=MemorySettings(provider="sqlite", sqlite_path=str(tmp_path / "memory.sqlite")),
        observability=ObservabilitySettings(trace_file=str(tmp_path / "traces.jsonl")),
        budget=BudgetSettings(enabled=False, state_file=str(tmp_path / "budget.json")),
    )


def test_chat_stores_a_grounded_fact_and_forget(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path)))

    response = client.post(
        "/chat", json={"message": "I usually wear size M", "customer_id": "cust-1"}
    )
    assert response.status_code == 200

    facts = client.get("/memory/cust-1").json()["facts"]
    assert [fact["text"] for fact in facts] == ["Wears size M"]
    assert facts[0]["kind"] == "profile"

    assert client.delete(f"/memory/cust-1/facts/{facts[0]['id']}").status_code == 200
    assert client.get("/memory/cust-1").json()["facts"] == []
    assert client.delete(f"/memory/cust-1/facts/{facts[0]['id']}").status_code == 404


def test_recall_in_a_later_session_is_traced(tmp_path: Path):
    memory = SqliteMemoryStore(str(tmp_path / "memory.sqlite"))
    memory.add(
        MemoryFact(
            id=uuid4().hex[:12],
            customer_id="cust-2",
            kind="profile",
            text="Wears size M",
            created_at=datetime.now(UTC).isoformat(),
        )
    )
    client = TestClient(create_app(_settings(tmp_path)))

    assert client.post("/chat", json={"message": "hi", "customer_id": "cust-2"}).status_code == 200

    spans = [
        json.loads(line)
        for line in (tmp_path / "traces.jsonl").read_text().splitlines()
        if line.strip()
    ]
    recalls = [
        span
        for span in spans
        if span["name"] == "memory" and span["attributes"].get("op") == "recall"
    ]
    assert recalls and recalls[0]["attributes"]["recalled"] == 1


def test_forget_all(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path)))
    client.post("/chat", json={"message": "I like tents", "customer_id": "cust-3"})
    client.post("/chat", json={"message": "I prefer boots", "customer_id": "cust-3"})
    assert len(client.get("/memory/cust-3").json()["facts"]) == 2

    assert client.delete("/memory/cust-3").json()["removed"] == 2
    assert client.get("/memory/cust-3").json()["facts"] == []
