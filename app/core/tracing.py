"""Span timing helper (constitution SL-2).

The loop measures durations and builds spans; the tracer only serializes. This
keeps timing where the work happens and the adapter dumb.
"""

from __future__ import annotations

import time
from types import TracebackType
from uuid import uuid4

from app.core.types import Span
from app.ports.tracer import Tracer


def now_ms() -> float:
    return time.time() * 1000.0


class SpanTimer:
    """Times a block and records a span on exit (no-op when ``tracer`` is None)."""

    def __init__(
        self,
        tracer: Tracer | None,
        name: str,
        trace_id: str,
        parent_id: str | None = None,
    ) -> None:
        self._tracer = tracer
        self.name = name
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.span_id = uuid4().hex[:16]
        self.attributes: dict = {}
        self.status = "ok"
        self.start_ms = 0.0

    def __enter__(self) -> SpanTimer:
        self.start_ms = now_ms()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if self._tracer is not None:
            self._tracer.record(
                Span(
                    trace_id=self.trace_id,
                    span_id=self.span_id,
                    parent_id=self.parent_id,
                    name=self.name,
                    start_ms=self.start_ms,
                    end_ms=now_ms(),
                    status="error" if exc_type else self.status,
                    attributes=dict(self.attributes),
                )
            )
        return False
