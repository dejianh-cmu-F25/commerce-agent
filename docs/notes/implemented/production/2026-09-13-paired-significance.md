# Agent Note: Improvements are stated with a CI and a p-value

Status: implemented (2026-09-13) — feature `026-paired-significance`

## Problem

The ablation reported a raw delta (e.g., memory +0.167) and the real eval a raw
Pass@1. On a 12-scenario gold set and 18 real runs, a raw difference is not proof
(EV-2): the same delta could be sampling noise. The project claimed
"improvements" without an effect size, a confidence interval, or a sample size.

## Alternatives considered

- **Report the delta only.** Simple, but indistinguishable from noise on small
  sets. Rejected by EV-2.
- **Add SciPy for `ttest_rel`/`chi2`.** Heavy dependency for two small functions;
  P6 favors the simplest thing that works. Rejected.
- **Larger gold set instead of statistics.** Better, but a separate concern (and
  a large set is out of scope); statistics are still required regardless.
- **Paired bootstrap + exact McNemar, stdlib only.** Chosen.

## Decision

- **`app/evaluation/significance.py`**: an exact two-sided McNemar p-value on
  paired booleans, a percentile bootstrap CI of a mean (fixed seed), and a
  `paired_delta` that returns delta + CI + p + n.
- **The ablation reports the paired delta vs the naked baseline with a 95% CI and
  a McNemar p-value**; the real reliability reports a bootstrap 95% CI on Pass@1.
- **Deterministic**: a fixed resample seed, so a re-run reproduces the CI.

## Consequences

- The report now shows the honest result: memory +0.167 with a 95% CI of
  [0.000, 0.417] and p = 0.500 on 12 scenarios — a real effect that this sample
  cannot call significant. That is the book's point, and it is now visible.
- No dependency was added; the statistics are ~40 lines of stdlib.
- A larger gold set or more seeds will narrow the CIs; the harness now supports
  the comparison either way.
