# Feature Specification: Web Experience

**Feature Branch**: `002-web-experience`

**Created**: 2026-09-13

**Status**: Implemented
**Input**: Polish the browser chat experience: render assistant markdown safely,
show tool calls as distinct steps, add a streaming status with stop and retry,
suggestion prompts for the empty state, sources/provenance display, a budget
meter, and accessible, responsive, theme-aware styling.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Trustworthy, readable answers (Priority: P1)

A customer reads the agent's reply. Markdown is rendered (not shown as raw
`**`/`-`), each tool call appears as its own step with a status, and the
grounding sources for the answer are visible.

**Why this priority**: This is what makes the harness visible and the answer
credible; it directly serves grounding (P4) and the component registry (WV-3).

**Independent Test**: Send a message that triggers a tool call; assert the reply
renders formatted text, that a tool step with an `ok` status is present, and that
a sources area lists the grounded items — with no raw HTML executed.

**Acceptance Scenarios**:

1. **Given** a reply containing `**bold**`, a list, and a link, **When** it
   renders, **Then** the formatting is applied and the link opens in a new tab
   with `rel="noopener noreferrer"`.
2. **Given** the model requests a tool, **When** the tool starts and finishes,
   **Then** a single step shows its name, arguments, and a status that changes
   from running to ok (or error).
3. **Given** a reply grounded in products, **When** it completes, **Then** a
   sources area lists those products.
4. **Given** model output that contains a `<script>` or `onerror` attribute,
   **When** it renders, **Then** no script executes and the tag is neutralized.

---

### User Story 2 - Clear streaming and control (Priority: P1)

While the agent works, the customer sees what is happening and can stop it; when
something fails, they can retry.

**Why this priority**: Streaming without feedback feels broken; a stuck or failed
turn with no recovery is a dead end.

**Independent Test**: Send a message; assert a visible status transitions through
submitted and streaming to ready, that a Stop control cancels the request, and
that a forced error shows an inline message with a working Retry.

**Acceptance Scenarios**:

1. **Given** a request in flight, **When** text is streaming, **Then** a status
   indicator and a streaming caret are visible and Send is disabled.
2. **Given** a request in flight, **When** the customer presses Stop, **Then** the
   request is cancelled, the partial reply remains, and Send is re-enabled.
3. **Given** a request fails, **When** the turn ends, **Then** an inline error
   with Retry is shown; pressing Retry resends the last message.

---

### User Story 3 - Discoverability and budget awareness (Priority: P2)

A first-time customer sees example prompts instead of an empty screen, and can
see how much of the budget has been spent.

**Why this priority**: Improves first-run success and makes the spend guard
(HR-12) visible, without being required for a working chat.

**Independent Test**: On load, assert suggestion chips are present and clicking
one fills the input; after a turn, assert the budget meter reflects spend/limit.

**Acceptance Scenarios**:

1. **Given** no messages, **When** the page loads, **Then** suggestion chips are
   shown; clicking one fills the input (and does not auto-send).
2. **Given** a completed turn, **When** usage is reported, **Then** the budget
   meter shows spent vs limit and updates.

---

### User Story 4 - Accessible, responsive, theme-aware (Priority: P2)

The interface works with a keyboard and a screen reader, at phone width, and in
the user's light or dark system theme.

**Why this priority**: Required by WV-7/WV-8 and cheap to do while building;
retrofitting accessibility is expensive.

**Independent Test**: Tab through the UI to send a message; assert visible focus
and that streamed text is announced; resize to 375px; toggle the system theme.

**Acceptance Scenarios**:

1. **Given** keyboard focus, **When** the customer tabs and types, **Then** focus
   is always visible and Enter submits.
2. **Given** streaming text, **When** it updates, **Then** it is announced via an
   `aria-live` region.
3. **Given** a 375px viewport, **When** the page renders, **Then** the layout is
   usable with no horizontal scroll.
4. **Given** the OS is in light mode, **When** the page loads, **Then** it uses
   the light theme; dark mode uses the dark theme.

### Edge Cases

- The model streams a long reply: auto-scroll follows only while the user is at
  the bottom; otherwise a "scroll to bottom" control appears.
- A tool call returns an error: the step shows an error status; the turn still
  completes.
- The budget is exceeded: a clear inline notice appears; no further calls are made.
- The network drops mid-stream: the partial reply stays and an error with Retry
  is shown.
- A reply contains an image or a link with a `javascript:` URL: it is neutralized.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Assistant text MUST be rendered as a safe markdown subset (bold,
  italic, lists, links, inline code, fenced code) rather than shown raw.
- **FR-002**: All model- or user-derived markup MUST be sanitized before it enters
  the DOM; raw HTML and `javascript:` URLs MUST NOT execute (WV-9).
- **FR-003**: Each tool call MUST render as a single step showing the tool name,
  its arguments, and a status (running / ok / error), separate from prose.
- **FR-004**: The UI MUST display the grounding sources for a grounded answer.
- **FR-005**: The UI MUST expose a status reflecting the turn lifecycle:
  idle, submitted, streaming, ready, error.
- **FR-006**: While streaming, a caret MUST indicate progress and Send MUST be
  disabled.
- **FR-007**: A Stop control MUST cancel the in-flight request without clearing
  the partial reply.
- **FR-008**: A failed turn MUST show an inline error with a Retry action.
- **FR-009**: The empty state MUST offer suggestion prompts that seed the input.
- **FR-010**: The UI MUST show a budget meter (spent vs limit) updated from usage
  events, and the cost of the latest turn.
- **FR-011**: Each message MUST offer a copy action.
- **FR-012**: Interactive elements MUST be keyboard-operable with a visible focus
  ring; Enter MUST submit.
- **FR-013**: Streamed updates MUST be announced via an `aria-live` region.
- **FR-014**: Motion MUST respect `prefers-reduced-motion`; interaction animation
  MUST be ≤ 200ms.
- **FR-015**: The layout MUST be usable from 375px to desktop and MUST follow
  `prefers-color-scheme`.
- **FR-016**: New UI element types MUST be registered in the existing component
  registry (`component_type -> renderer`); the generic renderer remains the
  fallback (WV-3).
- **FR-017**: The frontend MUST remain a no-build, vanilla-JS surface; any
  third-party library MUST be vendored at a pinned version (P8, HR-9).

### Key Entities

- **TurnStatus**: `idle | submitted | streaming | ready | error`.
- **ToolStep**: `name`, `arguments`, `status`, `result?`.
- **Suggestion**: `label`, `prompt`.
- **Source**: `title`, `price`, `in_stock` (provenance-backed).
- **BudgetMeter**: `spent`, `limit`, `last_turn_cost`.

## UI Requirements

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | Page load, no messages | Suggestion chips; focused input; budget meter at `—` |
| Submitted | Message sent, before first token | User bubble; agent placeholder; status "Thinking…"; Send disabled; Stop shown |
| Streaming | First token received | Text appears with a caret; tool steps appear as they run; status "Responding…" |
| Success | Turn ends (`TurnEnd`) | Full formatted reply; sources; budget meter updated; Send enabled; Stop hidden |
| Error | `ErrorEvent` or network failure | Inline error with Retry; partial reply retained; Send enabled |
| Disabled | Input empty or request in flight | Send disabled; suggestion chips inert |

### Accessibility

- [ ] Keyboard-operable with a visible focus ring; Enter submits; Esc stops.
- [ ] Streamed text announced via `aria-live="polite"` (polite, not assertive).
- [ ] Tool steps use `aria-expanded` when collapsible; status has a text label,
      not color alone.
- [ ] Motion respects `prefers-reduced-motion`; text inputs are ≥ 16px.

### Responsive & Theme

- [ ] Usable at 375px and on desktop; no horizontal scroll.
- [ ] Theme follows `prefers-color-scheme` (light and dark).

## Web Acceptance

Open `/`, click a suggestion chip (or type "I need a tent under $250"), and press
Send. The reply streams with formatted text; a `search_products` step with an
`ok` status appears; a sources area lists the grounded product; the budget meter
updates. Press Stop during a turn to confirm cancellation, and trigger an error
to confirm Retry.

## Observability

The UI renders the existing `TurnStart`/`TurnEnd`/`UsageReported`/`ErrorEvent`
stream. No new backend events are required beyond what feature 001 emits; the
turn `trace_id` remains the link to `logs/traces.jsonl` (feature 007).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time user can send a message and see a formatted, grounded
  answer within the same time as feature 001 (no added round trips).
- **SC-002**: 100% of model-derived markup is sanitized: an injected `<script>`
  or `onerror` never executes in an automated check.
- **SC-003**: All interactive controls are reachable and operable by keyboard
  alone, verified by a scripted tab-through.
- **SC-004**: The layout has no horizontal scroll at 375px, verified in the
  browser checkpoint.
- **SC-005**: Tool calls, sources, and the budget meter are each covered by an
  acceptance scenario and demonstrated in the checkpoint.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Assumptions

- Feature 001 is the baseline; this feature adds no new backend endpoints unless
  strictly needed for provenance display.
- The model may emit standard markdown; only a safe subset is rendered.
- Third-party libraries are vendored (pinned) under `web/static/vendor/`; no CDN
  and no build step.
- A headless browser checkpoint uses the Playwright tooling already available to
  the agent; it is not wired into CI in this feature.

## Real-World Coverage

- **Input distribution**: free-form chat; markdown and tool steps render from
  model/tool output. No adversarial-rendering suite (gap).
- **Data quality**: model/user markup is sanitized before the DOM (WV-9); tool
  JSON is parsed defensively.
- **Edge & failure modes**: Stop, error + Retry, and the empty state are defined.
- **Scale envelope**: single browser session; the system envelope is measured in `docs/scale.md`.
- **Degradation**: a failed turn surfaces inline with Retry.
- **Change evidence**: UI-only; no quantitative delta (see `specs/change-log.json`).
