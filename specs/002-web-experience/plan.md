# Implementation Plan: Web Experience

**Branch**: `002-web-experience` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/002-web-experience/spec.md`

## Summary

Turn the bare chat surface from feature 001 into a trustworthy, accessible,
theme-aware experience: render assistant markdown safely, show tool calls as
distinct steps with status, add streaming status with Stop/Retry, suggestion
prompts, a sources/provenance area, a budget meter, and responsive light/dark
styling — all as a **no-build, vanilla-JS** surface with a small component
registry (WV-3, P6, HR-9). Third-party libraries (markdown + sanitizer) are
**vendored at pinned versions** for offline reproducibility (P8, DP-4).

## Technical Context

**Language/Version**: Python 3.13 (backend, unchanged) + JavaScript ES2020
(browser, no build step)

**Primary Dependencies**: FastAPI + sse-starlette (existing backend);
**vendored** `marked` (markdown) and `DOMPurify` (sanitize) under
`web/static/vendor/`

**Storage**: N/A (no new persistence; provenance is derived from the session log)

**Testing**: `pytest` for any backend touch; a scripted **browser checkpoint**
(Playwright) for the UI; existing `spec_review.py` gate

**Target Platform**: modern desktop and mobile browsers (≥ 375px)

**Project Type**: web service with a static frontend

**Performance Goals**: first token unchanged from 001; UI interactions ≤ 200ms;
no layout shift on stream

**Constraints**: no build step; offline-reproducible; all model-derived markup
sanitized before it enters the DOM (WV-9)

**Scale/Scope**: single-user demo; one surface (`web/static/`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Clause | Check | Result |
| --- | --- | --- |
| P6 / HR-9 (simplicity, minimal scaffolding) | vanilla JS, vendored libs, no framework | PASS |
| P8 / DP-4 (reproducible, offline) | vendored pinned libs; no CDN | PASS |
| WV-1 / WV-6 (web acceptance + UI states) | spec has `## Web Acceptance`, `## UI States` | PASS |
| WV-3 (component registry) | new types registered; generic fallback kept | PASS |
| WV-7 / WV-8 (a11y, responsive, theme) | specified and tested in checkpoint | PASS |
| WV-9 (rendering safety) | DOMPurify before DOM insertion | PASS |
| P4 (grounding) | sources come from session provenance only | PASS |
| HR-12 (budgets) | budget meter reflects usage events | PASS |
| SL-1 (log is truth) | UI renders events only; no client-side model context | PASS |

No violations — Complexity Tracking is empty.

## Project Structure

### Documentation (this feature)

```text
specs/002-web-experience/
├── plan.md              # this file
├── research.md          # vendoring + pattern decisions
├── data-model.md        # UI-side view model
├── quickstart.md        # how to run and check
├── contracts/
│   └── ui.md            # event -> component/state contract
└── tasks.md             # /speckit-tasks output
```

### Source Code (repository root)

```text
web/
├── main.py                 # unchanged unless provenance needs a field
├── sessions.py
└── static/
    ├── index.html          # structure + ARIA landmarks
    ├── styles.css          # extracted styles; light/dark; reduced-motion
    ├── app.js              # state machine, SSE, registry, rendering
    └── vendor/
        ├── marked.min.js   # pinned
        └── purify.min.js   # pinned (DOMPurify)
```

**Structure Decision**: Extend the existing `web/static/` surface (single
project). Styles move from inline `<style>` to `styles.css` so theming and
reduced-motion are reviewable. Vendor files are committed so the container and
offline runs need no network.

## Complexity Tracking

> No constitution violations; nothing to justify.
