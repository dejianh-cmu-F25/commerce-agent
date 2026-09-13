# Agent Note: The non-English retrieval gap is measured

Status: implemented (2026-09-13) — feature `040-multilingual-retrieval`

## Problem

The audit named non-English coverage "thin" and later "not measured". An
unmeasured gap is a claim, not evidence — RW-1 asks for the real-world input
distribution to be measured, not assumed.

## Alternatives considered

- **Add non-English queries to the gated retrieval set.** The keyless lexical
  retriever cannot cross languages, so the English hit-rate threshold would fail
  for a reason the change cannot fix. Rejected.
- **Fix it now (multilingual embeddings).** A larger change with a new dependency;
  out of scope for a measurement feature. Deferred.
- **Measure the multilingual set separately and label it a gap.** Chosen.

## Decision

- **`MULTILINGUAL_SET`** (`evals/retrieval_set.py`): 8 policy queries in Spanish,
  French, German, and Chinese, each with an expected English source.
- **`evals/bench.py`** measures it with the keyless TF-IDF retriever and stores
  `multilingual` (with `gated: false`).
- **The report** renders it explicitly as "not gated — a measured gap", and
  `docs/clarify-vs-refuse.md` / `docs/edge-cases.md` state the measured value.

## Consequences

- The gap is now a number: **0.000** hit-rate@3 for es/de/zh, **0.500** for fr (a
  loanword overlap), over the English corpus. The English gate is unchanged.
- Closing the gap (multilingual embeddings) is a future feature with a clear
  before/after to measure against.
- **Residual**: the set is small (8 queries) and the corpus is English-only.
