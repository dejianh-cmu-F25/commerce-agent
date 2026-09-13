# Agent Note: Clarify on ambiguity; guard non-English injection

Status: implemented (2026-09-13) — feature `038-clarify-multilingual`

## Problem

Two RW-1 residuals: (1) the specs did not state how the agent should **clarify**
an ambiguous request versus refuse it — an agent that guesses can write to a cart
on a vague request; (2) the input guard and the eval sets were English-only.

## Alternatives considered

- **Let the model decide ambiguity.** No policy, no assertion. Rejected.
- **Refuse anything ambiguous.** Unhelpful; a clarifying question is the right
  outcome. Rejected.
- **Add multilingual patterns to the same lexical guard.** Chosen — cheap, keyless,
  and it reuses the normalization.

## Decision

- **`config/prompts/system.md`** now instructs: ask one clarifying question when a
  detail needed to act is missing, take no action, and stay in scope.
- **Gold scenario `ambiguous_request_clarifies`** asserts an empty tool list on
  "I want the cheaper one", so a regression that guesses fails the gate.
- **`app/safety/input_guard.py`** gains instruction-override patterns in Spanish,
  French, German, and Chinese; the adversarial set grows to 23 cases (4 new
  injection, 2 new benign), keeping the safe-handling rate at 1.000.
- **`docs/clarify-vs-refuse.md`** documents the three outcomes (clarify / refuse /
  act) and where each is enforced.

## Consequences

- An ambiguous request is clarified with no side effect; the guard refuses common
  override phrasing in five languages.
- **Residual gaps** (documented): the clarify policy is asserted by one scenario;
  non-English *retrieval* quality is not measured; the guard remains lexical.
