"""Unit tests for failure attribution (feature 023)."""

from __future__ import annotations

from app.core.session import AssistantMessage, Session, ToolResultEvent, UserMessage
from app.evaluation.failure import attribute


def test_attributes_the_first_error():
    session = Session(id="s")
    session.append(UserMessage("add P-999"))
    session.append(AssistantMessage(text="", tool_calls=[]))
    session.append(
        ToolResultEvent(
            call_id="c1",
            name="add_to_cart",
            content='{"error": "unknown product id"}',
            status="error",
        )
    )
    session.append(
        ToolResultEvent(call_id="c2", name="add_to_cart", content="Tool failed", status="error")
    )

    result = attribute(session)
    assert result is not None
    assert result.category == "ungrounded_id"
    assert result.step == 1  # the first error, not the second


def test_clean_run_and_reason_categories():
    assert attribute(Session(id="s")) is None

    budget = attribute(Session(id="s"), "budget")
    assert budget is not None and budget.category == "budget"

    max_turns = attribute(Session(id="s"), "max_turns")
    assert max_turns is not None and max_turns.category == "max_turns"


def test_out_of_policy_classification():
    session = Session(id="s")
    session.append(
        ToolResultEvent(
            call_id="c1",
            name="start_return",
            content='{"eligible": false, "reason": "outside window"}',
            status="error",
        )
    )
    result = attribute(session)
    assert result is not None and result.category == "out_of_policy"
