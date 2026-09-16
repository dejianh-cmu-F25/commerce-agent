# Implementation Plan: Parameterized Eval Cases

**Branch**: `024-parameterized-cases` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Rewrite `evals/real_cases.py` as templates + `build_cases(seed)`; extend the
predicate in `evals/agent_eval.py` (max price, min cart size); aggregate
reliability per template. No new dependency.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P7 evals first-class | a more discriminating eval | PASS |
| P8 keyless default | real runner stays opt-in | PASS |
| HR-12 budgets | unchanged cap | PASS |
| TT-2 deterministic | `build_cases` is pure/reproducible | PASS |
| HR-11 | templates are data | PASS |

## Design decisions

- **Template name is the task id.** Parameters vary by seed, so reliability
  aggregates the template across its variants.
- **Outcome predicates, not prose.** Extend the predicate with `max_price` and
  `min_cart_items`; the only string check is a topic keyword in the policy case.
- **Deterministic selection.** `params[seed % len(params)]`; no RNG.

## Complexity Tracking

> No violations; no new dependency.
