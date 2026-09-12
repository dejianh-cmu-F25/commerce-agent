"""Observability capability: Service Definition (constitution SL-2, OB).

A tracer records structured spans (turn, LLM call, tool call) sharing a
``trace_id``. Providers live in ``app/adapters`` and are selected by
configuration (PB-1). Reading uses the same seam so the web layer has one
dependency.
"""

from __future__ import annotations

from typing import Protocol

from app.core.types import Span, TraceSummary


class Tracer(Protocol):
    def record(self, span: Span) -> None:
        """Append one span. Best-effort: never raise into the caller."""
        ...

    def list_traces(self, limit: int = 50) -> list[TraceSummary]:
        """Return recent traces, newest first."""
        ...

    def get_spans(self, trace_id: str) -> list[Span]:
        """Return the spans of one trace, ordered by start time."""
        ...

    def recent_spans(self, limit: int = 2000) -> list[Span]:
        """Return up to ``limit`` most recent spans, for aggregation (OB-3)."""
        ...
