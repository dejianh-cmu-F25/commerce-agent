# Implementation Plan: Metrics Dashboard

**Branch**: `017-metrics-dashboard` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/017-metrics-dashboard/spec.md`

## Summary

Add a bounded `recent_spans` read to the `Tracer` port, a pure
`app/core/metrics.py` summarizer (latency by span type, tokens incl. cache, cost,
tool success/failure), a `GET /metrics` endpoint, and a Metrics tab. Record
cache-hit/miss tokens on the loop's LLM span. Keyless; reads the trace file. No
new dependency.

## Technical Context

**Language/Version**: Python 3.13; React 19 + TypeScript (frontend)

**Primary Dependencies**: none new

**Storage**: reads `observability.trace_file` (JSONL); no writes

**Testing**: `pytest` (unit: `summarize`; integration: `GET /metrics` after a
mock turn)

**Performance Goals**: aggregate the last N spans in one read

**Constraints**: keyless, read-only; tolerant of a missing/corrupt file (RD-1)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| PB-2 capability seam | `Tracer` gains a bounded read; two providers | PASS |
| SL-2 / OB-1 | reads the same spans; LLM span gains cache tokens | PASS |
| OB-3 | latency, tokens, cost, cache hit, tool success/failure surfaced | PASS |
| OB-5 | reads redacted attributes (the tracer truncates on write) | PASS |
| P3 / P8 | read-only; keyless | PASS |
| RD-1 | missing/corrupt trace file degrades to empty | PASS |
| WV-3 / WV-6 | new view with all states | PASS |
| HR-11 | extension point documented | PASS |

## Project Structure

```text
app/
├── core/metrics.py         # NEW: SpanStats, MetricsSummary, summarize
├── core/loop.py            # LLM span: cache_hit_tokens/cache_miss_tokens
├── ports/tracer.py         # + recent_spans(limit)
└── adapters/tracer_jsonl.py# implement recent_spans
web/main.py                 # GET /metrics
frontend/src/
├── lib/metrics.ts                     # NEW
├── components/app/metrics-view.tsx    # NEW
└── App.tsx                            # Metrics tab
tests/unit/test_metrics.py
tests/integration/test_metrics_api.py
docs/architecture.md; Agent Note
```

## Design decisions

- **Bounded, single read.** `recent_spans(limit)` returns the last N spans from
  the append-only file, so aggregation is one read rather than per-trace reads.
- **Pure summarizer.** `summarize(spans)` is a pure function over `Span`s,
  unit-testable without I/O; the endpoint is a thin wrapper.
- **Window vs all-time.** The endpoint reports the window's cost from spans and
  the all-time budget position from the meter, labelled distinctly.

## Complexity Tracking

> No constitution violations. One small loop change (LLM span attributes) noted
> in `docs/architecture.md`; no new dependency.
