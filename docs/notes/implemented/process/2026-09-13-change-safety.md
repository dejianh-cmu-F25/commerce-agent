# Agent Note: Every change states its blast radius and rollback

Status: implemented (2026-09-13) — feature `032-change-safety`

## Problem

SC-4 requires the blast radius and the migration/rollback path to be stated, but
the PR template only had a checkbox ("Blast radius and rollback stated") and no
change actually recorded either. A reviewer could not tell what a change could
touch or how to undo it — the safety property was asserted, not enforced.

## Alternatives considered

- **A checkbox in the PR template.** Not enforced; a box is ticked without a
  statement. Rejected as the only mechanism.
- **A per-spec field.** SC-4 is a property of a *change*, not a spec; a spec can
  ship many changes. Rejected.
- **Fields on every change-log entry, gated.** Chosen — the change log is already
  the per-change auditable record (EV-6).

## Decision

- **`blast_radius` and `rollback` are now fields on every change-log entry**;
  `scripts/check_results.py` requires them on all entries and
  `scripts/check_change_evidence.py` on the current one.
- **Backfilled, not grandfathered.** Every existing entry was given an honest
  value derived from its area/evidence, so the invariant holds for the whole
  corpus and `tests/unit/test_change_log.py` enforces it.
- **The report renders both columns**, and `docs/change-safety.md` states the
  seam map (ports/adapters) and the rollback policy (revert + rebuild; additive
  SQLite schema).
- **The PR template asks for a written statement**, not just a tick.

## Consequences

- A change cannot merge without saying what it can affect and how to undo it.
- The rollback story is uniform and honest: `git revert` + rebuild, with no
  destructive migration in the current design.
- **Residual gap**: there is no automated rollback (no canary/blue-green); a
  future destructive migration must state its reverse explicitly.
