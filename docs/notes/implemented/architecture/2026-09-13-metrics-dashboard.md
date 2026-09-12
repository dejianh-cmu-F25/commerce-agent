# Agent Note: Metrics are aggregated from spans, not a second store

Status: implemented (2026-09-13) — feature `017-metrics-dashboard`

## Problem

OB-3 lists latency, tokens, cost, cache hit, and tool success/failure as
first-class metrics, but they were only visible per-span in the Trace Viewer.
Surfacing them raised two questions:

1. **Where do metrics come from?** A dedicated metrics store would duplicate the
   tracer and could disagree with it.
2. **How does the web read them efficiently?** The `Tracer` port exposed only
   `list_traces` and `get_spans(trace_id)`, so aggregating N traces would re-read
   the trace file N times.

## Alternatives considered

- **A separate metrics store (Prometheus/StatsD).** Standard for production, but a
  new dependency and a second source of truth for a keyless demo. Rejected.
- **Aggregate by iterating `list_traces` + `get_spans` per trace.** No port
  change, but O(traces) file reads per request. Rejected: wasteful and easy to
  fix with one bounded read.
- **Compute metrics inside the loop and persist counters.** Spreads metric logic
  into the hot path and needs its own storage. Rejected.
- **A full time-series/range UI.** More powerful, but out of scope; a window over
  recent spans answers the question.

## Decision

- **Spans are the single source of truth.** `app/core/metrics.summarize(spans)` is
  a pure function; `GET /metrics` is a thin wrapper over the tracer.
- **The tracer gains one bounded read.** `recent_spans(limit)` returns the last N
  spans from the append-only file in a single read, so aggregation is cheap.
- **The LLM span records cache hit/miss tokens**, completing OB-3's cache metric
  at the point the data already exists (the `Usage` event).
- **Window vs all-time are labelled distinctly**: the endpoint reports the
  window's cost from spans and the all-time budget position from the meter.

## Consequences

- Adding a metric is: emit a span attribute, then aggregate it in
  `app/core/metrics.py` (HR-11) — no new store, no schema.
- Metrics reflect only what spans recorded; anything not on a span is invisible
  until an attribute is added.
- The window is bounded (default 2000 spans); long-range retention and
  time-series are out of scope.
