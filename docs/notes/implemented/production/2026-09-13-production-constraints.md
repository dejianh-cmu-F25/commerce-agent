# Agent Note: Production constraints are constitution clauses, checked by the gate

Status: implemented (2026-09-13) — constitution v1.3.0

## Problem

The project was strong at being *demonstrable* and weak at being *dependable*:
it had evaluation infrastructure (features 022–024) but nothing required a
feature to cover real phrasing, dirty data, or scale, and nothing required a
model/prompt/module change to prove it improved things. The risks were concrete:
a demo that collapses under real traffic, problems that surface only at scale and
cannot be localized, and changes justified by reputation rather than evidence.

## Alternatives considered

- **Leave these as informal review comments.** They evaporate; nothing enforces
  them, and the project drifts back to demo-quality. Rejected.
- **One giant "production readiness" document.** A checklist with no teeth and no
  per-feature obligation; it would be read once and ignored. Rejected.
- **A new feature spec per concern.** Wrong layer: these are cross-cutting,
  non-negotiable quality attributes, which is exactly what the constitution is
  for. Rejected.
- **New constitution clauses + a template section + gate checks + a checklist
  doc**, mirroring the existing WV pattern. Chosen.

## Decision

- **Three constitution clauses: RW / SC / EV** (the constitution is the normative
  source). RW = Real-World Fitness, SC = Scale & Operability, EV =
  Evidence-Backed Change. The definition of done for a change now requires an
  auditable change-log entry with a quantified before/after (EV-1 / EV-6).
- **A spec template section** `## Real-World Coverage` makes the per-feature
  obligation concrete.
- **A checklist doc** `docs/production-conventions.md`, the sibling of
  `docs/ui-conventions.md`.
- **Gate checks:** `spec_review.py` requires `## Real-World Coverage` for features
  that touch inputs/data/model/retrieval, and `scripts/check_change_evidence.py`
  requires evidence when the model/prompt/retrieval surface changes.
- **A new Agent Note class** `production`.
- **An honest audit** `docs/production-audit.md` applies the clauses to the
  project and names the gaps (RW-2, SC-1, SC-3 are the biggest).

## Consequences

- Features can no longer be "done" as happy-path demos; the spec must address the
  real world, and changes must carry evidence.
- The project can now state its own production gaps instead of discovering them
  in production — the audit lists them and a roadmap orders them.
- The clauses add process weight; proportionality is preserved by keeping the
  hard checks narrow (section presence, evidence presence) and the semantic
  judgments MANUAL in the PR checklist.
- RW-2 (data quality), SC-1 (scale envelope), and SC-3 (SLOs) are explicit gaps,
  tracked in `docs/production-audit.md`.
