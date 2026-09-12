# Tasks: Agent Evaluation Upgrade

**Feature**: `023-agent-evaluation` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

- [x] T001 `app/evaluation/agent_metrics.py` (process metrics from events)
- [x] T002 `app/evaluation/failure.py` (first-error attribution)
- [x] T003 `app/evaluation/reliability.py` (Pass@1/@k/Best@k/Pass^k)
- [x] T004 `app/evaluation/rubric.py` (rubric + DeepSeek judge + fallback)
- [x] T005 `app/core/settings.py`: `EvaluationSettings` + env; `.env.example` parity
- [x] T006 `evals/ablation.py` (keyless feature ablation) + `scripts/ci.sh`
- [x] T007 `evals/real_cases.py` + `evals/agent_eval.py` (opt-in real, capped)
- [x] T008 `evals/report.py`: ablation + real sections
- [x] T009 [P] unit tests: metrics, failure, reliability, rubric
- [x] T010 [P] integration: `tests/integration/test_ablation.py`
- [x] T011 Run keyless ablation; run `--real` once; commit `evals/report.md`
- [x] T012 `docs/architecture.md`; Agent Note
- [x] T013 `scripts/ci.sh --fast`; self-review; PR

## Dependencies

- T001–T005 before T006/T007/T009.
- T006 before T008/T010/T011.
- T007 before T008/T011.
- T013 last.
