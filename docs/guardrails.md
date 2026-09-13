# Guardrails

Constitution **EV-3** requires that guardrail metrics (quality, safety, latency,
cost) be compared per change — a change that improves its target metric must not
silently regress another. This document declares the guardrails and their floors;
`evals/guardrails.py` aggregates them from the keyless artifacts and the gate
fails on a regression.

## Declared guardrails

| Guardrail | Floor | Direction | Source |
| --- | ---: | --- | --- |
| `quality:gold_pass_rate` | 1.000 | at least | `segments` (gold scenarios) |
| `safety:adversarial_safe_rate` | 1.000 | at least | `adversarial` |
| `safety:regression_coverage` | 1.000 | at least | `regressions` |
| `data:dirty_accuracy` | 1.000 | at least | `data_quality` |
| `resilience:fallback_coverage` | 1.000 | at least | `fallbacks` |
| `latency:turn_p95_us` | 10000 | at most | `scale` (at the target concurrency) |
| `cost:spent_cny` | 10.00 | at most | `data/budget.json` (HR-12) |

A floor is a **minimum acceptable**, not a target: a metric above an `at_least`
floor (or below an `at_most` floor) is fine. The check **aggregates** the keyless
artifacts rather than recomputing, so it cannot disagree with the report and runs
in the gate for free.

```bash
uv run python evals/guardrails.py
```

## Per change (EV-1 / EV-3)

Every `measurable` entry in `specs/change-log.json` MUST state its `guardrails`
impact. The evidence gate (`scripts/check_change_evidence.py`) fails an entry that
omits it. A change that does not touch a guardrail says so explicitly.

## Trend history

`evals/guardrails.py --record` appends the current values to
`evals/guardrail-history.jsonl` (append-only, capped at 50 entries); the report
shows each guardrail's delta vs the previous recorded run. The gate runs the check
**without** `--record`, so a normal run never dirties the working tree.

```bash
uv run python evals/guardrails.py --record   # after a meaningful run
```

## Gaps (honest)

- Guardrails are keyless; the real (paid) eval's quality/safety numbers are a
  dated snapshot and are not floors.
- Recording is manual; there is no scheduler that records after every release.
