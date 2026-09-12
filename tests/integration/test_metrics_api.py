"""Integration tests for the metrics endpoint (feature 017)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.settings import (
    BudgetSettings,
    LLMSettings,
    ObservabilitySettings,
    SessionSettings,
    Settings,
    StorefrontSettings,
)
from web.main import create_app


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        llm=LLMSettings(provider="mock"),
        storefront=StorefrontSettings(provider="memory"),
        session=SessionSettings(store="memory"),
        observability=ObservabilitySettings(trace_file=str(tmp_path / "traces.jsonl")),
        budget=BudgetSettings(enabled=False, state_file=str(tmp_path / "budget.json")),
    )


def test_metrics_are_empty_before_activity(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path)))
    body = client.get("/metrics").json()

    assert body["window"]["spans"] == 0
    assert body["spans"] == []


def test_metrics_after_a_turn(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path)))
    assert client.post("/chat", json={"message": "hi"}).status_code == 200

    body = client.get("/metrics").json()
    assert body["window"]["spans"] >= 2
    assert {"turn", "llm"} <= {stat["name"] for stat in body["spans"]}
    assert {"currency", "spent", "limit", "remaining"} <= set(body["budget"])
