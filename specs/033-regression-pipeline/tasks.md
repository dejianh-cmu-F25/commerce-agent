# Tasks: Failure-to-Regression Pipeline

**Feature**: `033-regression-pipeline` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/evaluation/regressions.py`: `Regression`, `load`
- [x] T002 `evals/regressions.json`: the registry (5 entries)
- [x] T003 `evals/regressions.py`: keyless runner + gate; `scripts/ci.sh`
- [x] T004 `scripts/promote_regression.py`: promote (requires root cause)
- [x] T005 `evals/report.py` + `scripts/check_results.py`
- [x] T006 [P] `tests/unit/test_regressions.py`
- [x] T007 `docs/regressions.md`; Agent Note; change log entry
- [x] T008 `make ci-fast`; PR

## Dependencies

- T001/T002 before T003/T004/T006.
- T003 before T005/T008.
- T008 last.
