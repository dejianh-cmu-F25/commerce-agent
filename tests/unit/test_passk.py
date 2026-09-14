"""Pass^k and fault attribution (feature 046)."""

from __future__ import annotations

from app.evaluation.passk import attribute, pass_k


def test_pass_k_counts_all_k() -> None:
    # task 1 solved every time, task 2 flaky, task 3 never
    assert pass_k([[True, True], [True, False], [False, False]]) == 1 / 3


def test_pass_k_empty() -> None:
    assert pass_k([]) == 0.0


def test_attribute_no_failure() -> None:
    fault = attribute(passed=True)
    assert fault.entity == "agent"
    assert fault.type == "no_failure"


def test_attribute_environment_error() -> None:
    fault = attribute(passed=False, error=True)
    assert fault.entity == "environment"
    assert fault.type == "took_unintended_action"


def test_attribute_missing_tool() -> None:
    fault = attribute(
        passed=False,
        tool_calls=("search_products",),
        expected_tools=("search_products", "get_order_status"),
    )
    assert fault.type == "used_wrong_tool"
    assert "get_order_status" in fault.detail


def test_attribute_unexpected_tool() -> None:
    fault = attribute(passed=False, tool_calls=("a", "b"), expected_tools=("a",))
    assert fault.type == "used_wrong_tool"
    assert "unexpected" in fault.detail


def test_attribute_partial() -> None:
    assert (
        attribute(passed=False, tool_calls=("a",), expected_tools=("a",)).type
        == "goal_partially_completed"
    )
