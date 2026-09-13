"""Dependency fallback: degrade, record, don't retry (feature 031, RD-1)."""

from __future__ import annotations

from app.adapters.retriever_memory import InMemoryRetriever
from app.core.resilience import FallbackRetriever
from app.core.types import Chunk
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


async def test_coverage_benchmark_passes() -> None:
    result = await run_fallbacks()
    assert result["coverage"] == 1.0, result["failures"]
    assert result["baseline_coverage"] < result["coverage"]
