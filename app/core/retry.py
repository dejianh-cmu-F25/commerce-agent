"""Retry with exponential backoff and jitter (feature 046).

Concurrent evaluation puts real load on the provider and on Shopify, where a
transient 429 must not be scored as a wrong answer. Retries are limited and
jittered so a burst cannot synchronise into a thundering herd.
"""

from __future__ import annotations

import asyncio
import random
from collections.abc import Awaitable, Callable, Iterable
from typing import TypeVar

T = TypeVar("T")

# HTTP statuses worth retrying: rate limiting and transient server errors.
RETRYABLE_STATUS = frozenset({408, 409, 425, 429, 500, 502, 503, 504})


class RetryableError(Exception):
    """Marker for an error a caller has decided is worth retrying."""


def is_retryable(exc: BaseException, extra: Iterable[type[BaseException]] = ()) -> bool:
    """True for rate limits, timeouts and connection errors."""
    if isinstance(exc, (asyncio.TimeoutError, RetryableError)) or isinstance(exc, tuple(extra)):
        return True
    if isinstance(exc, (TimeoutError, ConnectionError)):
        return True
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if isinstance(status, int) and status in RETRYABLE_STATUS:
        return True
    # openai's APIConnectionError / APITimeoutError subclass APIError.
    return type(exc).__name__ in {"APIConnectionError", "APITimeoutError", "ConnectError"}


async def retry_async(
    operation: Callable[[], Awaitable[T]],
    *,
    attempts: int = 4,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    extra_retryable: Iterable[type[BaseException]] = (),
    on_retry: Callable[[int, float, BaseException], None] | None = None,
) -> T:
    """Run ``operation`` until it succeeds, retrying transient failures.

    Raises the last error when every attempt is exhausted.
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")
    last: BaseException | None = None
    for attempt in range(1, attempts + 1):
        try:
            return await operation()
        except asyncio.CancelledError:
            raise
        except BaseException as exc:  # noqa: BLE001 - re-raised below when not retryable
            if not is_retryable(exc, extra_retryable) or attempt == attempts:
                raise
            last = exc
            delay = min(max_delay, base_delay * 2 ** (attempt - 1))
            delay += random.uniform(0, delay / 2)  # full jitter
            if on_retry is not None:
                on_retry(attempt, delay, exc)
            await asyncio.sleep(delay)
    assert last is not None  # pragma: no cover - loop always returns or raises
    raise last
