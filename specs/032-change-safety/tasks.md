# Tasks: Change Safety

**Feature**: `032-change-safety` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 Backfill `blast_radius` + `rollback` on all change-log entries
- [x] T002 `scripts/check_results.py` + `scripts/check_change_evidence.py`: require both
- [x] T003 `evals/report.py`: render both columns
- [x] T004 [P] `tests/unit/test_change_log.py`
- [x] T005 `docs/change-safety.md`; PR template; Agent Note; change log entry
- [x] T006 `make ci-fast`; PR

## Dependencies

- T001 before T002/T003/T004.
- T006 last.
