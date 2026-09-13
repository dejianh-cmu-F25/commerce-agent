# Implementation Plan: Declared Fallbacks

**Branch**: `031-fallbacks` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `app/core/resilience.py` (`Degradation`, `FallbackRetriever`), a
`resilience.fallback_enabled` setting, wire dense → lexical in `build_retriever`,
and add a keyless coverage benchmark rendered in the report.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RD-1 | deterministic, config-gated fallback; degrades observably | PASS |
| PB-1 | `resilience.fallback_enabled` selects the behavior | PASS |
| SC-2 | degradation is recorded and attributable | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
app/core/resilience.py           # NEW: Degradation, FallbackRetriever
app/core/settings.py             # + ResilienceSettings
web/main.py                      # wrap dense with the lexical fallback
evals/fallbacks.py               # NEW: coverage benchmark + gate
evals/report.py; scripts/check_results.py; scripts/ci.sh
docs/degradation.md
tests/unit/test_resilience.py
```

## Design decisions

- **Wrap, don't branch inside.** `FallbackRetriever` implements `Retriever` and
  composes two, so the knowledge tool is unchanged and the fallback is testable
  in isolation.
- **Fail once, then stay down.** After the primary fails, the wrapper serves the
  secondary without retrying — deterministic and fast (no repeated timeouts).
- **Record, don't swallow.** Each failure appends a `Degradation`; a silent
  catch is forbidden (RD-1).
- **Config-gated.** `resilience.fallback_enabled=false` restores strict behavior
  so the fallback is a choice, not a hidden surprise.

## Complexity Tracking

> No violations; stdlib only.
