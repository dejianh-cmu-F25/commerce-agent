# Tasks: Skills

**Feature**: `019-skills` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Phase 1 — Loader + config

- [x] T001 `app/skills/loader.py` (`Skill`, `SkillLibrary`, `load_skills`)
- [x] T002 `app/core/settings.py`: `SkillsSettings` + `SKILLS_ENABLED`/`SKILLS_PATH`
- [x] T003 `config/settings.yaml` + `.env.example` (parity)

## Phase 2 — Tool + wiring

- [x] T004 `app/tools/skills.py` (`use_skill`)
- [x] T005 `web/main.py`: load library; append catalog; register the tool
- [x] T006 `skills/trip-planning/SKILL.md`, `skills/size-and-fit/SKILL.md`

## Phase 3 — Tests + verify

- [x] T007 [P] Unit: `tests/unit/test_skills.py` (frontmatter, derivation, missing dir, duplicates)
- [x] T008 [P] Integration: `tests/integration/test_skills_tool.py` (catalog + tool)
- [x] T009 Eval: `use_skill` scenario + register in `evals/runner.py`
- [x] T010 `docs/architecture.md`; Agent Note
- [x] T011 `scripts/ci.sh --fast`; self-review; PR

## Dependencies

- T001/T002 before T004/T005/T007/T008.
- T006 before T009/T010.
- T011 last.
