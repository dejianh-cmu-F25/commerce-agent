# Research: Observability

## D1. Port shape

**Decision**: `Tracer` with `record(span)`, `list_traces(limit)`, `get_spans(trace_id)`.
A `Span` dataclass lives in `app/core/types.py`.

**Rationale**: One capability for write + read; the web reads through the same
seam it writes through.

**Alternatives considered**: OpenTelemetry (rejected: heavy dependency for a
demo); a write-only tracer with a separate reader (rejected: two seams).

## D2. Span timing

**Decision**: the loop measures durations with `time.perf_counter()` and builds
`Span`s; the tracer only serializes. A small `SpanTimer` helper in the tracer
module reduces boilerplate.

**Rationale**: Timing belongs where the work happens; the adapter stays dumb and
testable.

## D3. Storage format

**Decision**: JSONL, one span per line, append + flush, guarded by a
`threading.Lock`. Reads tolerate missing/empty/corrupt lines.

**Rationale**: Append-only, greppable, no schema migration; SL-2 names
`logs/traces.jsonl`.

## D4. Redaction

**Decision**: truncate attribute strings to a configured length (default 500) and
record the original length; never write full prompts/tool outputs.

**Rationale**: OB-5; keeps the file small and avoids leaking user data.

## D5. Disabled tracing

**Decision**: `NullTracer` when `observability.trace_enabled` is false; the loop
takes an optional tracer and behaves identically without one.

**Rationale**: P8 (keyless/minimal) and P5 (injected).

## D6. Read API

**Decision**: `GET /traces?limit=` returns summaries; `GET /traces/{trace_id}`
returns spans ordered by `start_ms`. The reader is the same `JsonlTracer`.

**Rationale**: WV-5 web entry; no separate service.
