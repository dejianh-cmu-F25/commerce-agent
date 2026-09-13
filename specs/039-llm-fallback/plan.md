# Implementation Plan: LLM Provider Fallback

**Branch**: `039-llm-fallback` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `FallbackLLM` to `app/core/resilience.py`, `llm.fallback_*` settings, wire it
in `build_llm`, and add a keyless benchmark case.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RD-1 | the LLM dependency has a config-gated fallback | PASS |
| PB-1 | `llm.fallback_provider` selects it | PASS |
| P3 | no side effect; a mid-stream failure propagates | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
app/core/resilience.py       # + FallbackLLM
app/core/settings.py         # + llm.fallback_*
web/main.py                  # wrap when fallback_provider is set
evals/fallbacks.py           # + llm_fallback case
docs/degradation.md          # update the LLM row
tests/unit/test_resilience.py
```

## Design decisions

- **Fallback only before the first event.** Once a delta is sent it cannot be
  un-sent; a mid-stream failure must surface, not silently switch. This is the
  honest boundary.
- **Separate configuration.** The fallback is another provider/model/key; it is
  off unless configured, so the default path is unchanged.
- **Reuse `Degradation`.** The LLM fallback records the same shape as the
  retriever fallback (component/primary/fallback/reason).

## Complexity Tracking

> No violations; stdlib only.
