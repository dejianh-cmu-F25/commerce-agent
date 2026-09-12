# Feature Specification: Eval Report View

**Feature Branch**: `025-eval-report-view`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add a browser **Report** view that renders the committed
`evals/report.md` (retrieval benchmark, feature ablation, real-model reliability,
process metrics, cost, judge) via `GET /report`, with full UI states.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Read the evaluation report in the browser (Priority: P1)

A reviewer opens the Report view and reads the evaluation report — the retrieval
benchmark, the feature ablation, and (when a real run has been made) the
reliability, process, cost, and judge sections — without leaving the app.

**Why this priority**: The numbers that justify the harness (and the resume) are
in `evals/report.md`; surfacing them makes the evidence visible where the rest of
the demo lives.

**Independent Test**: `GET /report` returns the report markdown; the view renders
it.

**Acceptance Scenarios**:

1. **Given** a committed report, **When** the Report view opens, **Then** it
   renders the report markdown (headings, tables).
2. **Given** no report file, **When** the view opens, **Then** it shows an empty
   state explaining how to generate one.

---

### User Story 2 - Read-only and safe (Priority: P2)

The view is read-only and renders markdown through the sanitizing renderer.

**Independent Test**: The endpoint returns text only; the renderer sanitizes.

**Acceptance Scenarios**:

1. **Given** the report, **When** it contains a script tag, **Then** it is not
   executed (Streamdown sanitizes).

---

### Edge Cases

- **Missing report**: empty state with the generating command.
- **Fetch error**: inline error with Retry.
- **Large report**: the view scrolls within its container.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The web MUST expose `GET /report` returning the committed
  `evals/report.md` content (or an empty string when absent).
- **FR-002**: The UI MUST provide a Report view that renders the markdown through
  the sanitizing renderer (WV-9).
- **FR-003**: The UI MUST define empty, loading, success, and error states
  (WV-6).
- **FR-004**: The view MUST be read-only and keyboard-scrollable.

### Key Entities

- **Report**: the committed markdown artifact rendered in the browser.

## UI Requirements *(when the feature is browser-visible; WV-6..WV-8)*

A new **Report** view (a tab beside Chat / Traces / Merchant / Memory / Scenarios
/ Metrics).

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | No report file | A line with the command to generate one (`evals/report.py --write`) |
| Loading | The report is being fetched | A "Loading…" line |
| Success | The report is loaded | The rendered report (headings, tables) |
| Error | The fetch fails | An inline error with Retry |
| Disabled | Not applicable (read-only) | — |

### Accessibility

- [ ] The Report tab is keyboard-operable with a visible focus ring.
- [ ] Content is announced when it loads (`aria-live`).
- [ ] Motion respects `prefers-reduced-motion`.

### Responsive & Theme

- [ ] The report sits in the fluid column; wide tables scroll inside their container with no page-level horizontal scroll from 375px up.
- [ ] Theme follows `prefers-color-scheme`.

## Web Acceptance

- The header exposes a **Report** tab; selecting it renders `evals/report.md`.
- With no report, the view shows the generating command.

## Observability

- The view reads the committed artifact; no new span. The report itself records
  the model, seeds, and command.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The Report view renders the committed report's headings and tables.
- **SC-002**: A missing report yields the empty state, not an error.
- **SC-003**: No page-level horizontal scroll at 375px.
- **SC-004**: The local gate passes.

## Assumptions

- The report is a static committed artifact; the view does not regenerate it.
- Rendering reuses the existing sanitizing markdown renderer.
