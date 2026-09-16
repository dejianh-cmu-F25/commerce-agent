# Tasks: Scenario Runner

**Feature**: `016-scenario-runner` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Shared runner

- [x] T001 `evals/runner.py`: `ScenarioResult` + `run_scenarios` (moved from `run.py`)
- [x] T002 `evals/run.py`: thin CLI over the runner (same output/exit code)
- [x] T003 Keep `run_all` for the existing eval test (or update the test)

## Phase 2 — Web endpoints

- [x] T004 `web/main.py`: `GET /scenarios`, `POST /scenarios/run`

## Phase 3 — Frontend

- [x] T005 `lib/scenarios.ts` (types + client)
- [x] T006 `components/app/scenario-runner.tsx` (states, run, results)
- [x] T007 `App.tsx`: Scenarios tab; responsive header wrap

## Phase 4 — Tests + verify

- [x] T008 [P] Integration: `tests/integration/test_scenarios_api.py`
- [x] T009 `docs/architecture.md`; Agent Note
- [x] T010 `scripts/ci.sh --fast`; browser checkpoint (375px + results); review; PR

## Dependencies

- T001 before T002/T004/T008.
- T004 before T005/T008.
- T005/T006 before T007.
- T010 last.
