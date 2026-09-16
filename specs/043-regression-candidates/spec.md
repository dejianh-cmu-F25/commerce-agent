# Feature Specification: Regression Candidates

**Feature Branch**: `043-regression-candidates`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Export real-eval failures to a committed candidate file (deduped) so
promotion starts from evidence, closing the EV-5 manual-export residual.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Real failures become candidates automatically (Priority: P1)

A real eval run records each failed run (task, seed, category); an export step
turns them into deduped **candidates** in a committed file. A human still
root-causes and promotes (a candidate is not a regression).

**Why this priority**: EV-5 — failures must flow back into the suite; the export
should be automatic so no failure is lost, while the root cause stays human.

**Independent Test**: Run the export over a synthetic results file and assert the
candidates are written and deduped.

**Acceptance Scenarios**:

1. **Given** a results file with failures, **When** the export runs, **Then** each
   distinct `(task, category)` is a candidate and a re-run adds nothing.
2. **Given** a candidate, **When** it is promoted, **Then** it becomes a
   regression (the existing pipeline).

---

### Edge Cases

- **No results file**: the export is a no-op (no crash).
- **Duplicate failures across seeds**: deduped by `(task, category)`.
- **A candidate is not a regression**: it carries `status: candidate` and is not
  run by the gate.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The real eval MUST record per-failure detail (`task`, `seed`,
  `category`).
- **FR-002**: An export MUST append new, deduped candidates to a committed file.
- **FR-003**: The export MUST be idempotent and a no-op without a results file.
- **FR-004**: `docs/regressions.md` MUST document the export → root-cause →
  promote flow.

### Key Entities

- **Candidate**: `task`, `category`, `seeds`, `prompt_hash`, `status: candidate`.

## Real-World Coverage

- **Input distribution**: real-eval failures across tasks/seeds.
- **Data quality**: deduped by `(task, category)`; idempotent.
- **Edge & failure modes**: a missing results file is a no-op; a candidate is not
  gated.
- **Scale envelope**: the file is O(distinct failures); see `docs/regressions.md`.
- **Degradation**: n/a (an offline export; no runtime path).
- **Change evidence**: the candidate flow (change log).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A synthetic results file exports deduped candidates.
- **SC-002**: A missing results file is a no-op.
- **SC-003**: The gate passes; candidates are not run as regressions.
- **SC-004**: The flow is documented.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Assumptions

- The real eval is opt-in and its results file is not committed; the candidates
  file is committed when populated.
