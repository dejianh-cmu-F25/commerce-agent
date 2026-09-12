"""Unit tests for the deterministic memory extractor (feature 013)."""

from __future__ import annotations

import pytest

from app.memory.extract import extract_facts


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("I usually wear size M", [("profile", "Wears size M")]),
        ("My size is XL", [("profile", "Wears size XL")]),
        ("I'm allergic to wool", [("constraint", "Avoids wool")]),
        ("I avoid crowded places", [("constraint", "Avoids crowded places")]),
        ("I prefer lightweight tents", [("preference", "Prefers lightweight tents")]),
        ("I already own a tent", [("profile", "Owns a tent")]),
        ("My budget is $500", [("constraint", "Budget $500")]),
    ],
)
def test_extracts_durable_facts(text: str, expected: list[tuple[str, str]]):
    assert extract_facts(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "What tents are under $200?",
        "Do you have size M?",
        "Hello there.",
        "Can you help me plan a trip?",
    ],
)
def test_ignores_questions_and_chatter(text: str):
    assert extract_facts(text) == []


def test_multiple_facts_in_one_message():
    facts = extract_facts("I usually wear size M and I'm allergic to wool")
    assert ("profile", "Wears size M") in facts
    assert ("constraint", "Avoids wool") in facts


def test_is_deterministic_and_deduped():
    text = "I like red and I usually wear size M. I like red"
    first = extract_facts(text)
    assert first == extract_facts(text)
    assert first.count(("preference", "Prefers red")) == 1
