# Tasks: Declared Fallbacks

**Feature**: `031-fallbacks` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/core/resilience.py`: `Degradation`, `FallbackRetriever`
- [x] T002 `app/core/settings.py` + `config/settings.yaml` + `.env.example`: `resilience`
- [x] T003 `web/main.py`: wrap dense with the lexical fallback
- [x] T004 `evals/fallbacks.py` + `scripts/ci.sh`
- [x] T005 `evals/report.py` + `scripts/check_results.py`
- [x] T006 [P] `tests/unit/test_resilience.py`
- [x] T007 `docs/degradation.md`; Agent Note; change log entry
- [x] T008 `make ci-fast`; PR

## Dependencies

- T001 before T003/T004/T006.
- T004 before T005/T008.
- T008 last.
