# Tasks: Adversarial & Out-of-Distribution Input

**Feature**: `028-adversarial-input` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/safety/input_guard.py` (normalize_input, check_input, GuardVerdict)
- [x] T002 `app/core/settings.py` + `config/settings.yaml` + `.env.example`: `safety`
- [x] T003 `app/core/loop.py`: apply the guard before the model call
- [x] T004 `web/main.py`: pass `settings.safety`
- [x] T005 `evals/adversarial_set.py` + `evals/adversarial.py`; `scripts/ci.sh`
- [x] T006 `evals/report.py` + `scripts/check_results.py`: render/validate
- [x] T007 [P] `tests/unit/test_input_guard.py`, `tests/integration/test_adversarial_turn.py`
- [x] T008 Agent Note; change log entry
- [x] T009 `make ci-fast`; PR

## Dependencies

- T001 before T003/T005/T007.
- T005 before T006/T009.
- T009 last.
