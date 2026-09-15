"""Discriminating invariants (feature 046): the assertions must be able to FAIL.

A test set whose assertions cannot fail is saturated. These tests are the
**negative controls**: for every discriminating assertion there is an outcome it
rejects, so a passing run is evidence rather than construction.
"""

from __future__ import annotations

from app.evaluation.invariants import ASSERTIONS, RunOutcome, evaluate

DISCRIMINATING = (
    "has_proposal",
    "proposal_decision_matches",
    "proposal_cites_expected",
    "grounded_ids_only",
    "no_over_budget_price",
)


def test_every_discriminating_assertion_can_fail() -> None:
    """Negative control: each assertion has at least one outcome it rejects."""
    bad = [
        RunOutcome(final_text="hello"),  # has_proposal
        RunOutcome(  # proposal_decision_matches
            final_text="x",
            proposal={"decision": "ineligible", "cited_clauses": []},
            expected_decision="eligible",
        ),
        RunOutcome(  # proposal_cites_expected
            final_text="x",
            proposal={"decision": "eligible", "cited_clauses": []},
            expected_clauses=("returns#window-default",),
        ),
        RunOutcome(  # grounded_ids_only
            final_text="Try gid://shopify/Product/999 (made up)",
            allowed_ids=("gid://shopify/Product/1",),
        ),
        RunOutcome(  # no_over_budget_price
            final_text="The best option is $249.99.", budget=200.0
        ),
    ]
    for name in DISCRIMINATING:
        assert any(not ASSERTIONS[name](outcome) for outcome in bad), f"{name} never fails"


def test_passing_outcomes_pass() -> None:
    good = RunOutcome(
        final_text="The 2-Person Tent (gid://shopify/Product/1) is $189.00.",
        proposal={"decision": "eligible", "cited_clauses": ["returns#window-default"]},
        expected_decision="eligible",
        expected_clauses=("returns#window-default",),
        allowed_ids=("gid://shopify/Product/1",),
        budget=200.0,
    )
    verdict = evaluate(list(DISCRIMINATING), good)
    assert verdict.ok, verdict.failed


def test_citation_and_decision_are_independent() -> None:
    # right decision, wrong/absent citation -> fails
    outcome = RunOutcome(
        final_text="ok",
        proposal={"decision": "eligible", "cited_clauses": []},
        expected_decision="eligible",
        expected_clauses=("returns#window-default",),
    )
    verdict = evaluate(["proposal_decision_matches", "proposal_cites_expected"], outcome)
    assert verdict.failed == ["proposal_cites_expected"]


def test_grounding_is_skipped_without_allowlist() -> None:
    assert ASSERTIONS["grounded_ids_only"](RunOutcome(final_text="gid://shopify/Product/999"))


def test_budget_heuristic_allows_boundary() -> None:
    assert ASSERTIONS["no_over_budget_price"](RunOutcome(final_text="under $200.00", budget=200.0))
    assert not ASSERTIONS["no_over_budget_price"](RunOutcome(final_text="$200.01", budget=200.0))
