# Implementation Plan: Skills

**Branch**: `019-skills` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `app/skills/loader.py` (parse `skills/<name>/SKILL.md` with optional
frontmatter into a `SkillLibrary`), a `use_skill` tool, `SkillsSettings`, and
wiring that appends the catalog to the system prompt and registers the tool. Ship
two example skills. Keyless; adding a skill is a new file.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: stdlib only (`pathlib`, `re`)

**Storage**: `skills/<name>/SKILL.md` files

**Testing**: `pytest` (unit: loader; integration: catalog + tool); one eval
scenario

**Constraints**: keyless; fail-soft on a missing directory (P8); external content
(PB-4)

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| PB-4 prompts external | skill bodies are files; only the catalog is added to the prompt | PASS |
| PB-1 config as contract | `skills.enabled`/`skills.path`; a missing path is not fatal | PASS |
| HR-6 context discipline | the prompt carries names + descriptions; bodies load on demand | PASS |
| HR-11 extension point | a new skill is a new file | PASS |
| P2 one agent, skills, tools | skills are modularity, not a second agent | PASS |
| P8 keyless | stdlib parsing; no key | PASS |
| RD-1 resilience | unknown skill is a tool error; the turn continues | PASS |

## Project Structure

```text
app/skills/loader.py         # NEW: Skill, SkillLibrary, load_skills
app/tools/skills.py          # NEW: use_skill
app/core/settings.py         # + SkillsSettings, env overrides
web/main.py                  # build_skill_library; catalog + tool in build_agent
skills/trip-planning/SKILL.md, skills/size-and-fit/SKILL.md  # NEW examples
config/settings.yaml; .env.example
tests/unit/test_skills.py; tests/integration/test_skills_tool.py
evals/scenarios.py; evals/runner.py   # + use_skill scenario
docs/architecture.md; Agent Note
```

## Design decisions

- **Catalog + on-demand body (progressive disclosure).** The system prompt lists
  names and descriptions; `use_skill` returns the body. This respects HR-6 and
  keeps the prompt small as skills grow.
- **Frontmatter optional.** `---\nname: …\ndescription: …\n---` is parsed with a
  tiny reader; without it, the directory name and first line are used, so a skill
  is easy to author.
- **Fail-soft loading.** A missing/disabled directory yields an empty library and
  no tool; malformed files are skipped, never fatal.
- **Model-driven selection.** The catalog is the guide; there is no separate
  classifier (simpler, and the model already chooses tools).

## Complexity Tracking

> No violations. One loader + one tool; no new dependency.
