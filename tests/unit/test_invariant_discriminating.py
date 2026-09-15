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
    "quotes_are_grounded",
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
        RunOutcome(  # quotes_are_grounded
            final_text='Customers say "the battery dies after two hours of use".'
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


def test_a_quotation_must_come_from_the_tool_results() -> None:
    """The review failure mode: "customers say ..." with words no customer wrote."""
    evidence = RunOutcome(
        final_text='Customers say "The insole made them super tight almost too small."',
        tool_output=("The insole made them super tight almost too small.",),
    )
    assert ASSERTIONS["quotes_are_grounded"](evidence)

    invented = RunOutcome(
        final_text='Customers say "The zipper broke on the second day of a short trip."',
        tool_output=("The insole made them super tight almost too small.",),
    )
    assert not ASSERTIONS["quotes_are_grounded"](invented)


def test_a_quotation_with_no_tool_output_is_not_grounded() -> None:
    assert not ASSERTIONS["quotes_are_grounded"](
        RunOutcome(final_text='Customers say "the battery dies after two hours of use".')
    )


def test_short_quoted_words_are_emphasis_not_evidence() -> None:
    """People write "runs small" in quotes; that is not a citation."""
    assert ASSERTIONS["quotes_are_grounded"](
        RunOutcome(final_text='The shoes "run small", so size up.', tool_output=())
    )


def test_markdown_between_two_quotations_is_not_a_quotation() -> None:
    """Regression, found by validating the assertion against a real answer.

    A pattern that looks for "text between quote marks" matched from the closing mark
    of one review to the opening mark of the next, so the markdown in between
    ("** (4/5, top review): *") was reported as fabricated evidence.
    """
    answer = (
        'Customers say "It is a Madden game, so it is going to be fun." '
        "** (4.0/5, most helpful): *"
        '"GREAT PRICE GREAT! BEST PRODUCT EVER WOULD BUY AGAIN."*'
    )
    outcome = RunOutcome(
        final_text=answer,
        tool_output=(
            "It is a Madden game, so it is going to be fun.",
            "GREAT PRICE GREAT! BEST PRODUCT EVER WOULD BUY AGAIN.",
        ),
    )
    assert ASSERTIONS["quotes_are_grounded"](outcome)


def test_an_invented_order_number_is_caught_but_a_read_is_allowed():
    """Reading is how the agent learns the real number; writing one down is not."""
    grounded = RunOutcome(
        final_text="I don't see any orders on your account - what is the order number?",
        tool_calls=("list_orders",),
        tool_output=('{"orders": []}',),
    )
    assert ASSERTIONS["order_refs_are_grounded"](grounded)

    invented = RunOutcome(
        final_text="Sure, use order #12345 and I'll proceed.",
        tool_calls=("list_orders",),
        tool_output=('{"orders": []}',),
    )
    assert not ASSERTIONS["order_refs_are_grounded"](invented)

    quoted = RunOutcome(
        final_text="Your order #1006 was delivered.", tool_output=("order #1006 delivered",)
    )
    assert ASSERTIONS["order_refs_are_grounded"](quoted)
