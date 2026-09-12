"""Unit tests for parameterized real-eval cases (feature 024)."""

from __future__ import annotations

from evals.real_cases import CASE_NAMES, build_cases


def test_template_names_are_stable_and_parameters_vary():
    first = build_cases(0)
    second = build_cases(1)

    assert [case.name for case in first] == CASE_NAMES
    assert [case.name for case in second] == CASE_NAMES

    first_text = {case.name: case.user_text for case in first}
    second_text = {case.name: case.user_text for case in second}
    assert first_text != second_text  # at least one parameter changed


def test_construction_is_reproducible():
    assert build_cases(2) == build_cases(2)


def test_predicates_are_present():
    cases = {case.name: case for case in build_cases(0)}
    assert cases["budget_search"].max_price is not None
    assert cases["multi_item_cart"].min_cart_items == 2
    assert cases["ungrounded_rejected"].must_have_empty_cart is True
    assert "return" in cases["refuse_out_of_window"].forbidden_components
