# Implementation Plan: Paired Significance

**Branch**: `026-paired-significance` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `app/evaluation/significance.py` (exact McNemar, percentile bootstrap CI,
paired delta), integrate it into the ablation and the real reliability, and
render the CI/p-value in `evals/report.md`. No new dependency.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| EV-2 | paired, multiple seeds, effect size + confidence + sample size | PASS |
| P7 | strengthens the evaluation asset | PASS |
| TT-2 | deterministic (fixed seed) | PASS |
| P6 | stdlib only (`math`, `random`) | PASS |

## Project Structure

```text
app/evaluation/significance.py   # NEW
evals/ablation.py                # paired delta per config
evals/agent_eval.py              # Pass@1 CI
evals/report.py                  # render CI + p
tests/unit/test_significance.py
docs/notes/implemented/production/...-paired-significance.md
```

## Design decisions

- **Exact McNemar** (binomial on discordant pairs) — no SciPy dependency.
- **Percentile bootstrap** with a fixed seed for reproducibility.
- **Paired by scenario** — the ablation runs the same scenarios per config.

## Complexity Tracking

> No violations; stdlib only.
