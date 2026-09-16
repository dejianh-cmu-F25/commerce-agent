"""The post-purchase decision set is well-formed and self-consistent (045)."""

from __future__ import annotations

import json
from pathlib import Path

from app.returns.amazon_policy import load_amazon_policy

CASES = Path("evals/post_purchase_cases.jsonl")
POLICY = load_amazon_policy("config/policies/amazon.yaml")
DECISIONS = {"eligible", "ineligible", "escalate", "answer_status", "clarify"}
REQUIRED = {"case_id", "intent", "message", "expected_decision", "status"}


def _cases() -> list[dict]:
    return [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]


def test_cases_are_well_formed() -> None:
    cases = _cases()
    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids)), "duplicate case_id"
    for case in cases:
        assert REQUIRED <= case.keys(), f"{case.get('case_id')} missing fields"
        assert case["expected_decision"] in DECISIONS, case["expected_decision"]


def test_every_outcome_the_corpus_claims_to_measure_is_present() -> None:
    """Coverage, not a count: a corpus that lost a whole outcome category can still be
    "well formed", and a bare size floor would not notice."""
    outcomes = {case["expected_decision"] for case in _cases()}
    assert {"eligible", "ineligible", "escalate"} <= outcomes, outcomes


def test_policy_refs_resolve_to_real_clauses() -> None:
    # No tolerance list: an expectation naming a clause that does not exist is a stale
    # expectation, and the tolerance is what let one hide (it read "warranty" where the
    # clause is "returns#warranty").
    known = {clause.id for clause in POLICY.clauses()}
    for case in _cases():
        for ref in case.get("expected_policy_refs", []):
            assert ref in known, f"{case['case_id']} cites unknown clause {ref!r}"


def test_boundary_cases_are_both_present() -> None:
    decisions = {case["case_id"]: case["expected_decision"] for case in _cases()}
    assert decisions["return-window-edge-30"] == "eligible"
    assert decisions["return-window-edge-31"] == "ineligible"
