"""Integration tests for the eval report endpoint (feature 025)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.core.settings import (
    BudgetSettings,
    LLMSettings,
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
        budget=BudgetSettings(enabled=False, state_file=str(tmp_path / "budget.json")),
    )


def test_report_returns_the_committed_markdown(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path)))
    response = client.get("/report")

    assert response.status_code == 200
    markdown = response.json()["markdown"]
    assert "# Evaluation report" in markdown
    assert "Retrieval benchmark" in markdown
