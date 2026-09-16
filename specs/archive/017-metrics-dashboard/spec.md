# Feature Specification: Metrics Dashboard

**Feature Branch**: `017-metrics-dashboard`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Surface OB-3 metrics in a web Metrics view, aggregated from the tracer:
latency by span type, tokens (prompt/completion/cache), cost, and tool
success/failure, plus the budget. Keyless; reads the existing traces.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See harness metrics at a glance (Priority: P1)

An operator opens the Metrics view and sees, over the recent traces: how many
spans, average and p95 latency per span type, token totals (including cache
hits), cost, tool success/failure counts, and the budget position.

**Why this priority**: OB-3 lists these metrics; today they are only visible
per-span in the Trace Viewer. A dashboard makes harness health legible.

**Independent Test**: Generate a turn, call the metrics endpoint, and assert it
reports the turn/llm/tool spans, tokens, cost, and tool counts.

**Acceptance Scenarios**:

1. **Given** recent traces, **When** the Metrics view opens, **Then** it shows
   latency per span type, token totals, cost, and tool success/failure.
2. **Given** the budget, **When** metrics load, **Then** spent/limit/remaining
   are shown alongside the window's cost.
3. **Given** no traces, **When** the view opens, **Then** an empty state explains
   there is no activity yet.

---

### User Story 2 - Keyless and read-only (Priority: P1)

Metrics need no key, spend nothing, and never change state.

**Independent Test**: Call the endpoint with no key configured; assert it returns
and that no provider call occurs.

**Acceptance Scenarios**:

1. **Given** no API key, **When** metrics load, **Then** they aggregate the trace
   file without any model call.
2. **Given** a corrupt or missing trace file, **When** metrics load, **Then** the
   view shows zeros/empty rather than failing (RD-1).

---

### Edge Cases

- **No traces**: empty state; the endpoint returns zeroed metrics.
- **Trace file read error**: tolerated; metrics degrade to empty (RD-1).
- **Large window**: the endpoint caps the spans it aggregates (`limit`).
- **Tracing disabled**: the null tracer yields no spans; the view shows the empty
  state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The tracer capability MUST expose a bounded read of recent spans
  (`recent_spans(limit)`) for aggregation.
- **FR-002**: A pure function MUST summarize spans into per-span latency stats
  (count, errors, average, p95), token totals (prompt, completion, cache hit and
  miss), cost, and tool success/failure counts.
- **FR-003**: The agent loop's LLM span MUST record cache-hit and cache-miss
  tokens (so cache metrics are available).
- **FR-004**: The web MUST expose `GET /metrics` returning the summary, the
  window's span count, and the budget position.
- **FR-005**: The UI MUST provide a Metrics view with empty, loading, success, and
  error states (WV-6).
- **FR-006**: Metrics MUST be keyless and read-only: no provider call, no state
  change (P8, P3).

### Key Entities

- **SpanStats**: per span name — count, error count, average ms, p95 ms.
- **MetricsSummary**: the span stats list plus token totals, cost, and tool
  success/failure counts.

## UI Requirements

A new **Metrics** view (a tab beside Chat / Traces / Merchant / Memory /
Scenarios).

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | No spans in the window | A line saying there is no activity yet |
| Loading | Metrics are being fetched | A "Loading…" line |
| Success | Metrics loaded | Latency table per span type, token/cost tiles, tool success/failure, budget bar |
| Error | The fetch fails | An inline error with Retry |
| Disabled | Not applicable (read-only) | — |

### Accessibility

- [ ] Tabs and Refresh are keyboard-operable with a visible focus ring.
- [ ] Metrics update announced politely (`aria-live`).
- [ ] Numbers use tabular figures; values are conveyed by text, not color alone.
- [ ] Motion respects `prefers-reduced-motion`.

### Responsive & Theme

- [ ] Tiles wrap; tables scroll or wrap inside their card with no page-level horizontal scroll from 375px up.
- [ ] Theme follows `prefers-color-scheme`.

## Web Acceptance

- The header exposes a **Metrics** tab; selecting it shows latency by span type,
  tokens, cost, tool success/failure, and the budget.
- After a chat turn, the Metrics view reflects the new turn/llm/tool spans.

## Observability

- This feature is observability: it reads the same `logs/traces.jsonl` spans the
  Trace Viewer renders, and adds cache-hit tokens to the LLM span (OB-1, OB-3,
  OB-5).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After a turn, `GET /metrics` reports the turn/llm/tool spans with
  non-zero counts and the turn's tokens/cost.
- **SC-002**: Metrics require no key and make no provider call.
- **SC-003**: A missing trace file yields an empty state, not an error.
- **SC-004**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes with the feature enabled.

## Assumptions

- The trace file is the metrics source; a dedicated metrics store is out of scope.
- The aggregation window is the most recent N spans (default 2000); historical
  retention is out of scope.
- Cost comes from the LLM spans (per window); the budget meter remains the
  authoritative all-time spend (HR-12).

## Real-World Coverage

- **Input distribution**: trace spans from the trace file.
- **Data quality**: aggregates redacted span attributes; a missing/corrupt file
  degrades to empty.
- **Edge & failure modes**: no spans -> empty state; a fetch error -> inline error.
- **Scale envelope**: a bounded window (default 2000 spans); the system envelope is measured in `docs/scale.md`.
- **Degradation**: read-only; no provider needed.
- **Change evidence**: metrics exist (`specs/change-log.json` #22).
