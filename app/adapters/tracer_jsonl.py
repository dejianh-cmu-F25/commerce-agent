"""JSONL tracer (Service Provider for :class:`app.ports.tracer.Tracer`).

Appends one span per line to ``observability.trace_file`` (SL-2). Reads are
tolerant: a missing, empty, or partially corrupt file never raises.
"""

from __future__ import annotations

import json
import threading
from dataclasses import asdict
from pathlib import Path
from typing import Any

from app.core.types import Span, TraceSummary


class NullTracer:
    """A no-op tracer used when tracing is disabled (P8)."""

    def record(self, span: Span) -> None:
        return None

    def list_traces(self, limit: int = 50) -> list[TraceSummary]:
        return []

    def get_spans(self, trace_id: str) -> list[Span]:
        return []

    def recent_spans(self, limit: int = 2000) -> list[Span]:
        return []


class JsonlTracer:
    def __init__(self, path: str, max_attr_len: int = 500) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._max_attr_len = max_attr_len
        self._lock = threading.Lock()

    def _redact(self, value: Any) -> Any:
        if isinstance(value, str) and len(value) > self._max_attr_len:
            return value[: self._max_attr_len] + "…"
        return value

    def record(self, span: Span) -> None:
        safe = Span(
            trace_id=span.trace_id,
            span_id=span.span_id,
            parent_id=span.parent_id,
            name=span.name,
            start_ms=span.start_ms,
            end_ms=span.end_ms,
            status=span.status,
            attributes={k: self._redact(v) for k, v in span.attributes.items()},
        )
        line = json.dumps(asdict(safe), ensure_ascii=False)
        with self._lock:
            with self._path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")

    def _read(self) -> list[Span]:
        if not self._path.exists():
            return []
        spans: list[Span] = []
        for raw in self._path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line:
                continue
            try:
                spans.append(Span(**json.loads(line)))
            except (json.JSONDecodeError, TypeError):
                continue  # tolerate a corrupt line
        return spans

    def list_traces(self, limit: int = 50) -> list[TraceSummary]:
        groups: dict[str, list[Span]] = {}
        for span in self._read():
            groups.setdefault(span.trace_id, []).append(span)
        summaries = [
            TraceSummary(
                trace_id=trace_id,
                start_ms=min(s.start_ms for s in group),
                duration_ms=round(max(s.end_ms for s in group) - min(s.start_ms for s in group), 2),
                span_count=len(group),
                status="error" if any(s.status == "error" for s in group) else "ok",
            )
            for trace_id, group in groups.items()
        ]
        summaries.sort(key=lambda summary: summary.start_ms, reverse=True)
        return summaries[:limit]

    def get_spans(self, trace_id: str) -> list[Span]:
        return sorted(
            (span for span in self._read() if span.trace_id == trace_id),
            key=lambda span: span.start_ms,
        )

    def recent_spans(self, limit: int = 2000) -> list[Span]:
        return self._read()[-max(1, limit) :]
