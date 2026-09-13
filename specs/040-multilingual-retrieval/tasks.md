# Tasks: Multilingual Retrieval Measurement

**Feature**: `040-multilingual-retrieval` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `evals/retrieval_set.py`: `MULTILINGUAL_SET`
- [x] T002 `evals/bench.py`: measure + store (not gated)
- [x] T003 `evals/report.py` + `scripts/check_results.py`
- [x] T004 `docs/clarify-vs-refuse.md` / `docs/edge-cases.md`: update the gap
- [x] T005 Agent Note; change log entry
- [x] T006 `make ci-fast`; PR

## Dependencies

- T001 before T002.
- T002 before T003/T006.
- T006 last.
