"""Integration tests for the Scenario Runner API (feature 016)."""

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


def test_list_scenarios_returns_the_catalog(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path)))
    response = client.get("/scenarios")

    assert response.status_code == 200
    scenarios = response.json()["scenarios"]
    assert scenarios
    names = {scenario["name"] for scenario in scenarios}
    assert {"search_only", "add_to_cart", "start_return"} <= names
    assert all(
        {"user_text", "expect_tools", "expect_components"} <= set(scenario)
        for scenario in scenarios
    )


def test_run_scenarios_pass_keylessly(tmp_path: Path):
    client = TestClient(create_app(_settings(tmp_path)))
    response = client.post("/scenarios/run")

    assert response.status_code == 200
    results = response.json()["results"]
    assert results
    failed = [result["name"] for result in results if not result["ok"]]
    assert not failed, failed
    assert all({"tools", "components"} <= set(result) for result in results)
