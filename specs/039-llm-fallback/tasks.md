# Tasks: LLM Provider Fallback

**Feature**: `039-llm-fallback` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/core/resilience.py`: `FallbackLLM`
- [x] T002 `app/core/settings.py` + `config/settings.yaml` + `.env.example`: `llm.fallback_*`
- [x] T003 `web/main.py`: wrap when configured
- [x] T004 `evals/fallbacks.py`: `llm_fallback` case
- [x] T005 `docs/degradation.md`; Agent Note; change log entry
- [x] T006 [P] `tests/unit/test_resilience.py`: LLM fallback
- [x] T007 `make ci-fast`; PR

## Dependencies

- T001/T002 before T003/T004/T006.
- T007 last.
