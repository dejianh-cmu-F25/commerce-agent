# Tasks: Metrics Dashboard

**Feature**: `017-metrics-dashboard` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Metrics core

- [x] T001 `app/core/metrics.py`: `SpanStats`, `MetricsSummary`, `summarize`
- [x] T002 `Tracer.recent_spans(limit)` in `app/ports/tracer.py` + `tracer_jsonl.py`
- [x] T003 `app/core/loop.py`: record `cache_hit_tokens` / `cache_miss_tokens` on the LLM span

## Phase 2 — Web + frontend

- [x] T004 `web/main.py`: `GET /metrics`
- [x] T005 `lib/metrics.ts` + `components/app/metrics-view.tsx`
- [x] T006 `App.tsx`: Metrics tab

## Phase 3 — Tests + verify

- [x] T007 [P] Unit: `tests/unit/test_metrics.py`
- [x] T008 [P] Integration: `tests/integration/test_metrics_api.py`
- [x] T009 `docs/architecture.md`; Agent Note
- [x] T010 `scripts/ci.sh --fast`; browser checkpoint; review; PR

## Dependencies

- T001/T002/T003 before T004/T007/T008.
- T004 before T005/T008.
- T005/T006 before T010.
