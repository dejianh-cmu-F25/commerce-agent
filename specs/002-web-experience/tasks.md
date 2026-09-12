# Tasks: Web Experience

**Feature**: `002-web-experience` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable (different files, no dependency).

## Phase 1 — Backend seam (tool-declared UI component)

- [x] T001 Extend `ToolResult` with optional `component` + `payload` in `app/tools/registry.py`
- [x] T002 Emit `UIComponent` from `app/core/loop.py` when a tool declares a component
- [x] T003 Set `component="products"` + items payload in `app/tools/catalog.py`
- [x] T004 [P] Unit test in `tests/unit/test_loop.py`: a component-declaring tool emits `UIComponent`

## Phase 2 — Assets and structure

- [x] T005 Vendor pinned `marked` and `DOMPurify` under `web/static/vendor/`
- [x] T006 [P] Extract styles to `web/static/styles.css` (tokens, light/dark, reduced-motion)
- [x] T007 [P] Update `web/static/index.html`: landmarks, `aria-live`, suggestions, budget meter, Stop, scroll-to-bottom, favicon
- [x] T008 [P] Add `web/static/favicon.svg` (fixes the 404)

## Phase 3 — Client behavior (US1, US2, US3, US4)

- [x] T009 `app.js`: explicit turn state machine (`idle/submitted/streaming/ready/error`)
- [x] T010 `app.js`: Stop via `AbortController`; partial reply retained
- [x] T011 `app.js`: markdown render via `marked` + `DOMPurify`; links `rel="noopener noreferrer"`
- [x] T012 `app.js`: tool calls as steps with status + disclosure
- [x] T013 `app.js`: sources from `UIComponent(products)` through the component registry
- [x] T014 `app.js`: suggestion chips seed the input (no auto-send)
- [x] T015 `app.js`: budget meter + latest-turn cost
- [x] T016 `app.js`: copy message; inline error + Retry
- [x] T017 `app.js`: autoscroll while pinned; "scroll to bottom" control
- [x] T018 `app.js`: `aria-live` announcements; Esc stops; visible focus

## Phase 4 — Verification and delivery

- [x] T019 Run `ruff`, `ruff format --check`, `pyright`, `pytest`
- [x] T020 Browser checkpoint (Playwright): Web Acceptance path + `checkpoint.png` + `checkpoint.md`
- [x] T021 Run `spec_review.py 002-web-experience` and `verify_notes.py`; add an Agent Note if needed
- [x] T022 Commit and open the PR

## Dependencies

- Phase 1 (T001–T004) precedes Phase 3 sources work (T013).
- Phase 2 (T005–T008) precedes Phase 3.
- T019–T022 follow all implementation.
