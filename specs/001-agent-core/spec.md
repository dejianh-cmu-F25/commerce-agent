# Feature Specification: Agent Core Loop

**Feature Branch**: `001-agent-core`

**Created**: 2026-09-13

**Status**: Implemented (baseline)

**Input**: The foundation of the commerce agent: a hand-written loop that turns a
user message into model calls, tool calls, and a reply, with a session log as the
single source of truth.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ask, act, answer (Priority: P1)

A customer types a request. The agent decides whether to call a tool, calls it,
reads the result, and replies based on that result.

**Why this priority**: Without this, no other feature exists. It is the loop.

**Independent Test**: Send a message that needs a tool; assert the agent called
the tool, recorded the result, and produced a final assistant message.

**Acceptance Scenarios**:

1. **Given** a session and a catalog tool, **When** the customer asks for a tent,
   **Then** the agent calls `search_products` and replies using the tool result.
2. **Given** a tool returns no rows, **When** the agent replies, **Then** it says
   nothing was found rather than inventing a product.
3. **Given** a tool call fails, **When** the loop continues, **Then** the error is
   recorded as a tool result and the turn does not crash.

---

### User Story 2 - The log is the truth (Priority: P1)

The model only ever sees messages projected from the session log.

**Why this priority**: Reproducibility, evaluation, and trust depend on it.

**Independent Test**: Re-derive messages twice from the same session; assert
equality, and assert the loop builds requests only through `derive_messages`.

**Acceptance Scenarios**:

1. **Given** a session with history, **When** a request is built, **Then** it
   equals `derive_messages(session, system_prompt)`.
2. **Given** any divergence between built and derived messages, **When** the loop
   builds a request, **Then** it raises and the turn ends with an error event.

---

### User Story 3 - Stream to the browser (Priority: P2)

Events reach the surface as they happen.

**Why this priority**: The web demo needs progressive feedback.

**Independent Test**: Run a turn with a collecting sink; assert the event order
`TurnStart -> (ToolCallStarted|ToolResult)* -> TextDelta* -> TurnEnd`.

**Acceptance Scenarios**:

1. **Given** a running web app, **When** the customer sends a message, **Then**
   the browser receives SSE events and renders text and tool activity.

### Edge Cases

- The model never stops requesting tools: the loop stops at `max_turns` and ends
  the turn with reason `max_turns`.
- The provider returns malformed tool arguments: they parse to `{}` and the tool
  reports an error without ending the turn.

## Requirements *(mandatory)*

- **FR-001**: The loop MUST support multiple steps per turn, each a model call
  plus its tool calls.
- **FR-002**: Each turn MUST be bounded by `agent.max_turns`.
- **FR-003**: Model messages MUST be built only from the session log; a mismatch
  MUST crash the process (SL-1).
- **FR-004**: Tool execution MUST reject unknown tool names and MUST NOT end the
  turn on a tool error.
- **FR-005**: The loop MUST emit agent events through an injected `EventSink` and
  MUST NOT import a surface.
- **FR-006**: The LLM client MUST be injected and replaceable (mock and DeepSeek
  providers exist).

### Key Entities

- **Session**: `id`, append-only `events`, derived `cart`, derived `provenance`.
- **SessionEvent**: `UserMessage | AssistantMessage | ToolResultEvent`.
- **AgentEvent**: `TurnStart | TextDelta | ToolCallStarted | ToolResult |
  UIComponent | CartUpdate | TurnEnd | ErrorEvent`.

## Web Acceptance

Open `/`, type "I need a tent under $250", and press Send. The page shows the
assistant reply streaming in; with a real provider it also shows the
`search_products` tool call. `/healthz` returns `{"status":"ok"}`.

## UI Requirements

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | Page load, no messages | Header with budget `—`; empty transcript; focused input |
| Streaming | Message sent | User bubble; agent bubble fills as `TextDelta` arrives; Send disabled |
| Success | Turn ends | Agent reply with tool-call lines and a grounded answer; budget updates |
| Error | LLM or tool failure | `ErrorEvent` shown inline; Send re-enabled |
| Disabled | Request in flight | Send button disabled until the turn ends |

## Observability

Each turn emits `TurnStart`/`TurnEnd` with a `turn_id`. Structured tracing to
`logs/traces.jsonl` arrives with feature 080; this feature defines the event
boundary it will attach to.

## Success Criteria *(mandatory)*

- **SC-001**: A tool-using turn completes in one call and records the tool result.
- **SC-002**: Unit tests cover the happy path, an unknown tool, and the turn bound.
- **SC-003**: `derive_messages` is deterministic.
- **SC-004**: The web app starts and streams a reply in mock mode without any API key.

## Evaluation Plan

- **Dataset(s)**: the in-repo evaluation sets under `evals/` (keyless) — see `specs/RESULTS.md`.
- **Metric(s)**: see `## Measured Results` and `specs/RESULTS.md`.
- **Threshold(s)**: enforced by the local gate (`make ci-fast`).
- **Cost/speed**: keyless (no model call).
- **Report**: `specs/RESULTS.md`, `evals/report.md`.

## Assumptions

- The catalog is a small in-memory stand-in; feature 002 replaces it.
- Sessions are in-memory for now; persistence and resume arrive with feature 009.
- Checkout and payment are out of scope here (feature 021).

## Real-World Coverage

- **Input distribution**: free-form chat; unseen phrasings go to the model.
  Adversarial and out-of-distribution input is guarded before the model and
  measured (feature 028, `evals/adversarial.py`).
- **Data quality**: the session log is append-only; tool JSON is parsed
  defensively. User text is not validated beyond length.
- **Edge & failure modes**: unknown tool → error event, the turn continues; max
  turns is bounded; the budget stops the loop.
- **Scale envelope**: single process, single session; the system envelope is measured in `docs/scale.md`.
- **Degradation**: an LLM failure surfaces as an error event; there is no model fallback.
- **Change evidence**: model/prompt changes must update `specs/RESULTS.md` (EV-1).
