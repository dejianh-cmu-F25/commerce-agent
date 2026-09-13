# Tasks: Clarify-vs-Refuse & Multilingual Guard

**Feature**: `038-clarify-multilingual` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `config/prompts/system.md`: clarify + scope rules
- [x] T002 `evals/scenarios.py`: `ambiguous_request_clarifies`
- [x] T003 `app/safety/input_guard.py`: es/fr/de/zh patterns
- [x] T004 `evals/adversarial_set.py`: multilingual cases
- [x] T005 `docs/clarify-vs-refuse.md`; Agent Note; change log entry
- [x] T006 [P] `tests/unit/test_input_guard.py`: multilingual
- [x] T007 `make ci-fast`; PR

## Dependencies

- T003 before T004/T006.
- T007 last.
