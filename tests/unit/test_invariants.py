"""Behavioral invariant checker and case file (feature 045)."""

from __future__ import annotations

import json
from pathlib import Path

from app.evaluation.invariants import ASSERTIONS, RunOutcome, evaluate

CASES = Path("evals/invariant_cases.jsonl")
VALID_INVARIANTS = {f"INV-{n}" for n in range(1, 9)}


def test_clean_run_passes_all_assertions() -> None:
    outcome = RunOutcome(reason="stop", final_text="I can help with orders and returns.")
    result = evaluate(["no_error", "no_tool_call", "has_text"], outcome)
    assert result.ok and result.failed == []


def test_no_error_fails_on_error_reason() -> None:
    result = evaluate(["no_error"], RunOutcome(reason="error", error=True, final_text="x"))
    assert not result.ok and result.failed == ["no_error"]


def test_no_tool_call_fails_when_a_tool_ran() -> None:
    outcome = RunOutcome(tool_calls=("search_products",), final_text="x")
    assert evaluate(["no_tool_call"], outcome).failed == ["no_tool_call"]


def test_no_write_tool_allows_reads_but_blocks_writes() -> None:
    read = RunOutcome(tool_calls=("get_order_status",), final_text="x")
    assert evaluate(["no_write_tool"], read).ok
    write = RunOutcome(tool_calls=("return_approve",), final_text="x")
    assert evaluate(["no_write_tool"], write).failed == ["no_write_tool"]


def test_within_turns_bound() -> None:
    assert evaluate(["within_turns"], RunOutcome(turns=8, max_turns=8)).ok
    assert evaluate(["within_turns"], RunOutcome(turns=9, max_turns=8)).failed == ["within_turns"]


def test_no_prompt_leak_detects_a_verbatim_window() -> None:
    prompt = "You are the post-purchase assistant for ACME. Never invent an order id."
    leaked = RunOutcome(final_text=prompt[10:70], system_prompt=prompt)
    assert evaluate(["no_prompt_leak"], leaked).failed == ["no_prompt_leak"]
    safe = RunOutcome(final_text="I can help you with returns.", system_prompt=prompt)
    assert evaluate(["no_prompt_leak"], safe).ok


def test_unknown_assertion_fails_loud() -> None:
    assert evaluate(["not_a_real_assertion"], RunOutcome()).failed == ["not_a_real_assertion"]


def test_all_assertion_names_are_registered() -> None:
    assert {
        "no_error",
        "no_tool_call",
        "no_write_tool",
        "has_text",
        "within_turns",
        "no_prompt_leak",
    } <= set(ASSERTIONS)
    # discriminating assertions (feature 046) are also registered
    assert {
        "has_proposal",
        "proposal_decision_matches",
        "proposal_cites_expected",
        "grounded_ids_only",
        "no_over_budget_price",
    } <= set(ASSERTIONS)


def test_case_file_is_well_formed() -> None:
    cases = [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]
    assert len(cases) >= 14
    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids))
    for case in cases:
        assert case["invariant"] in VALID_INVARIANTS, case["invariant"]
        assert case["expected_behavior"] in {"redirect", "refuse", "clarify", "propose", "answer"}
        assert "message" in case or "pad_to_chars" in case
        for name in case["assert"]:
            assert name in ASSERTIONS, f"{case['case_id']} asserts unknown {name!r}"
