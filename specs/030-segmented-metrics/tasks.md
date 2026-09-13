# Tasks: Segmented Metrics

**Feature**: `030-segmented-metrics` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `evals/scenarios.py`: add `intent` to every scenario
- [x] T002 `evals/runner.py`: `ScenarioResult.intent` + `tool_results`
- [x] T003 `app/evaluation/segments.py`: `by_intent`, `by_tool`
- [x] T004 `evals/run.py`: write `segments` to the keyless artifact
- [x] T005 `evals/report.py` + `scripts/check_results.py`
- [x] T006 [P] `tests/unit/test_segments.py`
- [x] T007 `docs/diagnosability.md`; Agent Note; change log entry
- [x] T008 `make ci-fast`; PR

## Dependencies

- T001/T002 before T003/T004.
- T004 before T005/T008.
- T008 last.
