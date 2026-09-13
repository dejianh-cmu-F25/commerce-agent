# Agent Note: The edge/failure boundaries are enumerated and enforced

Status: implemented (2026-09-13) — feature `035-edge-cases`

## Problem

RW-3 requires edge and failure modes to be enumerated with a defined behavior
each. The specs had an `Edge & failure modes` bullet, but the coverage was uneven:
a reviewer had to reconstruct the cross-cutting boundary list per spec, and many
per-spec notes still said "not measured (gap)" long after the system envelope was
measured (feature 029). Nothing enforced that a spec actually enumerated its
boundaries.

## Alternatives considered

- **Rely on the spec template.** Presence of the section was checked; its content
  was not. Rejected — a section can be a heading and a shrug.
- **Enumerate boundaries per spec only.** Duplicated and inconsistent across 34
  specs. Rejected.
- **One canonical matrix + a content check.** Chosen.

## Decision

- **`docs/edge-cases.md`**: 16 cross-cutting boundaries (empty/oversized/
  adversarial input, unknown tool, malformed JSON, ungrounded id, dirty data,
  missing corpus, dependency failure, budget, return window, unapproved write,
  duplicate ingestion, concurrency, session restart), each with a defined
  behavior and an enforcement pointer.
- **`scripts/spec_review.py`** now fails a spec whose `## Real-World Coverage`
  omits any of the six bullets or leaves one empty (an explained `n/a (reason)`
  is allowed).
- **`tests/unit/test_spec_coverage.py`** enforces the six bullets on **every**
  spec, so the invariant holds corpus-wide.
- **Stale notes refreshed**: 20 per-spec "Scale envelope: not measured (gap)"
  lines now point at the measured `docs/scale.md`; 001/023's adversarial "gap"
  notes now reference the guard (028). Genuine gaps (JSONL rotation, non-English
  phrasing, large corpus) stay.

## Consequences

- A reviewer reads one matrix for the cross-cutting behavior and the spec for the
  feature-specific edges.
- A spec can no longer ship with an empty coverage bullet; the gate and the corpus
  test keep the enumeration honest.
- **Residual gaps** remain named in the matrix: multi-tenant isolation,
  long-session memory, large corpus, adversarial retrieval.
