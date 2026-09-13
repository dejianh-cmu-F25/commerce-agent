# Agent Note: The LLM has a config-gated provider fallback

Status: implemented (2026-09-13) — feature `039-llm-fallback`

## Problem

RD-1 requires a fallback per external dependency, but the LLM had none: a
provider outage surfaced an error turn even when a second provider was available.
The audit listed this as the last RD-1 residual.

## Alternatives considered

- **Retry the same provider.** Does not help an outage; still fails. Rejected.
- **Fall back at any point in the stream.** Impossible: a delta already sent
  cannot be un-sent, so a mid-stream switch would produce a garbled answer.
  Rejected.
- **Fall back only before the first event, to a separately configured provider.**
  Chosen.

## Decision

- **`FallbackLLM`** (`app/core/resilience.py`) wraps a primary and a secondary
  client: if the primary raises **before emitting**, the secondary serves the
  stream and a `Degradation` is recorded; if the primary raises **after** a delta,
  the error propagates (the honest boundary); a failed primary is not retried.
- **Config-gated**: `llm.fallback_provider` (empty = off) plus
  `fallback_model`/`fallback_base_url`/`fallback_api_key`. Off by default because
  a second provider is a real credential/cost choice.
- **Wired in `build_llm`**; the keyless benchmark gains two cases (`llm_fallback`,
  `llm_midstream_propagates`), taking coverage from **0.286** to **1.000**.

## Consequences

- A provider outage before the first token now serves the answer from the
  configured fallback instead of failing the turn; the degradation is observable.
- A mid-stream outage still surfaces — a partial answer is never silently mixed
  with a fallback's.
- **Residual gaps**: the fallback is off unless configured; degradations are
  recorded in-process, not exported as a counter.
