# Feature Specification: Web Trace Viewer

**Feature Branch**: `008-trace-viewer`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add a web Trace Viewer: a Chat/Traces toggle in the header, a list of
recent traces from `GET /traces`, and a turn/step/tool span timeline with
durations, status and redacted attributes from `GET /traces/{id}`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Browse recent traces (Priority: P1)

An operator switches to the Traces view and sees the recent traces with their
duration, span count, and status.

**Why this priority**: OB-4; traces are useless if they can only be read with
curl.

**Independent Test**: With traces on disk, open the Traces view and assert the
list shows a trace with its duration and span count.

**Acceptance Scenarios**:

1. **Given** at least one trace, **When** the Traces view opens, **Then** the
   list shows each trace's short id, duration, span count, and status.

---

### User Story 2 - Inspect a trace timeline (Priority: P1)

Selecting a trace shows its spans as a timeline: the `turn` root and its `llm`
and `tool` children, each with duration, status, and attributes.

**Independent Test**: Select a trace and assert the spans render in order with
parent/child indentation and their attributes.

**Acceptance Scenarios**:

1. **Given** a selected trace, **When** it loads, **Then** the `turn` span is
   shown with its `llm`/`tool` children indented and ordered by start time.
2. **Given** a span, **When** it renders, **Then** its duration and status are
   visible, and attributes (tokens, cost, tool name) are shown.

---

### User Story 3 - Refresh and empty states (Priority: P2)

The view can be refreshed, and an empty or failing backend shows a clear state.

**Independent Test**: With tracing disabled, assert the empty state; refresh
reloads the list.

**Acceptance Scenarios**:

1. **Given** no traces, **When** the view opens, **Then** a "no traces yet"
   message is shown.
2. **Given** the list is shown, **When** Refresh is clicked, **Then** the list
   reloads.

### Edge Cases

- The trace file is missing: the list is empty (not an error).
- A trace id disappears between list and select: show a not-found message.
- Very long attribute values: truncated by the backend (OB-5) and wrapped in the UI.
- The Chat view is unchanged by the toggle.

## Requirements *(mandatory)*

- **FR-001**: The header MUST offer a Chat/Traces toggle; Chat is the default.
- **FR-002**: The Traces view MUST list recent traces from `GET /traces`
  (short id, duration, span count, status, relative time).
- **FR-003**: Selecting a trace MUST fetch `GET /traces/{trace_id}` and render a
  timeline ordered by `start_ms`, indented by `parent_id`.
- **FR-004**: Each span MUST show its name, duration, status, and attributes.
- **FR-005**: The view MUST handle empty (no traces) and error states.
- **FR-006**: The view MUST offer a Refresh action.
- **FR-007**: Switching views MUST NOT change the chat (the transcript and
  composer are preserved).
- **FR-008**: The Traces view MUST be responsive and theme-aware (WV-7/WV-8).

### Key Entities

- **TraceSummary**: `trace_id`, `start_ms`, `duration_ms`, `span_count`, `status`.
- **Span**: `trace_id`, `span_id`, `parent_id`, `name`, `start_ms`, `end_ms`,
  `status`, `attributes`.

## UI Requirements

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Traces: loading | View opened / refresh | "Loading traces…" |
| Traces: empty | No traces | "No traces yet — send a message." |
| Traces: list | Traces exist | Rows with id, duration, spans, status |
| Trace: detail | A trace selected | Span timeline with attributes |
| Traces: error | Fetch fails | Inline message; Refresh available |
| Chat | Toggle to Chat | Unchanged transcript + composer |

## Web Acceptance

Send a message, switch to **Traces**: the turn's trace is listed; selecting it
shows the `turn` span with `llm`/`tool` children and their durations/attributes.
Switch back to **Chat**: the transcript is intact.

## Observability

This feature renders the observability data produced by 007 (OB-4). No new
backend events.

## Success Criteria *(mandatory)*

- **SC-001**: The Traces view lists recent traces and shows a selected trace's
  spans (turn/llm/tool) with durations and status.
- **SC-002**: An empty trace store shows the empty state; a fetch error shows an
  error state; Refresh reloads.
- **SC-003**: Toggling views preserves the chat transcript and composer.
- **SC-004**: The view is usable at 375px and follows the theme.

## Assumptions

- 007 provides `GET /traces` and `GET /traces/{trace_id}`.
- No router is added; the view is a client-side toggle (a single page).
- The viewer is read-only.

## Real-World Coverage

- **Input distribution**: recent traces from the tracer.
- **Data quality**: renders the recorded spans; nothing is fabricated.
- **Edge & failure modes**: no traces -> empty state; a fetch error -> inline error.
- **Scale envelope**: a list limit; not measured (gap).
- **Degradation**: read-only; the chat is preserved when switching views.
- **Change evidence**: browser checkpoint (008).
