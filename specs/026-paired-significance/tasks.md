# Tasks: Paired Significance

**Feature**: `026-paired-significance` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/evaluation/significance.py` (mcnemar_p, bootstrap_ci, paired_delta)
- [x] T002 `evals/ablation.py`: paired delta per config
- [x] T003 `evals/agent_eval.py`: Pass@1 CI
- [x] T004 `evals/report.py`: render CI + p
- [x] T005 [P] `tests/unit/test_significance.py`
- [x] T006 Agent Note; change log entry
- [x] T007 `make ci-fast`; PR

## Dependencies

- T001 before T002/T003/T005.
- T002/T003 before T004.
- T007 last.
