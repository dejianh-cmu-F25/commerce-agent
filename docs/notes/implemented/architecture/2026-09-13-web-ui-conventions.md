# Agent Note: Web UI conventions and rendering safety

Status: implemented (2026-09-13)

## Problem

Spec Kit's `spec-template.md` has no UI section, so browser-visible behavior was
under-specified: feature 001 shipped a web surface whose only stated acceptance
was a happy-path sentence. The first browser checkpoint then found the page
rendered nothing (an SSE separator bug) — exactly the kind of gap a UI-state and
accessibility convention would have surfaced earlier. We also had no rule for
rendering model-derived markdown safely.

## Decision

Add a UI convention to the constitution and templates:

- Constitution **WV-6..WV-9**: UI states must be enumerated; interactive UI must
  be accessible; layout must be responsive and follow the system theme;
  model/user-derived markup must be sanitized before it enters the DOM.
- `spec-template.md` gains a `## UI Requirements` section (UI States,
  Accessibility, Responsive & Theme).
- `docs/ui-conventions.md` holds the guide, the curated review checklist, and
  the rendering-safety rule.
- `scripts/spec_review.py` gains an AUTO check: a spec with `## Web Acceptance`
  must also declare `## UI States`.

The frontend stays **vanilla JS with a component registry** (WV-3) and no build
step. Where a library helps (markdown), we will **vendor a pinned copy** rather
than pull from a CDN, so the app stays offline-reproducible (P8, DP-4).

## Alternatives considered

- **Adopt a React chat framework** (assistant-ui, AI Elements, CopilotKit).
  Rejected: introduces a build toolchain and a runtime dependency for a demo
  whose value is the harness, not the frontend. Violates P6 and HR-9.
- **Load markdown from a CDN** (e.g., jsDelivr `marked`). Rejected: breaks
  offline reproducibility and container builds; adds a network dependency at
  runtime.
- **No UI convention; rely on review.** Rejected: 001's checkpoint already
  demonstrated that undocumented UI states and separators slip through.
- **Make the UI-states check MANUAL instead of AUTO.** Rejected: a cheap,
  deterministic check is a better sensor (HR-3); it costs nothing and catches a
  real omission.

## Consequences

- New browser-visible specs must enumerate states, accessibility, and responsive
  behavior; `spec_review.py` blocks a PR that omits `## UI States`.
- Feature 001's spec was retrofitted with a `## UI States` section to keep CI
  green and to demonstrate the convention.
- Feature 002 (web experience) will follow this convention and vendor `marked`
  + `DOMPurify` under `web/static/vendor/`.
- Constitution version moves 1.0.0 → 1.1.0; changes go through a PR (Governance).
