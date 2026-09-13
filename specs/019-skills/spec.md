# Feature Specification: Skills

**Feature Branch**: `019-skills`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Implement the skills extension point (HR-11): load
`skills/<name>/SKILL.md`, advertise skill names and descriptions in the system
prompt, and let the agent load a procedure on demand through a `use_skill` tool.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load a procedure on demand (Priority: P1)

The agent sees a catalog of available skills and, when a task matches, loads the
skill body and follows it.

**Why this priority**: The architecture reserves skills as the mechanism for
long-tail procedures; none exist, so every procedure would have to live in the
system prompt or code.

**Independent Test**: Build the agent with a skill present; assert the catalog is
in the system prompt and `use_skill` returns the body.

**Acceptance Scenarios**:

1. **Given** a skill on disk, **When** the agent is built, **Then** the system
   prompt lists its name and description (not its full body).
2. **Given** a known skill name, **When** `use_skill` runs, **Then** it returns
   the skill body.
3. **Given** an unknown skill name, **When** `use_skill` runs, **Then** it returns
   an error and the turn continues.

---

### User Story 2 - Add a skill without code (Priority: P1)

A new skill is a new directory with a `SKILL.md`; no code change is needed.

**Independent Test**: Add a skill file, rebuild, and assert it appears in the
catalog and is loadable.

**Acceptance Scenarios**:

1. **Given** a new `skills/<name>/SKILL.md`, **When** the app starts, **Then** the
   skill is advertised and loadable.

---

### User Story 3 - Keyless and fail-soft (Priority: P2)

Skills need no key; a missing directory or malformed file does not break startup.

**Independent Test**: Point at a missing directory; assert the app starts with no
skills.

**Acceptance Scenarios**:

1. **Given** `skills.enabled: false`, **When** the app starts, **Then** there is
   no catalog and no `use_skill` tool.
2. **Given** a missing skills directory, **When** the app starts, **Then** it
   starts with no skills (no crash).

---

### Edge Cases

- **No frontmatter**: the name comes from the directory; the description from the
  first non-empty line.
- **Duplicate names**: the first wins; a warning is not fatal.
- **Empty body**: the skill is still listed; loading it returns what is there.
- **Context discipline**: only names + descriptions go in the prompt; bodies load
  on demand (HR-6).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST load skills from `skills/<name>/SKILL.md`, honoring
  optional `---` frontmatter with `name` and `description`.
- **FR-002**: The system prompt MUST advertise the skill catalog (name +
  description), not full bodies.
- **FR-003**: A `use_skill(name)` tool MUST return a known skill's body and return
  an error for an unknown name (never ending the turn).
- **FR-004**: `skills.enabled` and `skills.path` MUST select behavior; a disabled
  or missing set yields no catalog and no tool (fail-soft, P8).
- **FR-005**: Adding a `SKILL.md` MUST change behavior without a code change
  (HR-11).
- **FR-006**: Skills MUST be keyless and external (files, not inline strings;
  PB-4).

### Key Entities

- **Skill**: a named procedure with a description and a body, loaded from a file.
- **SkillLibrary**: the loaded skills; renders the catalog and resolves by name.

## Observability

- `use_skill` is a normal tool: its call is traced as a `tool` span and rendered
  as a chat step (OB-1).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: With skills present, the catalog appears in the system prompt.
- **SC-002**: `use_skill` returns the body for a known skill and an error for an
  unknown one.
- **SC-003**: Adding a `SKILL.md` makes it advertised and loadable with no code
  change.
- **SC-004**: A missing/disabled skills directory starts cleanly.
- **SC-005**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes.

## Assumptions

- Skills are static markdown; no dynamic loading or versioning.
- Selection is model-driven (the catalog guides the model to call `use_skill`);
  there is no separate intent classifier.
- The example skills are demo procedures, not exhaustive.

## Real-World Coverage

- **Input distribution**: skill names from the model; a missing skill errors.
- **Data quality**: `SKILL.md` files with optional frontmatter; a malformed file
  is skipped, not fatal.
- **Edge & failure modes**: an unknown skill returns an error without ending the
  turn; a missing directory yields no skills.
- **Scale envelope**: the catalog grows with the prompt; not measured (gap).
- **Degradation**: skills disabled by config -> no catalog, no tool.
- **Change evidence**: ablation +0.083 (`specs/change-log.json` #25).
