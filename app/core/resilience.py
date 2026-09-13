"""Graceful fallback for external dependencies (feature 031, RD-1).

Every external dependency has a deterministic, config-gated fallback and degrades
**observably** rather than failing silently. :class:`FallbackRetriever` serves a
secondary on a primary failure, records a :class:`Degradation`, and does not
retry a failed primary (fast, deterministic). Stdlib only.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Sequence
from dataclasses import dataclass
from typing import Protocol

from app.core.types import Chunk, LLMEvent, Message, ToolSpec
from app.ports.llm import LLMClient


@dataclass(frozen=True)
class Degradation:
    """One recorded dependency failure: what failed, what served instead, why."""

    component: str
    primary: str
    fallback: str
    reason: str


class _Retriever(Protocol):
    def add(self, chunks: list[Chunk]) -> None: ...

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]: ...


class FallbackRetriever:
    """A retriever that falls back to a secondary when the primary fails.

    ``enabled=False`` disables the fallback: the primary's failure propagates, so
    the fallback is a configuration choice, not a hidden surprise.
    """

    def __init__(
        self,
        primary: _Retriever,
        secondary: _Retriever,
        *,
        component: str = "retriever",
        enabled: bool = True,
    ) -> None:
        self._primary = primary
        self._secondary = secondary
        self._component = component
        self._enabled = enabled
        self._degraded = False
        self._degradations: list[Degradation] = []

    def add(self, chunks: list[Chunk]) -> None:
        self._primary.add(chunks)
        self._secondary.add(chunks)

    def retrieve(self, query: str, k: int = 3) -> list[Chunk]:
        if self._degraded:
            return self._secondary.retrieve(query, k)  # already down: don't retry
        if not self._enabled:
            return self._primary.retrieve(query, k)  # disabled: let it fail loud
        try:
            return self._primary.retrieve(query, k)
        except Exception as exc:  # degrade, but record it (RD-1)
            self._degraded = True
            self._degradations.append(
                Degradation(
                    component=self._component,
                    primary=type(self._primary).__name__,
                    fallback=type(self._secondary).__name__,
                    reason=str(exc),
                )
            )
            return self._secondary.retrieve(query, k)

    @property
    def degraded(self) -> bool:
        return self._degraded

    @property
    def degradations(self) -> list[Degradation]:
        return list(self._degradations)


class FallbackLLM:
    """Fall back to a secondary LLM when the primary fails **before emitting**.

    Once a delta is sent it cannot be un-sent, so a mid-stream failure propagates
    rather than silently switching providers. A failed primary is not retried.
    """

    def __init__(
        self,
        primary: LLMClient,
        secondary: LLMClient,
        *,
        component: str = "llm",
        enabled: bool = True,
    ) -> None:
        self._primary = primary
        self._secondary = secondary
        self._component = component
        self._enabled = enabled
        self._degraded = False
        self._degradations: list[Degradation] = []

    async def stream(
        self, messages: Sequence[Message], tools: Sequence[ToolSpec] = ()
    ) -> AsyncIterator[LLMEvent]:
        if self._degraded:
            async for event in self._secondary.stream(messages, tools):
                yield event
            return
        if not self._enabled:
            async for event in self._primary.stream(messages, tools):
                yield event
            return

        emitted = False
        try:
            async for event in self._primary.stream(messages, tools):
                emitted = True
                yield event
            return
        except Exception as exc:
            if emitted:
                raise  # a partial response cannot be retried
            self._degraded = True
            self._degradations.append(
                Degradation(
                    component=self._component,
                    primary=type(self._primary).__name__,
                    fallback=type(self._secondary).__name__,
                    reason=str(exc),
                )
            )
        async for event in self._secondary.stream(messages, tools):
            yield event

    @property
    def degraded(self) -> bool:
        return self._degraded

    @property
    def degradations(self) -> list[Degradation]:
        return list(self._degradations)
