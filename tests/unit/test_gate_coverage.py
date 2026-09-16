"""Meta-test: every money-adjacent tool in the production agent is gated.

The fail-closed rule (046 hardening) refuses a ``proposal`` / ``irreversible`` tool
that no gate covers, and this asserts the *production* wiring actually covers them,
so a new such tool cannot ship ungated by accident.
"""

from __future__ import annotations

from app.adapters.mock_llm import MockLLMClient, text_turn
from app.core.settings import load_settings
from web.main import build_agent


def _production_registry():
    settings = load_settings()
    agent = build_agent(settings, llm=MockLLMClient([text_turn("ok")] * 4))
    return agent._tools  # noqa: SLF001 - the registry is the unit under test


def test_no_money_adjacent_tool_is_ungated():
    registry = _production_registry()
    effects = registry.effects()
    # Sanity: the classes exist in the production surface.
    assert effects.get("propose_return_decision") == "proposal"
    assert effects.get("complete_checkout") == "irreversible"
    assert registry.gated_uncovered() == [], registry.gated_uncovered()


def test_named_tools_are_covered_by_their_gate():
    registry = _production_registry()
    gates = registry._gates  # noqa: SLF001 - the resolved gate set
    assert gates is not None
    assert gates.covers("propose_return_decision", "proposal")
    assert gates.covers("complete_checkout", "irreversible")
    assert gates.covers("add_to_cart", "write")
    assert "policy" in gates.names() and "approval" in gates.names()
