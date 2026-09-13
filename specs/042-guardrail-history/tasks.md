# Tasks: Guardrail Trend History

**Feature**: `042-guardrail-history` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `evals/guardrails.py`: `load_history`, `record`, `--record`, trend
- [x] T002 Seed `evals/guardrail-history.jsonl`
- [x] T003 `evals/report.py`: delta column
- [x] T004 `docs/guardrails.md`; Agent Note; change log entry
- [x] T005 [P] `tests/unit/test_guardrails.py`: record/load
- [x] T006 `make ci-fast`; PR

## Dependencies

- T001 before T002/T003/T005.
- T006 last.
