"""Query understanding: rules, LLM rewrite, and its fallback (feature 047)."""

from __future__ import annotations

import asyncio

from app.adapters.query_llm import LlmQueryUnderstanding, parse_plan
from app.adapters.query_rules import RuleQueryUnderstanding
from app.core.types import Finish, TextDelta


def test_rules_extract_a_price_ceiling() -> None:
    plan = asyncio.run(RuleQueryUnderstanding().understand("a gold gift for my wife under $30"))
    assert plan.terms == "a gold gift for my wife under $30"  # terms are not rewritten
    assert plan.where == {"price": {"$lte": 30.0}}


def test_rules_leave_a_plain_need_unfiltered() -> None:
    plan = asyncio.run(RuleQueryUnderstanding().understand("something to keep my ears warm"))
    assert plan.where == {}


def test_rules_do_not_mistake_a_trailing_phrase_for_a_category() -> None:
    # Regression: an earlier version read "in summer" as a category filter and
    # dropped need hit@10 from 0.792 to 0.708.
    plan = asyncio.run(
        RuleQueryUnderstanding().understand("products to keep dyed hair healthy in summer")
    )
    assert plan.where == {}


def test_parse_plan_reads_the_first_json_object() -> None:
    assert parse_plan('noise {"query": "floor cleaner", "max_price": 20} tail') == {
        "query": "floor cleaner",
        "max_price": 20,
    }
    assert parse_plan("no json here") is None


class _FakeLLM:
    def __init__(self, text: str = "", *, fail: bool = False) -> None:
        self._text = text
        self._fail = fail

    async def stream(self, messages, tools=()):
        if self._fail:
            raise RuntimeError("provider down")
        yield TextDelta(self._text)
        yield Finish("stop")


def test_llm_rewrite_returns_terms_and_filter() -> None:
    llm = _FakeLLM('{"query": "floor cleaner for hardwood", "max_price": 25}')
    plan = asyncio.run(LlmQueryUnderstanding(llm, "{query}").understand("clean my floors"))
    assert plan.terms == "floor cleaner for hardwood"
    assert plan.where == {"price": {"$lte": 25.0}}


def test_llm_rewrite_falls_back_on_provider_error() -> None:
    plan = asyncio.run(
        LlmQueryUnderstanding(_FakeLLM(fail=True), "{query}").understand("clean my floors")
    )
    assert plan.terms == "clean my floors"
    assert plan.where == {}


def test_llm_rewrite_falls_back_on_unparseable_output() -> None:
    plan = asyncio.run(
        LlmQueryUnderstanding(_FakeLLM("sorry, I cannot help"), "{query}").understand("hello")
    )
    assert plan.terms == "hello"
