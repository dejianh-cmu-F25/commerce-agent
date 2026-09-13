# Implementation Plan: Segmented Metrics

**Branch**: `030-segmented-metrics` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add an `intent` to each scenario, record per-tool status in the runner, add pure
segmentation (`app/evaluation/segments.py`), write the segments to the keyless
artifact, render them, and validate them in the gate.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| SC-2 | metrics segmentable by intent and tool | PASS |
| OB | reuses the existing trace-derived tool status | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
app/evaluation/segments.py       # NEW: by_intent, by_tool
evals/scenarios.py               # + intent per scenario
evals/runner.py                  # + intent, tool_results on ScenarioResult
evals/run.py                     # write segments to the keyless artifact
evals/report.py                  # render the segmented section
scripts/check_results.py; scripts/ci.sh
docs/diagnosability.md           # SC-2 statement + gaps
tests/unit/test_segments.py
```

## Design decisions

- **Intent is declared, not inferred.** A scenario's job is a property of the
  scenario, not a guess from its tool list.
- **Reuse the sink's tool status.** The runner already has `ToolResult` events;
  no new tracing.
- **Pure segmentation.** `by_intent`/`by_tool` take plain results and return
  dicts, so they are trivially testable and reusable by the web Scenario Runner.

## Complexity Tracking

> No violations; stdlib only.
