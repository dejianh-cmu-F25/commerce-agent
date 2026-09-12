# Tasks: Retrieval Benchmark & Ablation

**Feature**: `022-retrieval-benchmark` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/evaluation/retrieval_metrics.py` (hit-rate@k, recall@k, MRR, evaluate)
- [x] T002 `evals/retrieval_set.py` (labeled cases, easy/medium/hard)
- [x] T003 `evals/bench.py` (three configs, thresholds, JSON out)
- [x] T004 `evals/report.py` (assemble `evals/report.md`)
- [x] T005 `scripts/ci.sh`: run the bench
- [x] T006 [P] `tests/unit/test_retrieval_metrics.py`
- [x] T007 [P] `tests/integration/test_retrieval_bench.py`
- [x] T008 Generate + commit `evals/report.md`; `docs/architecture.md`; Agent Note
- [x] T009 `scripts/ci.sh --fast`; self-review; PR

## Dependencies

- T001/T002 before T003/T006.
- T003 before T004/T005/T007/T008.
- T009 last.
