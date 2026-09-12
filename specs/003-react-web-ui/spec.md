# Feature Specification: React Web UI

**Feature Branch**: `003-react-web-ui`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Rebuild the browser chat surface with React 19 and Vercel AI Elements
(Tailwind v4 + shadcn/ui), driven by `useChat` over a custom transport that
adapts the existing SSE event stream, and served by FastAPI as a built SPA. Keep
the feature parity of 002 and fix the layout so the app fills the viewport.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Chat on the React surface (Priority: P1)

A customer opens the app and has the same conversation quality as before:
streamed, formatted replies; tool calls shown as steps; grounding sources; a
budget meter; stop and retry — now rendered with React and AI Elements.

**Why this priority**: This is the whole point of the rebuild; parity is the
minimum bar.

**Independent Test**: Send a message that triggers a tool; assert the reply
streams, a tool step with a status appears, sources are listed, and the budget
meter updates.

**Acceptance Scenarios**:

1. **Given** the app loads, **When** the customer sends a message, **Then** the
   reply streams into an AI Elements `Message`/`Response` with markdown rendered.
2. **Given** the model requests a tool, **When** it starts and finishes, **Then**
   an AI Elements `Tool` step shows the name, input, and a status (running → ok).
3. **Given** a grounded reply, **When** it completes, **Then** an AI Elements
   `Sources` area lists the product(s) from the `products` UI component.
4. **Given** a turn completes, **When** usage is reported, **Then** the budget
   meter reflects spent vs limit.

---

### User Story 2 - Control and recovery (Priority: P1)

The customer can stop a stream and retry a failed turn, using `useChat`'s status
model.

**Why this priority**: Required for parity and for a trustworthy surface.

**Independent Test**: Send a message and press Stop mid-stream; then force an
error and press Retry.

**Acceptance Scenarios**:

1. **Given** a request in flight, **When** the customer presses Stop, **Then**
   the stream aborts and the partial reply remains.
2. **Given** a failed turn, **When** it ends, **Then** an error is shown with a
   Retry that resends the last message.

---

### User Story 3 - Discoverability and budget (Priority: P2)

A first-time customer sees suggestion prompts, and the budget is visible.

**Independent Test**: On load, suggestion buttons are present and fill the
composer; after a turn, the budget meter updates.

**Acceptance Scenarios**:

1. **Given** no messages, **When** the page loads, **Then** suggestion buttons
   are shown; clicking one seeds the composer.
2. **Given** a completed turn, **When** usage is reported, **Then** the budget
   meter updates.

---

### User Story 4 - Fills the viewport, accessible, theme-aware (Priority: P2)

The layout fills the viewport at all sizes, works with a keyboard and screen
reader, and follows the system theme.

**Independent Test**: Load at 1440px and 375px; tab through and send; toggle the
system theme.

**Acceptance Scenarios**:

1. **Given** any viewport, **When** the app renders, **Then** the header, the
   conversation, and the composer fill the height with no horizontal scroll.
2. **Given** keyboard focus, **When** the customer tabs, **Then** focus is always
   visible and Enter submits.
3. **Given** the OS is in light mode, **When** the app loads, **Then** it uses the
   light theme; dark mode uses the dark theme.

### Edge Cases

- The stream aborts: the partial reply stays; the composer is usable again.
- A tool errors: the step shows an error state; the turn still completes.
- The budget is exceeded: an inline notice appears.
- A reply contains raw HTML or a `javascript:` link: it is neutralized (WV-9).

## Requirements *(mandatory)*

- **FR-001**: The surface MUST be a React 19 app built with Vite, TypeScript,
  Tailwind v4, shadcn/ui, and AI Elements components.
- **FR-002**: The chat MUST be driven by `useChat` from `@ai-sdk/react` over a
  **custom `ChatTransport`** that adapts the existing `POST /chat` SSE stream to
  AI SDK UI message chunks; the backend event contract MUST NOT change.
- **FR-003**: The transport MUST map text, tool calls/results, the `products` UI
  component, usage, budget, and error events (see `contracts/ui.md`).
- **FR-004**: Assistant text MUST render as sanitized markdown (WV-9).
- **FR-005**: Tool calls MUST render as AI Elements `Tool` steps with a status.
- **FR-006**: Grounding sources MUST render as AI Elements `Sources`.
- **FR-007**: Stop and Retry MUST work via the `useChat` status model.
- **FR-008**: The empty state MUST offer suggestions that seed the composer.
- **FR-009**: A budget meter MUST reflect usage events.
- **FR-010**: The layout MUST fill the viewport (full height, no horizontal
  scroll at 375px) — fixing the 002 layout gap.
- **FR-011**: Interactive elements MUST be keyboard-operable with visible focus;
  streamed content announced via a live region (WV-7).
- **FR-012**: The app MUST follow `prefers-color-scheme` (WV-8).
- **FR-013**: FastAPI MUST serve the built SPA at `/` while keeping the API
  endpoints.
- **FR-014**: The frontend MUST build in CI and in a multi-stage Docker image;
  `node_modules/` and build output MUST NOT be committed.
- **FR-015**: The old vanilla surface (`web/static/app.js`, `index.html`,
  `styles.css`, `vendor/`) MUST be removed.
- **FR-016**: The layout MUST scale with the window: header, transcript, and
  composer share one aligned column with a **fluid width** (≈92% of the viewport,
  capped at ~80rem) so it fits small screens and stays readable on large ones; the
  empty state MUST fill and center in the transcript area; wide content (suggestion
  rows, code) MUST wrap or scroll inside its own container so there is no
  page-level horizontal scroll from 320px up; live resize MUST re-flow cleanly.

### Key Entities

- **AgentUIMessage**: AI SDK `UIMessage` with custom data parts `sources` and
  `budget`.
- **ChatTransport**: adapts `POST /chat` SSE → `UIMessageChunk`.
- **Suggestion**, **Source**, **Budget**: as in 002.

## UI Requirements *(WV-6..WV-8)*

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | Load, no messages | Suggestion buttons; focused composer; budget `—` |
| Submitted | Message sent | User message; status "submitted"; Stop available |
| Streaming | First token | Assistant `Response` fills with a caret; `Tool` steps appear; status "streaming" |
| Success | Turn ends | Full reply; `Sources`; budget updated; composer enabled |
| Error | Failure | Inline error with Retry; partial reply kept |
| Disabled | In flight | Submit disabled |

### Accessibility

- [ ] Keyboard operable with visible focus; Enter submits; Esc stops.
- [ ] Streamed text announced via a live region.
- [ ] Tool status has a text label, not color alone.

### Responsive & Theme

- [ ] Shell fills the viewport; `body` height equals the window height.
- [ ] No page-level horizontal scroll from 320px up; wide content scrolls or wraps inside its container.
- [ ] Header, transcript, and composer share one aligned column with a fluid
      width (≈92% of the viewport, capped at ~80rem) — no fixed breakpoint jumps.
- [ ] Empty state fills the transcript area and is vertically centered.
- [ ] Suggestion rows wrap (or scroll inside their own container) on narrow screens.
- [ ] Live window resize re-flows with no stuck widths or overlap.
- [ ] Follows `prefers-color-scheme` (light and dark).

## Web Acceptance *(convention, WV-1)*

Open `/`, send "I need a tent under $250 for a weekend trip". The reply streams
with rendered markdown; a `search_products` tool step shows `ok`; a `Sources`
area lists the tent; the budget meter updates. Stop a turn mid-stream; trigger an
error and Retry.

## Observability *(convention, WV-1)*

The UI consumes the existing 001/002 event stream; no new backend events. The
turn `trace_id` remains the link to `logs/traces.jsonl` (feature 080).

## Success Criteria *(mandatory)*

- **SC-001**: Feature parity with 002 (states, tool steps, sources, budget,
  stop/retry, suggestions) demonstrated in the checkpoint.
- **SC-002**: 100% of model-derived markup is sanitized (no script/`onerror`/
  `javascript:` executes) — verified by a test.
- **SC-003**: The layout has no horizontal scroll at 375px and fills the viewport
  at desktop — verified in the checkpoint.
- **SC-004**: `npm run build`, `eslint`, `tsc --noEmit`, and `vitest` pass in the
  local gate (`scripts/ci.sh`); the Docker image builds with the frontend bundled.

## Assumptions

- Feature 002 remains the behavioral baseline; this feature replaces the
  implementation, not the behavior.
- The backend event contract is unchanged; only the frontend and its build/serve
  pipeline change.
- Node 18+ is available in CI and Docker build stages.
- Vendored registry components (AI Elements, shadcn/ui) are treated as generated
  code and excluded from strict typechecking.
