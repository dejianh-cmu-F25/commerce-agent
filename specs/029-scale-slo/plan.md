# Implementation Plan: Scale Envelope & SLOs

**Branch**: `029-scale-slo` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `evals/scale.py` (keyless concurrency benchmark for retrieval and a full
scripted agent turn), declare the dimensions + budgets in `docs/scale.md`, render
the table in the report, and enforce the budgets in the gate.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| SC-1 | dimensions declared + measured behavior at the boundary | PASS |
| SC-3 | latency/error/cost budgets declared + tracked + regressions visible | PASS |
| P8 | keyless (no network) | PASS |
| HR-12 | cost budget already tracked; the benchmark is free | PASS |

## Project Structure

```text
evals/scale.py                   # NEW: concurrency benchmark + SLO check
docs/scale.md                    # NEW: dimensions, budgets, measured boundary
evals/report.py                  # render the scale section
scripts/check_results.py; scripts/ci.sh
tests/unit/test_scale.py
specs/029-scale-slo/
```

## Design decisions

- **Measure the keyless stack.** A scripted agent turn and TF-IDF retrieval are
  deterministic and free, so the envelope is reproducible in the gate (P8).
- **p95, not mean.** A budget on p95 catches tail regressions; the report also
  carries p50 and throughput.
- **Generous regression guards.** Budgets are set well above measured values so a
  loaded CI host does not flake; the value is catching an order-of-magnitude
  regression.
- **Envelope as data.** The benchmark records the tested dimensions (catalog,
  chunks, concurrency, ops) so the claim is falsifiable.

## Complexity Tracking

> No violations; stdlib only.
