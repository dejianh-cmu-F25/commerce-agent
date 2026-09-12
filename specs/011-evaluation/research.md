# Research: Evaluation Harness

## D1. Replay engine

**Decision**: reuse `MockLLMClient` (a scripted list of turns). A scenario's
`turns` are the model's responses, one per `stream` call.

**Rationale**: already used by tests; deterministic and keyless (TT-2).

## D2. What to assert

**Decision**: tool-call sequence, rendered component types, and cart state only.
Never model prose (TT-2).

**Rationale**: prose is non-deterministic in general; the harness behaviour is
what matters.

## D3. Isolation per scenario

**Decision**: each scenario gets a fresh in-memory storefront and a fresh temp
SQLite merchant, so scenarios cannot affect each other.

## D4. Gating

**Decision**: `scripts/ci.sh` runs `python evals/run.py`; a `pytest` wrapper runs
the same suite so it is also covered by the unit/integration tier.

## D5. Location

**Decision**: a top-level `evals/` package (referenced by the PR template),
not under `app/`.

**Rationale**: it is a development artifact, not shipped code.
