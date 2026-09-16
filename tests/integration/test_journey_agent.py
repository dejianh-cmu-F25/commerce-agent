"""The wired agent runs the journey tool set with a runtime policy gate (046)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from app.core.session import Session
from app.core.settings import (
    BudgetSettings,
    LLMSettings,
    SessionSettings,
    Settings,
    StorefrontSettings,
)
from web.main import build_agent

ORDER = "gid://shopify/Order/1001"
LINE = "gid://shopify/FulfillmentLineItem/1"


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        llm=LLMSettings(provider="mock"),
        storefront=StorefrontSettings(provider="memory"),
        session=SessionSettings(store="memory"),
        budget=BudgetSettings(enabled=False, state_file=str(tmp_path / "budget.json")),
    )


def _tool_names(tmp_path: Path) -> set[str]:
    agent = build_agent(_settings(tmp_path))
    return {spec.name for spec in agent._tools.specs()}  # noqa: SLF001 - smoke test


def test_journey_tools_are_wired(tmp_path: Path) -> None:
    names = _tool_names(tmp_path)
    expected = {
        "search_products",
        "search_knowledge",
        "get_order_status",
        "list_returnable_items",
        "propose_return_decision",
        "create_checkout_session",
        "complete_checkout",
    }
    assert expected <= names
    assert "start_return" not in names  # the legacy tool is no longer wired


def test_policy_gate_rejects_a_contradicting_proposal(tmp_path: Path) -> None:
    agent = build_agent(_settings(tmp_path))
    session = Session(id="t")

    def propose(decision: str):
        return asyncio.run(
            agent._tools.execute(  # noqa: SLF001 - smoke test
                "propose_return_decision",
                {
                    "order_id": ORDER,
                    "fulfillment_line_item_id": LINE,
                    "decision": decision,
                    "reason": "unwanted",
                },
                session,
            )
        )

    good = propose("eligible")
    assert json.loads(good.content).get("validated") is True

    bad = propose("ineligible")
    assert bad.status == "error"
    assert json.loads(bad.content)["validated"] is False
