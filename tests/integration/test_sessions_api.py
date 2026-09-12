"""Integration tests for the session HTTP surface (feature 005)."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi.testclient import TestClient

from app.adapters.session_sqlite import SqliteSessionStore
from app.core.session import AssistantMessage, UserMessage
from app.core.settings import (
    BudgetSettings,
    LLMSettings,
    SessionSettings,
    Settings,
    StorefrontSettings,
)
from web.main import create_app


def _settings(
    tmp_path: Path, *, store: Literal["memory", "sqlite"], sqlite_path: str = ""
) -> Settings:
    return Settings(
        llm=LLMSettings(provider="mock"),
        storefront=StorefrontSettings(provider="memory"),
        session=SessionSettings(store=store, sqlite_path=sqlite_path),
        budget=BudgetSettings(enabled=False, state_file=str(tmp_path / "budget.json")),
    )


def test_get_session_returns_derived_messages(tmp_path: Path):
    path = str(tmp_path / "sessions.sqlite")
    seed = SqliteSessionStore(path)
    session = seed.create()
    session.append(UserMessage("hello"))
    session.append(AssistantMessage(text="hi there"))
    seed.save(session)

    client = TestClient(create_app(_settings(tmp_path, store="sqlite", sqlite_path=path)))
    response = client.get(f"/sessions/{session.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["session_id"] == session.id
    assert body["messages"][0] == {"role": "user", "content": "hello"}
    assert body["messages"][1]["role"] == "assistant"


def test_get_unknown_session_is_404(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path, store="memory")))
    assert client.get("/sessions/nope").status_code == 404
