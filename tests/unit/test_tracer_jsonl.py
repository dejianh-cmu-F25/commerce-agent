"""Unit tests for the JSONL tracer (feature 007)."""

from __future__ import annotations

from pathlib import Path

from app.adapters.tracer_jsonl import JsonlTracer, NullTracer
from app.core.types import Span


def _span(*, trace_id: str = "t1", name: str = "turn", **attributes: object) -> Span:
    return Span(
        trace_id=trace_id,
        span_id="s1",
        name=name,
        start_ms=1.0,
        end_ms=2.0,
        status="ok",
        attributes=dict(attributes),
    )


def test_record_and_read(tmp_path: Path):
    tracer = JsonlTracer(str(tmp_path / "traces.jsonl"))
    tracer.record(_span(name="turn"))
    tracer.record(_span(name="llm"))

    assert [s.name for s in tracer.get_spans("t1")] == ["turn", "llm"]
    summaries = tracer.list_traces()
    assert len(summaries) == 1
    assert summaries[0].span_count == 2
    assert summaries[0].status == "ok"


def test_redaction_truncates_long_values(tmp_path: Path):
    tracer = JsonlTracer(str(tmp_path / "traces.jsonl"), max_attr_len=10)
    tracer.record(_span(output="x" * 100))
    span = tracer.get_spans("t1")[0]
    assert span.attributes["output"] == "x" * 10 + "…"


def test_tolerates_missing_file_and_corrupt_lines(tmp_path: Path):
    path = tmp_path / "traces.jsonl"
    tracer = JsonlTracer(str(path))
    assert tracer.list_traces() == []

    path.write_text(
        "not json\n"
        '{"trace_id":"t1","span_id":"s","name":"turn","start_ms":1,"end_ms":2,'
        '"parent_id":null,"status":"ok","attributes":{}}\n'
    )
    assert len(tracer.get_spans("t1")) == 1


def test_null_tracer_is_a_noop():
    tracer = NullTracer()
    tracer.record(_span())
    assert tracer.list_traces() == []
    assert tracer.get_spans("t1") == []
