# Tasks: Parameterized Eval Cases

**Feature**: `024-parameterized-cases` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `evals/real_cases.py`: templates + `build_cases(seed)` + new predicate fields
- [x] T002 `evals/agent_eval.py`: per-seed cases; predicate handles max price / min cart; per-template aggregation
- [x] T003 [P] `tests/unit/test_real_cases.py` (stable names, varying params, reproducible)
- [x] T004 Run `--real`; regenerate `evals/report.md`
- [x] T005 `scripts/ci.sh --fast`; self-review; PR

## Dependencies

- T001 before T002/T003/T004.
- T005 last.
