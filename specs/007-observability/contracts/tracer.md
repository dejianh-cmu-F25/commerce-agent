# Contract: Tracer

## Port (`app/ports/tracer.py`)

```python
class Tracer(Protocol):
    def record(self, span: Span) -> None: ...
    def list_traces(self, limit: int = 50) -> list[TraceSummary]: ...
    def get_spans(self, trace_id: str) -> list[Span]: ...
```

- `record` appends one span; it must not raise into the loop (tracing is
  best-effort).
- `list_traces` returns the most recent traces, newest first.
- `get_spans` returns the spans of one trace ordered by `start_ms`.
- The port does not import the web layer.

## Providers

| Provider | Module | Notes |
| --- | --- | --- |
| `JsonlTracer` | `app/adapters/tracer_jsonl.py` | append-only JSONL; tolerant reads |
| `NullTracer` | `app/adapters/tracer_jsonl.py` | no-op; used when disabled |

## Instrumentation (`app/core/loop.py`)

`Agent` takes an optional `tracer: Tracer | None`. Per turn:

1. `trace_id = uuid4().hex`; open a `turn` span (root).
2. Around each model call: an `llm` span (parent `turn`).
3. Around each tool call: a `tool` span (parent `turn`).

Span attributes are redacted (truncated) before `record`.

## HTTP (web surface, WV-5)

- `GET /traces?limit=50` → `{"traces": [TraceSummary, …]}`
- `GET /traces/{trace_id}` → `{"trace_id": "…", "spans": [Span, …]}` or 404
- A missing/empty trace file yields an empty list (never an error).
