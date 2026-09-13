"""Graceful fallback for external dependencies (feature 031, RD-1).

Every external dependency has a deterministic, config-gated fallback and degrades
**observably** rather than failing silently. :class:`FallbackRetriever` serves a
secondary on a primary failure, records a :class:`Degradation`, and does not
retry a failed primary (fast, deterministic). Stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.core.types import Chunk


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
