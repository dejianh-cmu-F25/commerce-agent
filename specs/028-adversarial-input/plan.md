# Implementation Plan: Adversarial & Out-of-Distribution Input

**Branch**: `028-adversarial-input` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add a pure input guard (`app/safety/input_guard.py`), apply it in the agent loop
before the model call, plumb `safety` settings, and add a keyless labeled
benchmark rendered in the report. No new dependency.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RW-1 | hostile/OOD input has defined behavior before the model | PASS |
| P3 | a blocked turn has no side effects (no tool) | PASS |
| P4 | refusal is generic; the prompt is never revealed | PASS |
| SL-1 | the refusal is recorded in the log; context stays reconstructable | PASS |
| P6 | stdlib only (`re`, `unicodedata`) | PASS |

## Project Structure

```text
app/safety/input_guard.py        # NEW: normalize + classify
app/core/settings.py             # + SafetySettings
app/core/loop.py                 # apply the guard before the model call
web/main.py                      # pass settings.safety
evals/adversarial_set.py         # NEW: labeled hostile/benign inputs
evals/adversarial.py             # NEW: safe-handling benchmark + gate
evals/report.py                  # render the adversarial section
scripts/check_results.py; scripts/ci.sh
config/settings.yaml; .env.example
tests/unit/test_input_guard.py
tests/integration/test_adversarial_turn.py
docs/notes/implemented/production/...-adversarial-input.md
```

## Design decisions

- **Deterministic lexical guard, not a model.** Cheap, keyless, and runs before
  any spend (HR-12). A model classifier is a future option, not this feature.
- **Normalize before matching.** NFKC folds fullwidth homoglyphs; zero-width
  characters are stripped; whitespace is collapsed. This closes the cheap evasions.
- **Refuse, don't sanitize.** A blocked turn is recorded as an assistant refusal
  in the log (SL-1) and ends with a distinct reason; no model/tool call.
- **Measured against a naive baseline.** Without the guard every hostile case is
  allowed, so the before/after is honest.

## Complexity Tracking

> No violations; stdlib only.
