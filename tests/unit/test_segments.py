"""Intent/tool segmentation of run results (feature 030, SC-2)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.evaluation.segments import by_intent, by_tool


@dataclass
class Result:
    ok: bool
    intent: str
    tool_results: list[tuple[str, str]] = field(default_factory=list)


def test_by_intent_groups_and_rates() -> None:
    results = [Result(True, "search"), Result(False, "search"), Result(True, "orders")]
    assert by_intent(results) == {
        "orders": {"passed": 1.0, "total": 1.0, "pass_rate": 1.0},
        "search": {"passed": 1.0, "total": 2.0, "pass_rate": 0.5},
    }


def test_by_tool_counts_errors() -> None:
    results = [
        Result(True, "cart", [("add_to_cart", "ok")]),
        Result(True, "cart", [("add_to_cart", "error"), ("search_products", "ok")]),
    ]
    assert by_tool(results) == {
        "add_to_cart": {"calls": 2.0, "errors": 1.0, "error_rate": 0.5},
        "search_products": {"calls": 1.0, "errors": 0.0, "error_rate": 0.0},
    }


def test_empty_results() -> None:
    assert by_intent([]) == {}
    assert by_tool([]) == {}
