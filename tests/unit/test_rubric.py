"""Unit tests for the rubric judge (feature 023)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from app.core.types import Finish, LLMEvent, Message, TextDelta, ToolSpec
from app.evaluation.rubric import deterministic_grade, judge_answer


class FakeLLM:
    def __init__(self, text: str) -> None:
        self._text = text

    async def stream(
        self, messages: Sequence[Message], tools: Sequence[ToolSpec] = ()
    ) -> AsyncIterator[LLMEvent]:
        yield TextDelta(self._text)
        yield Finish("stop")


def test_deterministic_grade_vetoes_ungrounded_price():
    result = deterministic_grade("It costs $99.", ["The tent is $189."])
    assert result.veto is True
    assert result.judge == "deterministic"


def test_deterministic_grade_allows_grounded_price():
    result = deterministic_grade("It costs $189.", ["The tent is $189."])
    assert result.veto is False
    assert result.scores["grounding"] == 4


async def test_judge_parses_scores():
    llm = FakeLLM(
        '{"grounding": 4, "correctness": 3, "policy_compliance": 4, "completeness": 2, '
        '"tone": 4, "veto": false, "rationale": "ok"}'
    )
    result = await judge_answer(llm, question="q", answer="a", context="c", grounded_facts=[])
    assert result.scores["grounding"] == 4
    assert result.scores["completeness"] == 2
    assert result.veto is False
    assert result.judge == "deepseek"


async def test_judge_falls_back_on_bad_output():
    llm = FakeLLM("this is not json")
    result = await judge_answer(
        llm, question="q", answer="it costs $9", context="", grounded_facts=["$189"]
    )
    assert result.judge == "deterministic"
    assert result.veto is True
