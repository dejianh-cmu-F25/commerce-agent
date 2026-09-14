# Agent Note: Two-layer evaluation of the post-purchase agent

Status: implemented (2026-09-14) — feature `045-post-purchase-pivot`

## Problem

A single "accuracy" number hides the failures that matter. The agent could score
well on labeled decisions and still crash on a weather question, leak the prompt,
or act on another customer's order. The project needed an evaluation that measures
**both** "is the answer correct?" and "does the property always hold?", and it
needed real numbers, not mock ones.

## Alternatives considered

- **One aggregate accuracy metric.** Simple, but blind to behavioral failures
  (the Replit-class incidents are not accuracy failures). Rejected.
- **LLM-as-judge for everything.** Expensive, itself non-deterministic, and it
  cannot check "no tool was called". Rejected for the invariant layer.
- **Deterministic assertions for invariants + labeled cases for decisions.** Chosen.
- **Mock-only evaluation.** Produces numbers that prove nothing about the model.
  Rejected: the real run is the evidence; the keyless run is a harness self-test.

## Decision

- **Two corpora, two metrics.** `evals/post_purchase_cases.jsonl` (16 labeled
  decisions → `decision_accuracy`, `policy_citation_support`) and
  `evals/invariant_cases.jsonl` (17 behavioral cases → `invariant_pass_rate`,
  `no_fail_rate`).
- **The model proposes, the harness disposes.** The agent calls
  `propose_return_decision` (no side effect); the deterministic
  `app.returns.eligibility.decide_return` is the verifier, and its agreement with
  the human labels is reported (11/13) as a check on both.
- **Real model, budget-metered.** `--real` runs DeepSeek through the existing cost
  meter; the run costs ≈CNY 0.20 and the numbers live in
  `reports/post-purchase-eval.md`.
- **Failures are the point.** The first run found three real defects — tenancy
  (INV-7), an unmodeled warranty path, and a policy-override injection the guard
  misses — each recorded as a next action.

## Consequences

- The project now reports honest, two-layer evidence: decision accuracy 13/16,
  invariant pass 16/17, no-fail 1.000.
- The failures are specific and actionable, which is more valuable than a high
  score: tenancy and the warranty boundary are now first-class work items.
- **Residual**: the corpora are small (16 + 17); the tenancy fixture is simplified
  (a foreign order is absent rather than owned by another customer); the async
  client emits a cosmetic shutdown warning.
