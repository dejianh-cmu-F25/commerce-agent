"""The post-purchase decision set is well-formed and self-consistent (045)."""

from __future__ import annotations

import json
from pathlib import Path

from app.returns.clauses import load_policy

CASES = Path("evals/post_purchase_cases.jsonl")
POLICY = load_policy("config/policies/policies.yaml")
DECISIONS = {"eligible", "ineligible", "escalate", "answer_status", "clarify"}
REQUIRED = {"case_id", "intent", "message", "expected_decision", "status"}


def _cases() -> list[dict]:
    return [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]


def test_cases_are_well_formed() -> None:
    cases = _cases()
    assert len(cases) >= 15
    ids = [case["case_id"] for case in cases]
    assert len(ids) == len(set(ids)), "duplicate case_id"
    for case in cases:
        assert REQUIRED <= case.keys(), f"{case.get('case_id')} missing fields"
        assert case["expected_decision"] in DECISIONS, case["expected_decision"]


def test_policy_refs_resolve_to_real_clauses() -> None:
    known = {clause.id for clause in POLICY.clauses} | {"warranty"}
    for case in _cases():
        for ref in case.get("expected_policy_refs", []):
            assert ref in known, f"{case['case_id']} cites unknown clause {ref!r}"


def test_boundary_cases_are_both_present() -> None:
    decisions = {case["case_id"]: case["expected_decision"] for case in _cases()}
    assert decisions["return-window-edge-30"] == "eligible"
    assert decisions["return-window-edge-31"] == "ineligible"
