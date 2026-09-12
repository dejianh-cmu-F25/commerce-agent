# Implementation Plan: Gates

**Branch**: `020-gates` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

## Summary

Add `app/gates/` with `GateResult`, `Gate`, `GateContext`, `ProvenanceGate`,
`ReturnEligibilityGate`, and `GatePipeline`; refactor `app/tools/cart.py` and
`app/tools/orders.py` to use them, preserving outputs. Behavior-preserving.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P3 model proposes, harness disposes | guardrails are decision-only; no mutation | PASS |
| P4 grounding | provenance gate centralizes the server-issued-id rule | PASS |
| PB-2 capability seam | gates are a module with a pipeline | PASS |
| P6 simplicity | one small module; no generic framework | PASS |
| RD-1 | gates return reasons; tools map them to the same errors | PASS |

## Project Structure

```text
app/gates/base.py       # GateResult, Gate, GateContext
app/gates/provenance.py # ProvenanceGate
app/gates/returns.py    # ReturnEligibilityGate
app/gates/pipeline.py   # GatePipeline
app/tools/cart.py, app/tools/orders.py   # use the gates
tests/unit/test_gates.py
docs/architecture.md; Agent Note
```

## Design decisions

- **A shared context, a tiny pipeline.** `GateContext` carries the session and the
  few values gates need; `GatePipeline.run` returns the first block. No generic
  framework (P6).
- **Decision-only gates.** Gates never mutate; tools keep ownership of side
  effects and of the exact output shape.
- **Same outputs.** The tools map a block to the identical JSON/status as before,
  so the refactor is invisible to tests and evals.

## Complexity Tracking

> No violations. A behavior-preserving extraction; no new dependency.
