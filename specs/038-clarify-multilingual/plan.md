# Implementation Plan: Clarify-vs-Refuse & Multilingual Guard

**Branch**: `038-clarify-multilingual` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add clarify rules to the system prompt, a gold scenario asserting no action on
ambiguity, multilingual injection patterns to the input guard, multilingual
labeled cases, and a policy doc.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| RW-1 | clarify-vs-refuse specified; language coverage widened | PASS |
| P3 | an ambiguous request triggers no side effect | PASS |
| P4 | the guard refuses without revealing the prompt | PASS |
| P6 | stdlib only | PASS |

## Project Structure

```text
config/prompts/system.md         # + clarify / scope rules
evals/scenarios.py               # + ambiguous_request_clarifies
app/safety/input_guard.py        # + es/fr/de/zh injection patterns
evals/adversarial_set.py         # + multilingual cases
docs/clarify-vs-refuse.md        # the policy
tests/unit/test_input_guard.py   # multilingual cases
```

## Design decisions

- **Clarify is a policy, not a new mechanism.** The harness already supports a
  text-only turn; the prompt states the rule and a gold scenario asserts it.
- **Multilingual patterns, not translation.** Add the override phrasing in the
  target languages to the same guard; NFKC + lowercase handle accents/case.
- **Keep the guard honest.** The residual (a novel paraphrase can evade a lexical
  guard) stays documented.

## Complexity Tracking

> No violations; stdlib only.
