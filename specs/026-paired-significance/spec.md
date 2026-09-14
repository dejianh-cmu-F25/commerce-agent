# Feature Specification: Paired Significance

**Feature Branch**: `026-paired-significance`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Add paired significance to the evaluation report — a bootstrap 95%
confidence interval on the ablation delta and a McNemar test against the naked
baseline — so a "before → after" is statistically stated, not just a raw
difference (EV-2).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ablation deltas carry a CI and a p-value (Priority: P1)

Each ablation configuration reports its paired delta vs the naked baseline with a
95% confidence interval and a McNemar p-value.

**Why this priority**: EV-2 requires effect size, confidence, and sample size;
a raw delta on a small set is not proof.

**Independent Test**: Feed known paired outcomes and assert the delta, CI, and
p-value.

**Acceptance Scenarios**:

1. **Given** per-scenario outcomes for two configs, **When** the paired delta is
   computed, **Then** it reports the mean delta, a 95% CI, the p-value, and n.
2. **Given** the same inputs, **When** it runs twice, **Then** the result is
   identical (fixed seed).

---

### User Story 2 - Real reliability carries a CI (Priority: P2)

The real-model Pass@1 is reported with a bootstrap 95% CI.

**Independent Test**: The agent section includes a Pass@1 confidence interval.

**Acceptance Scenarios**:

1. **Given** the real run outcomes, **When** the report is rendered, **Then**
   Pass@1 is shown with its 95% CI.

---

### Edge Cases

- **No discordant pairs**: McNemar returns p = 1.0.
- **Empty input**: delta 0, CI (0, 0).
- **All-success or all-failure**: CI is defined (may be degenerate).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide pure functions: a two-sided exact McNemar
  p-value on paired booleans, and a percentile bootstrap CI of a mean.
- **FR-002**: The ablation MUST report, per config, the paired delta vs the naked
  baseline with a 95% CI, a McNemar p-value, and n.
- **FR-003**: The real reliability MUST report a bootstrap 95% CI on Pass@1.
- **FR-004**: Results MUST be deterministic (fixed resample seed).
- **FR-005**: The report MUST render the CI and p-value.

### Key Entities

- **PairedDelta**: delta, ci_low, ci_high, p_value, n.

## Observability

- Pure computation over existing results; no new span. The report records the CI
  and p-value.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The ablation table shows a 95% CI and a p-value per config.
- **SC-002**: The real section shows Pass@1 with a 95% CI.
- **SC-003**: Deterministic across runs.
- **SC-004**: The local gate passes.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Assumptions

- The gold set is small, so CIs will be wide; that is the honest result (the book
  warns about small samples).
- Percentile bootstrap with 2000 resamples is sufficient for a demo.

## Real-World Coverage

- **Input distribution**: evaluation outcomes (booleans per task/run); the
  statistics operate on whatever the eval set produces.
- **Data quality**: the bootstrap is fixed-seed and deterministic; empty input
  returns `(0, 0)`; mismatched lengths raise.
- **Edge & failure modes**: no discordant pairs -> p = 1.0; all-success or
  all-failure -> a degenerate but defined CI.
- **Scale envelope**: n/a (offline computation); the CI width honestly reflects
  the sample size.
- **Degradation**: pure stdlib functions; no dependency.
- **Change evidence**: this feature strengthens the evidence of other changes
  (EV-2); recorded in `specs/change-log.json` #38.
