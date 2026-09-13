# Agent Note: Guardrails are trended over recorded runs

Status: implemented (2026-09-13) — feature `042-guardrail-history`

## Problem

EV-3 requires regressions to be visible. The guardrail floors (feature 036) catch
a drop *below* the minimum, but a slow drift toward the floor is invisible without
history. The residual was named: "no per-guardrail trend history".

## Alternatives considered

- **Record on every gate run.** Would dirty the working tree on every push and
  produce meaningless repeated entries. Rejected.
- **Explicit `--record` after a meaningful run, with a committed history.**
  Chosen: the gate validates, a human records.

## Decision

- **`evals/guardrail-history.jsonl`** is an append-only, capped (50-entry) record:
  one `{date, metrics}` object per recorded run.
- **`evals/guardrails.py --record`** appends the current values; the gate runs
  without it, so a normal run never writes.
- **The report shows the delta** vs the previous recorded entry; the first run
  shows `—`.
- **`docs/guardrails.md`** documents the recording policy.

## Consequences

- A drift is now visible: the report shows `Δ prev` per guardrail, so a metric
  moving toward its floor over releases is caught before it breaches.
- The committed file stays small (capped), and the gate remains side-effect-free.
- **Residual**: recording is manual (no scheduler after each release).
