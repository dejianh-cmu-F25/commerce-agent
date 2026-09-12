# Tasks: Browser Resume

**Feature**: `006-browser-resume` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Helpers

- [x] T001 `frontend/src/lib/resume.ts`: `rehydrateMessages` mapping
- [x] T002 [P] `frontend/src/lib/resume.test.ts`: vitest for the mapping
- [x] T003 `frontend/src/lib/transport.ts`: persist/read/clear the session id; `getSessionId`, `reset`

## Phase 2 — UI

- [x] T004 `App.tsx`: rehydrate on mount (200 / 404 / error paths)
- [x] T005 `App.tsx`: New chat action (clear storage, reset transport, clear messages)
- [x] T006 `App.tsx`: Resuming state (composer available, no error UI)

## Phase 3 — Verify & deliver

- [x] T007 `scripts/ci.sh --fast` (lint/typecheck/test/build + python gates)
- [x] T008 Browser checkpoint: reload resumes; New chat clears; stale id → empty; screenshot
- [x] T009 Update `docs/checkpoints.md`; commit and open the PR

## Dependencies

- T001/T003 before T004.
- T004 before T005/T006.
- T007–T009 last.
