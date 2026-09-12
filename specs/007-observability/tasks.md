# Tasks: Observability (Structured Traces)

**Feature**: `007-observability` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Port + types + config

- [x] T001 Add `Span` (and `TraceSummary`) to `app/core/types.py`
- [x] T002 Add `Tracer` protocol in `app/ports/tracer.py`
- [x] T003 Add `observability.trace_max_attr_len` to settings + `config/settings.yaml`

## Phase 2 — Adapter

- [x] T004 `JsonlTracer` (record/list/get, tolerant reads) + `NullTracer` in `app/adapters/tracer_jsonl.py`
- [x] T005 `build_tracer(settings)` in `web/main.py`

## Phase 3 — Instrumentation

- [x] T006 `Agent` takes an optional `tracer`; emit `turn` span
- [x] T007 Emit `llm` spans (tokens, cost) and `tool` spans (name, status, redacted io)
- [x] T008 Redaction helper (truncate) with a configurable length

## Phase 4 — API + tests

- [x] T009 `GET /traces` and `GET /traces/{trace_id}` (404 unknown)
- [x] T010 [P] Unit: `tests/unit/test_tracer_jsonl.py`
- [x] T011 [P] Integration: instrumented turn writes turn/llm/tool spans; API 200/404
- [x] T012 Update `scripts/spec_review.py` SL-2/OB to detect the tracer (AUTO)

## Phase 5 — Verify & deliver

- [x] T013 `scripts/ci.sh --fast`
- [x] T014 Browser checkpoint + `checkpoint.png` + `checkpoint.md`
- [x] T015 Update `docs/architecture.md`; commit and open the PR

## Dependencies

- T001/T002 before T004/T006.
- T004/T005 before T006.
- T006/T007 before T009/T011.
- T010–T012 after T004/T006.
- T013–T015 last.
