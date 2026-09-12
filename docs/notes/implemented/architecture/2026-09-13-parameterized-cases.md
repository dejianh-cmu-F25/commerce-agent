# Agent Note: Parameterized cases make the eval discriminate

Status: implemented (2026-09-13) — feature `024-parameterized-cases`

## Problem

The real-model eval used a handful of fixed, easy cases; the model passed all of
them (Pass@1/Pass@k/Pass^k = 1.000), so the metric could not distinguish models,
configs, or regressions. The book's answer is parameterized task generation.

## Alternatives considered

- **Keep the fixed cases.** They saturate; the metric is uninformative. Rejected.
- **Randomize parameters with an RNG.** Prevents memorization, but breaks
  reproducibility and paired comparison across seeds. Rejected.
- **Add more fixed hard cases.** Better, but still memorizable and not paired.
- **Parameterize with deterministic selection.** Chosen: `params[seed % n]` keeps
  runs reproducible and comparable while varying the concrete task.

## Decision

- **Templates + `build_cases(seed)`.** Six templates (budget search, multi-item
  cart, add named item, policy question, out-of-window refusal, ungrounded id)
  instantiate concrete cases per seed; the template **name** is stable so
  reliability aggregates across parameter variants.
- **Outcome predicates, not prose.** The predicate supports a maximum rendered
  price, a minimum cart size, forbidden components, and an empty-cart
  requirement; the only string check is a topic keyword in the policy case.
- **Outcome failures are attributed as `incomplete`.** When a run fails the
  predicate without a tool error, the first-error attribution is "incomplete"
  (the task was not completed), distinct from tool/grounding/policy errors.

## Consequences

- The metric now discriminates: a DeepSeek run over 6 templates × 3 seeds scored
  Pass@1 0.778 / Pass@k 0.833 / Pass^k 0.667, with the multi-item cart failing
  consistently and the budget search failing on one variant — real signal.
- Parameter variants are small and hand-curated; broader generation and a
  per-difficulty breakdown are the next step.
- The keyless gate is unaffected; the real runner remains opt-in and
  budget-capped.
