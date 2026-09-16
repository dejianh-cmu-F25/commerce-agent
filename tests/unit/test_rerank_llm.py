"""The LLM listwise reranker: it reorders, records cost, and never breaks search."""

from __future__ import annotations

import asyncio

from app.adapters.cost_meter import UsageCostMeter
from app.adapters.rerank_llm import LlmListwiseReranker, parse_order
from app.core.settings import BudgetSettings
from app.core.types import Finish, TextDelta, Usage


class FakeLLM:
    """Streams a scripted answer; optionally raises instead."""

    def __init__(self, text: str = "", *, fail: bool = False) -> None:
        self._text = text
        self._fail = fail
        self.calls = 0

    async def stream(self, messages, tools=()):
        self.calls += 1
        if self._fail:
            raise RuntimeError("provider down")
        yield TextDelta(self._text)
        yield Usage(prompt_tokens=1000, completion_tokens=10)
        yield Finish("stop")


CANDIDATES = ["a red tent", "a blue tent", "a camping stove"]


def test_parse_order_accepts_only_a_full_permutation():
    assert parse_order("here: [3,1,2]", 3) == [2, 0, 1]
    assert parse_order("```json\n[2,1,3]\n```", 3) == [1, 0, 2]
    # Not a permutation -> unusable, the caller keeps the original order.
    assert parse_order("[1,1,2]", 3) is None
    assert parse_order("[1,2]", 3) is None
    assert parse_order("no array here", 3) is None


def test_rerank_reorders_by_the_model_answer(tmp_path):
    reranker = LlmListwiseReranker(FakeLLM("[3,1,2]"), top_k=3)
    ranked = asyncio.run(reranker.rerank("a tent", list(CANDIDATES)))
    assert ranked == ["a camping stove", "a red tent", "a blue tent"]


def test_unparseable_answer_keeps_the_retrieval_order():
    reranker = LlmListwiseReranker(FakeLLM("I cannot help with that."), top_k=3)
    assert asyncio.run(reranker.rerank("a tent", list(CANDIDATES))) == CANDIDATES


def test_a_provider_failure_keeps_the_retrieval_order():
    reranker = LlmListwiseReranker(FakeLLM(fail=True), top_k=3)
    assert asyncio.run(reranker.rerank("a tent", list(CANDIDATES))) == CANDIDATES


def test_it_records_its_own_usage(tmp_path):
    """It runs outside the agent loop, so nothing else would meter it."""
    meter = UsageCostMeter(BudgetSettings(state_file=str(tmp_path / "budget.json")))
    reranker = LlmListwiseReranker(FakeLLM("[3,1,2]"), top_k=3, cost_meter=meter)
    asyncio.run(reranker.rerank("a tent", list(CANDIDATES)))
    assert meter.spent_cny() > 0


def test_a_single_candidate_is_not_worth_a_call():
    llm = FakeLLM("[1]")
    reranker = LlmListwiseReranker(llm, top_k=1)
    assert asyncio.run(reranker.rerank("a tent", ["only one"])) == ["only one"]
    assert llm.calls == 0


class HangingLLM:
    """Streams nothing and never returns, like a stalled provider socket."""

    async def stream(self, messages, tools=()):
        await asyncio.sleep(3600)
        yield TextDelta("")


def test_a_hung_provider_does_not_hang_search():
    """A stalled call must fall back, not block the turn (observed in the probe)."""
    reranker = LlmListwiseReranker(HangingLLM(), top_k=3, timeout_s=0.05)
    assert asyncio.run(reranker.rerank("a tent", list(CANDIDATES))) == CANDIDATES
    assert reranker.timeouts == 1
