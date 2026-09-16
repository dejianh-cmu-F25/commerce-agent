"""Bounded fan-out and retry: the properties concurrent evaluations rely on."""

from __future__ import annotations

import asyncio

import pytest

from app.core.retry import retry_async
from app.evaluation.concurrency import run_bounded


async def test_results_keep_input_order_despite_completion_order():
    async def slow_then_fast(index: int, _i: int) -> int:
        await asyncio.sleep((10 - index) / 100)  # later items finish first
        return index

    results = await run_bounded(list(range(10)), slow_then_fast, concurrency=10)
    assert results == list(range(10))


async def test_one_failure_does_not_void_the_batch():
    async def flaky(index: int, _i: int) -> int:
        if index == 3:
            raise RuntimeError("boom")
        return index

    results = await run_bounded(list(range(6)), flaky, concurrency=6)
    assert results[3].__class__ is RuntimeError
    assert [r for i, r in enumerate(results) if i != 3] == [0, 1, 2, 4, 5]


async def test_never_exceeds_the_concurrency_ceiling():
    in_flight = 0
    peak = 0

    async def worker(_item: int, _i: int) -> None:
        nonlocal in_flight, peak
        in_flight += 1
        peak = max(peak, in_flight)
        await asyncio.sleep(0.01)
        in_flight -= 1

    await run_bounded(list(range(40)), worker, concurrency=4)
    assert peak <= 4


async def test_on_done_counts_are_monotonic_and_complete():
    seen: list[int] = []

    async def worker(item: int, _i: int) -> int:
        await asyncio.sleep(0.001)
        return item

    await run_bounded(
        list(range(20)),
        worker,
        concurrency=5,
        on_done=lambda completed, total, _result: seen.append(completed),
    )
    assert seen == list(range(1, 21))


async def test_rejects_invalid_concurrency():
    with pytest.raises(ValueError):
        await run_bounded([], lambda _item, _i: asyncio.sleep(0), concurrency=0)


async def test_retry_succeeds_after_transient_failures():
    attempts = 0

    async def flaky() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise TimeoutError("transient")
        return "ok"

    assert await retry_async(flaky, attempts=5, base_delay=0) == "ok"
    assert attempts == 3


async def test_retry_gives_up_and_raises_the_last_error():
    attempts = 0

    async def always_fails() -> None:
        nonlocal attempts
        attempts += 1
        raise TimeoutError("still down")

    with pytest.raises(TimeoutError):
        await retry_async(always_fails, attempts=3, base_delay=0)
    assert attempts == 3


async def test_non_retryable_error_raises_immediately():
    attempts = 0

    async def bad_request() -> None:
        nonlocal attempts
        attempts += 1
        raise ValueError("400 bad request")

    with pytest.raises(ValueError):
        await retry_async(bad_request, attempts=4, base_delay=0)
    assert attempts == 1


async def test_retry_honours_a_status_code_marker():
    attempts = 0

    class RateLimited(Exception):
        status_code = 429

    async def limited() -> str:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RateLimited()
        return "ok"

    assert await retry_async(limited, attempts=3, base_delay=0) == "ok"
    assert attempts == 2
