# Tasks: Evaluation Harness

**Feature**: `011-evaluation` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Gold set + runner

- [x] T001 `evals/__init__.py` + `evals/scenarios.py` (Scenario, SCENARIOS)
- [x] T002 `evals/run.py`: `run_all()` + `main()` (real loop/tools/stores; deterministic assertions)
- [x] T003 `tests/integration/test_evals.py`: the suite passes under pytest

## Phase 2 — Gate + config

- [x] T004 `scripts/ci.sh`: run `evals/run.py` as a step
- [x] T005 `pyproject.toml`: include `evals` in pyright

## Phase 3 — Verify & deliver

- [x] T006 `scripts/ci.sh --fast` (evals included)
- [x] T007 Update `docs/architecture.md` (evals row); commit and open the PR

## Dependencies

- T001 before T002.
- T002 before T003/T004.
- T006/T007 last.
