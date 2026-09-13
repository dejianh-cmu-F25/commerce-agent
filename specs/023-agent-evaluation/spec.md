# Feature Specification: Agent Evaluation Upgrade

**Feature Branch**: `023-agent-evaluation`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Upgrade the evaluation harness per the book's chapter 7: process
metrics, failure attribution (first error), Pass@k / Pass^k, a Rubric
LLM-as-a-Judge (DeepSeek), statistical reporting, and a feature ablation —
keyless in the gate plus opt-in real-model runs, with a committed report.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Process metrics and failure attribution (Priority: P1)

For a run, the harness reports white-box process metrics (steps, tool calls,
tool success, ungrounded-id attempts, latency, tokens, cost) and, when a run
fails, attributes the **first** error with a category and evidence.

**Why this priority**: End-to-end pass/fail does not say why a run failed; the
book's failure attribution is what turns a score into a fix.

**Independent Test**: Run a scenario with a scripted error and assert the
attribution names the first bad step and category.

**Acceptance Scenarios**:

1. **Given** a run, **When** metrics are computed, **Then** steps, tool counts,
   latency, tokens, and cost are reported.
2. **Given** a failed run, **When** attribution runs, **Then** it returns the
   first error's category, step, and evidence (e.g. unknown tool, ungrounded id,
   out-of-policy return, budget, max turns).

---

### User Story 2 - Reliability: Pass@k and Pass^k (Priority: P1)

Given N runs of a task, the harness reports Pass@1, Pass@k, Best@k, and Pass^k,
so capability and reliability are distinguished.

**Why this priority**: The book's central metric distinction; the project needs
it for a credible "reliability" number.

**Independent Test**: Feed known success patterns and assert the four metrics.

**Acceptance Scenarios**:

1. **Given** k runs with 3 successes of 5, **When** reliability is computed,
   **Then** Pass@1 = 0.6 and Pass^k reflects all-successes.

---

### User Story 3 - Rubric judge (DeepSeek) with a veto (Priority: P2)

An optional judge scores an answer against a rubric (grounding, correctness,
policy compliance, completeness, tone) with a **veto** for fabrication, and
falls back to deterministic checks when disabled.

**Why this priority**: Open-ended answers need more than exact match; the veto
encodes the project's grounding rule (P4).

**Independent Test**: Grade a fabricated answer and assert the veto fires;
disable the judge and assert the deterministic fallback runs.

**Acceptance Scenarios**:

1. **Given** a fabricated price, **When** the judge runs, **Then** the veto
   fails the answer.
2. **Given** `evaluation.judge` disabled, **When** grading runs, **Then** the
   deterministic (grounding) check is used.

---

### User Story 4 - Feature ablation, keylessly (Priority: P1)

The harness runs the gold set under configurations (naked, +memory, +skills,
retrieval variants) and reports the pass-rate delta of each feature.

**Why this priority**: This is the "I changed X → effect Y" evidence.

**Independent Test**: Ablate memory; assert the memory-recall scenario flips.

**Acceptance Scenarios**:

1. **Given** the configs, **When** the ablation runs, **Then** each config's
   pass rate and the delta vs the naked baseline are reported.

---

### User Story 5 - Real runs and a committed report (Priority: P2)

An opt-in real run uses DeepSeek (budget-capped) over a small case set × seeds
to produce reliability, process metrics, and judge scores; the report is
committed.

**Independent Test**: `evals/agent_eval.py --real` respects the cost cap and
writes the report sections.

**Acceptance Scenarios**:

1. **Given** `--real` and a key, **When** it runs, **Then** it reports Pass@1 /
   Pass^k and stops at the cost cap.
2. **Given** no key, **When** `--real` runs, **Then** it fails loud with a clear
   message.

---

### Edge Cases

- **No key**: `--real` fails loud; the keyless path is unaffected.
- **Budget exhausted**: the run stops and reports partial results.
- **Judge returns bad JSON**: the deterministic fallback is used (RD-1).
- **All-success or all-failure**: reliability metrics still defined.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The harness MUST compute process metrics from the run's events:
  steps, tool calls, tool success/failure, ungrounded-id attempts, latency,
  tokens, and cost.
- **FR-002**: The harness MUST attribute the **first** error of a failed run to a
  category with step and evidence.
- **FR-003**: The harness MUST compute Pass@1, Pass@k, Best@k, and Pass^k.
- **FR-004**: The harness MUST provide a rubric judge (DeepSeek) with a veto for
  fabrication, configurable, with a deterministic fallback (RD-1).
- **FR-005**: The harness MUST ablate features (memory, skills, retrieval) on the
  keyless gold set and report deltas.
- **FR-006**: Real runs MUST be opt-in, budget-capped, and MUST fail loud without
  a key (HR-12, PB-1).
- **FR-007**: The report (`evals/report.md`) MUST include the ablation, the real
  reliability/process/cost/judge sections, and the failure categories; it is
  committed.
- **FR-008**: The keyless parts MUST run in the gate; real runs MUST NOT.

### Key Entities

- **RunMetrics**: process metrics for one run.
- **FailureAttribution**: category, step, evidence.
- **Reliability**: Pass@1, Pass@k, Best@k, Pass^k, n, successes.
- **JudgeResult**: per-dimension scores, veto, rationale.

## Observability

- Process metrics read the existing trace spans and the cost meter; the judge and
  real runs are recorded in `evals/results-real.json` with the model, seeds, and
  command (OB-1, OB-3).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The ablation reports a pass-rate delta per feature (memory and
  skills change their scenarios; the naked baseline is lower).
- **SC-002**: A real DeepSeek run reports Pass@1/Pass^k over the case set × seeds
  and stops at the cost cap.
- **SC-003**: The report is committed and states the model, seeds, and command.
- **SC-004**: The judge's veto fires on a fabricated answer; the fallback works.
- **SC-005**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes.

## Assumptions

- Real runs use DeepSeek as both agent and judge (same family; the same-source
  bias is documented, and the judge model is configurable).
- The real case set is a small, robust subset with outcome-based success
  predicates (not exact tool sequences).
- Statistical reporting is paired over seeds with a confidence interval; large
  sample sizes are out of scope for a demo.
- The gate stays keyless and fast; real runs are manual and budget-capped.

## Measured Results

Feature ablation (keyless, 12 gold scenarios):

| Config | Pass rate | Delta vs naked |
| --- | ---: | ---: |
| `naked` | 0.750 | +0.000 |
| `+memory` | 0.917 | +0.167 |
| `+skills` | 0.833 | +0.083 |

Real model (DeepSeek, 6 templates × 3 seeds = 18 runs; dated snapshot, not
regenerated by the gate; rendered-prompt hash `8578920a4f16`): Pass@1 **0.778** ·
Pass@k 1.000 · Pass^k **0.667**; 0 ungrounded attempts; 0 judge vetoes; avg 2.06
steps; p95 5485 ms; **¥0.0949**.

- Source: `evals/report.md`; aggregate: [`specs/RESULTS.md`](../RESULTS.md).

## Real-World Coverage

- **Input distribution**: seeded templates including negative cases; language
  and adversarial coverage are thin (gap).
- **Data quality**: results are dated snapshots with model and prompt hash.
- **Edge & failure modes**: a bad judge response falls back to rules (RD-1); the run stops at the cost cap.
- **Scale envelope**: 6 templates × 3 seeds; not a load test (gap).
- **Degradation**: the real runner is opt-in; the keyless ablation runs in the gate.
- **Change evidence**: this feature provides the before/after infrastructure (EV).
