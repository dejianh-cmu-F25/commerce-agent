# Tasks: Guardrail Metrics

**Feature**: `036-guardrails` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `evals/guardrails.py`: aggregate + floor check; `scripts/ci.sh`
- [x] T002 `docs/guardrails.md`: metrics + floors + policy
- [x] T003 `evals/report.py` + `scripts/check_results.py`
- [x] T004 `scripts/check_change_evidence.py`: require guardrails; backfill the log
- [x] T005 [P] `tests/unit/test_guardrails.py`
- [x] T006 Agent Note; change log entry
- [x] T007 `make ci-fast`; PR

## Dependencies

- T001 before T003/T005/T007.
- T007 last.
