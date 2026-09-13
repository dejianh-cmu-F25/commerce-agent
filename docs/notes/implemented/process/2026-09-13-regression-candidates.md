# Agent Note: Real-eval failures export to candidates automatically

Status: implemented (2026-09-13) — feature `043-regression-candidates`

## Problem

EV-5 requires failures to flow back into the suite, and RW-4 requires a fix to
ship with a regression. The registry existed (feature 033) but the step from a
real-eval failure to a candidate was manual: a failure could be lost between a
run and someone noticing it.

## Alternatives considered

- **Auto-promote failures into regressions.** Wrong: a regression needs a root
  cause (RW-4), which a machine cannot supply. Rejected.
- **Export to candidates automatically; root-cause and promote by hand.** Chosen —
  the evidence is never lost, and the cause stays a human judgment.

## Decision

- **`evals/agent_eval.py`** records per-failure detail (`task`, `seed`,
  `category`) in `results-real.json`.
- **`scripts/export_regression_candidates.py`** reads the results file and appends
  new, deduped candidates (`task`, `category`, `seeds`, `prompt_hash`,
  `status: candidate`) to `evals/regression-candidates.jsonl`. It is idempotent
  and a no-op without a results file.
- **A candidate is not a regression**: it is not run by the gate; a human
  root-causes it and promotes it (`scripts/promote_regression.py`).
- **`docs/regressions.md`** documents the export → root-cause → promote flow.

## Consequences

- No real-eval failure is lost; each distinct failure is a candidate with its
  evidence attached.
- **Residual**: the export runs after a real eval (opt-in); there is no scheduler.
  The candidates file is empty until a real run produces failures.
