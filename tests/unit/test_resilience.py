"""Dependency fallback: degrade, record, don't retry (feature 031, RD-1)."""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence

from app.adapters.mock_llm import MockLLMClient, text_turn
from app.adapters.retriever_memory import InMemoryRetriever
from app.core.resilience import FallbackLLM, FallbackRetriever
from app.core.types import Chunk, LLMEvent, Message, TextDelta, ToolSpec
from evals.fallbacks import run_fallbacks


class _Failing:
    def __init__(self) -> None:
        self.attempts = 0

    def add(self, chunks: list[Chunk]) -> None:
        return None

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        self.attempts += 1
        raise RuntimeError("down")


def _chunks() -> list[Chunk]:
    return [Chunk(id="c1", text="return policy within 30 days", source="returns")]


def test_falls_back_and_records_once_without_retrying() -> None:
    primary = _Failing()
    secondary = InMemoryRetriever()
    secondary.add(_chunks())
    wrapper = FallbackRetriever(primary, secondary)

    assert wrapper.retrieve("return", 3)
    assert wrapper.degraded
    assert len(wrapper.degradations) == 1
    assert wrapper.degradations[0].component == "retriever"
    wrapper.retrieve("again", 3)
    assert primary.attempts == 1  # not retried after it failed


def test_healthy_primary_is_not_degraded() -> None:
    primary = InMemoryRetriever()
    primary.add(_chunks())
    secondary = InMemoryRetriever()
    secondary.add(_chunks())
    wrapper = FallbackRetriever(primary, secondary)
    assert wrapper.retrieve("return", 3)
    assert not wrapper.degraded


def test_disabled_fallback_propagates() -> None:
    secondary = InMemoryRetriever()
    secondary.add(_chunks())
    wrapper = FallbackRetriever(_Failing(), secondary, enabled=False)
    try:
        wrapper.retrieve("return", 3)
    except RuntimeError:
        return
    raise AssertionError("a disabled fallback must let the primary failure propagate")


class _FailingLLM:
    async def stream(
        self, messages: Sequence[Message], tools: Sequence[ToolSpec] = ()
    ) -> AsyncIterator[LLMEvent]:
        raise RuntimeError("provider down")
        yield  # pragma: no cover


class _MidstreamFailingLLM:
    async def stream(
        self, messages: Sequence[Message], tools: Sequence[ToolSpec] = ()
    ) -> AsyncIterator[LLMEvent]:
        yield TextDelta("partial")
        raise RuntimeError("provider down")


async def test_llm_falls_back_before_emitting() -> None:
    wrapper = FallbackLLM(_FailingLLM(), MockLLMClient([text_turn("fallback")]))
    events = [event async for event in wrapper.stream([])]
    assert any(isinstance(e, TextDelta) and e.text == "fallback" for e in events)
    assert wrapper.degraded and len(wrapper.degradations) == 1


async def test_llm_midstream_failure_propagates() -> None:
    wrapper = FallbackLLM(_MidstreamFailingLLM(), MockLLMClient([text_turn("nope")]))
    try:
        _ = [event async for event in wrapper.stream([])]
    except RuntimeError:
        assert not wrapper.degraded
        return
    raise AssertionError("a mid-stream failure must propagate")


async def test_coverage_benchmark_passes() -> None:
    result = await run_fallbacks()
    assert result["coverage"] == 1.0, result["failures"]
    assert result["baseline_coverage"] < result["coverage"]
