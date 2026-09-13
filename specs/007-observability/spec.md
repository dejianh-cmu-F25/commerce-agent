# Feature Specification: Observability (Structured Traces)

**Feature Branch**: `007-observability`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add a `Tracer` port and a JSONL adapter that writes structured spans
(turn, LLM call, tool call) to `logs/traces.jsonl` with a `trace_id`, redacted
inputs/outputs, duration, tokens and cost; expose read endpoints for a trace.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every turn is traceable (Priority: P1)

Each turn emits structured spans sharing a `trace_id`: a `turn` span, one `llm`
span per model call, and one `tool` span per tool call. Spans carry timing,
status, and (redacted) inputs/outputs.

**Why this priority**: SL-2 and the OB principles; without traces the harness is a
black box.

**Independent Test**: Run a turn with a mock LLM and a file tracer; assert the
spans written share a `trace_id` and have the expected names/durations.

**Acceptance Scenarios**:

1. **Given** a turn that calls a tool, **When** it completes, **Then** the trace
   contains `turn`, `llm`, and `tool` spans with a shared `trace_id`.
2. **Given** a span with a long input/output, **When** it is written, **Then** the
   value is truncated (redacted, OB-5).

---

### User Story 2 - Tracing is configurable (Priority: P1)

Tracing can be disabled, and the sink is selected by configuration; a bad value
fails loud at load.

**Independent Test**: Load settings with tracing off and assert no spans are
written; assert an unknown sink is rejected.

**Acceptance Scenarios**:

1. **Given** `observability.trace_enabled: false`, **When** a turn runs, **Then**
   nothing is written.
2. **Given** a valid config, **When** the app starts, **Then** the JSONL tracer
   writes to the configured file.

---

### User Story 3 - Traces are readable (Priority: P2)

A trace can be listed and fetched over HTTP for review (WV-5).

**Independent Test**: After a turn, `GET /traces` lists it and
`GET /traces/{trace_id}` returns its spans.

**Acceptance Scenarios**:

1. **Given** a completed turn, **When** `GET /traces` is called, **Then** the
   trace appears with its duration and span count.
2. **Given** a `trace_id`, **When** `GET /traces/{trace_id}` is called, **Then**
   the ordered spans are returned; unknown id → 404.

### Edge Cases

- Tracing disabled: spans are not written and the loop behaves identically.
- The trace file is missing or empty: the API returns an empty list, not an error.
- A malformed line in the file: skipped (never crash the reader).
- Concurrent writes: appended atomically (a lock + flush per span).

## Requirements *(mandatory)*

- **FR-001**: A `Tracer` port MUST define `record(span)`, `list_traces(limit)`,
  and `get_spans(trace_id)`.
- **FR-002**: A JSONL adapter MUST append one JSON object per span to the
  configured file, and read traces back.
- **FR-003**: Each turn MUST share one `trace_id`; spans MUST have `span_id` and
  `parent_id` (the turn span is the root).
- **FR-004**: Spans MUST record `name`, `start_ms`, `end_ms`, `status`, and
  attributes (tokens/cost for `llm`; tool name/status for `tool`).
- **FR-005**: Inputs/outputs MUST be redacted (truncated) before writing (OB-5).
- **FR-006**: Tracing MUST be injectable and optional; a `NullTracer` is used when
  disabled (P5, P8).
- **FR-007**: The web layer MUST expose `GET /traces` and `GET /traces/{trace_id}`
  (404 unknown), and MUST NOT change the chat behavior.
- **FR-008**: Reading MUST tolerate a missing/empty/corrupt file.

### Key Entities

- **Span**: `trace_id`, `span_id`, `parent_id`, `name`, `start_ms`, `end_ms`,
  `status`, `attributes`.
- **TraceSummary**: `trace_id`, `start_ms`, `duration_ms`, `span_count`, `status`.
- **Tracer**: the capability (record, list, get).

## UI Requirements

No browser change; the chat is unchanged. Traces are exposed via the API.

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty / Streaming / Success / Error | As in 003 | Unchanged |

## Web Acceptance

Open `/`, send a message. Then `GET /traces` lists a trace and
`GET /traces/{trace_id}` returns its `turn`/`llm`/`tool` spans.

## Observability

This feature **is** the observability layer: `logs/traces.jsonl`, `trace_id`
across turn/llm/tool, metrics (latency, tokens, cost, tool status), and redacted
inputs/outputs (SL-2, OB-1/2/3/5). The web Trace Viewer (OB-4) is a follow-up.

## Success Criteria *(mandatory)*

- **SC-001**: A tool-using turn writes ≥3 spans (turn, llm, tool) with one
  `trace_id`.
- **SC-002**: `GET /traces` and `GET /traces/{trace_id}` return the trace; unknown
  → 404; a missing file → empty list.
- **SC-003**: Redaction truncates long values.
- **SC-004**: With tracing disabled, no spans are written and behavior is
  unchanged.

## Assumptions

- The trace file is `logs/traces.jsonl` (already in `observability.trace_file`).
- The loop is the instrumentation point; adapters stay dumb.
- A rich Trace Viewer UI (OB-4) is a follow-up feature.

## Real-World Coverage

- **Input distribution**: spans emitted by the loop.
- **Data quality**: one JSON span per line; attribute values are redacted to a max
  length; a corrupt line is tolerated.
- **Edge & failure modes**: a tracer failure never changes the turn; reads tolerate
  a missing/empty file.
- **Scale envelope**: a growing JSONL file; rotation is out of scope (gap).
- **Degradation**: a no-op tracer is used when tracing is disabled.
- **Change evidence**: traces recorded (`specs/RESULTS.md`).
