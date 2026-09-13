# Tasks: Scale Envelope & SLOs

**Feature**: `029-scale-slo` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `evals/scale.py` (measure levels, SLO check)
- [x] T002 `docs/scale.md` (dimensions, budgets, measured boundary)
- [x] T003 `evals/report.py` + `scripts/check_results.py` + `scripts/ci.sh`
- [x] T004 [P] `tests/unit/test_scale.py` (SLO evaluation)
- [x] T005 Agent Note; change log entry
- [x] T006 `make ci-fast`; PR

## Dependencies

- T001 before T003/T004.
- T006 last.
