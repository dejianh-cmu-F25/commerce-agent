# Agent Note: Guardrails are compared, not assumed

Status: implemented (2026-09-13) — feature `036-guardrails`

## Problem

EV-3 requires that guardrail metrics (quality, safety, latency, cost) be compared
per change, so a change that improves its target metric cannot silently regress
another. The project had the metrics (gold pass rate, adversarial safe-rate,
dirty-data accuracy, fallback coverage, latency, cost) but nothing that compared
them to a declared floor or required a change to state its guardrail impact.

## Alternatives considered

- **Recompute the guardrails in one script.** Duplicates the other evals and can
  drift from the report. Rejected.
- **Rely on the PR checklist.** A checkbox is not a comparison. Rejected.
- **Aggregate the existing artifacts against declared floors, and require a
  statement per measurable change.** Chosen.

## Decision

- **`docs/guardrails.md`** declares 7 guardrails with numeric floors and an
  explicit direction (`at_least` / `at_most`).
- **`evals/guardrails.py`** reads the keyless artifacts and the budget, compares
  each metric to its floor, writes the table to the report, and **fails the gate**
  on a regression. It aggregates rather than recomputes, so it cannot disagree
  with the report.
- **`scripts/check_change_evidence.py`** now requires a `guardrails` statement on
  every `measurable` change-log entry (EV-1/EV-3); the nine older measurable
  entries were backfilled with an honest "not compared at the time (pre-036)".

## Consequences

- A change that drops a guardrail below its floor fails the gate; the report shows
  every guardrail, its value, its floor, and its status.
- The latency guardrail value is a wall-clock timing and is a snapshot; the gate
  validates the row, not the exact value.
- **Residual gap**: guardrails are keyless and current-value only — there is no
  trend history, and the paid eval's numbers are not floors.
