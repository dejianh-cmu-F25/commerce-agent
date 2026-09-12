# Implementation Plan: Retrieval Benchmark & Ablation

**Branch**: `022-retrieval-benchmark` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add pure retrieval metrics (`app/evaluation/retrieval_metrics.py`), a labeled
query set (`evals/retrieval_set.py`), a keyless benchmark comparing TF-IDF,
dense+hash, and dense+Chroma (`evals/bench.py`), a report generator
(`evals/report.py` → committed `evals/report.md`), and a gate step. No new
dependency.

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: none new (uses the existing retrievers)

**Storage**: in-process / temp Chroma per run

**Testing**: `pytest` (unit: metrics; integration: bench runs and thresholds);
the bench itself runs in the gate

**Constraints**: keyless, deterministic metrics; small corpus

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P4 grounding | measures the retrieval path that grounds answers | PASS |
| P7 evals first-class | a new, reproducible eval asset | PASS |
| P8 keyless | hash embedding; no key; no network | PASS |
| TT-2 deterministic | metrics assert deterministic outcomes | PASS |
| HR-11 | new queries are data; documented | PASS |
| OB-3 | produces quality metrics for the report | PASS |

## Project Structure

```text
app/evaluation/retrieval_metrics.py   # NEW: hit_rate_at_k, recall_at_k, mrr
evals/retrieval_set.py                # NEW: labeled cases
evals/bench.py                        # NEW: run configs, thresholds
evals/report.py                       # NEW: assemble evals/report.md
evals/report.md                       # NEW: committed
scripts/ci.sh                         # run the bench
tests/unit/test_retrieval_metrics.py
tests/integration/test_retrieval_bench.py
docs/architecture.md; Agent Note
```

## Design decisions

- **Deterministic metrics; indicative latency.** hit@k/recall@k/MRR are
  deterministic (no model); latency is reported but not gated.
- **Three configs on one set.** TF-IDF `memory`, dense+`hash`, dense+`chroma`
  (temp dir) — a clean ablation of the retrieval choice.
- **Report from a JSON artifact.** `evals/bench.py` emits structured results;
  `evals/report.py` renders `evals/report.md` and merges later real sections
  (023) without clobbering them.
- **Data, not code.** Adding a query is a `retrieval_set.py` entry.

## Complexity Tracking

> No violations; no new dependency.
