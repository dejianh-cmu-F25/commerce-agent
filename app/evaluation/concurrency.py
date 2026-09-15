"""Bounded async fan-out for evaluations (feature 046).

The evaluation loops used to run one case at a time, so wall time was the sum of
every model call. Cases are independent (each builds its own session), so they can
run concurrently behind a semaphore.

Two properties the callers rely on:

- **Nothing is lost**: a case that raises is returned as the exception, and the
  rest of the batch still completes. One flaky case never voids a run.
- **Ordered results**: results come back in the input order, so scoring and the
  pass^k grid stay index-aligned with the case list regardless of completion order.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar

T = TypeVar("T")
R = TypeVar("R")

OnDone = Callable[[int, int, "R | BaseException"], Awaitable[None] | None]


async def run_bounded(
    items: Sequence[T],
    worker: Callable[[T, int], Awaitable[R]],
    *,
    concurrency: int,
    on_done: OnDone[R] | None = None,
) -> list[R | BaseException]:
    """Run ``worker(item, index)`` for every item, at most ``concurrency`` at once.

    ``on_done(completed, total, result)`` is called once per finished item with a
    monotonically increasing ``completed`` count, so a caller can report progress
    without racing on its own counter.
    """
    if concurrency < 1:
        raise ValueError("concurrency must be >= 1")
    semaphore = asyncio.Semaphore(concurrency)
    results: list[R | BaseException] = [None] * len(items)  # type: ignore[list-item]
    completed = 0

    async def run_one(index: int, item: T) -> None:
        nonlocal completed
        async with semaphore:
            try:
                result: R | BaseException = await worker(item, index)
            except asyncio.CancelledError:
                raise
            except BaseException as exc:  # noqa: BLE001 - one case must not void the run
                result = exc
        results[index] = result
        completed += 1
        if on_done is not None:
            outcome = on_done(completed, len(items), result)
            if outcome is not None:
                await outcome

    await asyncio.gather(*(run_one(index, item) for index, item in enumerate(items)))
    return results
