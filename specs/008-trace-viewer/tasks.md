# Tasks: Web Trace Viewer

**Feature**: `008-trace-viewer` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Helpers

- [x] T001 `frontend/src/lib/traces.ts`: types, `listTraces`, `getTrace`, `formatDuration`, `buildSpanTree`
- [x] T002 [P] `frontend/src/lib/traces.test.ts`: vitest for `formatDuration` and `buildSpanTree`

## Phase 2 — UI

- [x] T003 `components/app/trace-viewer.tsx`: list (id, duration, spans, status) + Refresh
- [x] T004 `trace-viewer.tsx`: detail timeline (indent by parent, attributes)
- [x] T005 `trace-viewer.tsx`: loading / empty / error states
- [x] T006 `App.tsx`: Chat/Traces toggle; render the viewer; preserve the chat

## Phase 3 — Verify & deliver

- [x] T007 `scripts/ci.sh --fast`
- [x] T008 Browser checkpoint: list + timeline + toggle preserves chat; screenshot
- [x] T009 Update `docs/checkpoints.md`; commit and open the PR

## Dependencies

- T001 before T003/T004.
- T003/T004/T005 before T006.
- T007–T009 last.
