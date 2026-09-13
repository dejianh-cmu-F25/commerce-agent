# Feature Specification: Customer Memory

**Feature Branch**: `013-customer-memory`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add cross-session customer memory so the agent recalls grounded facts
about a returning customer. Facts are extracted deterministically from what the
customer says, stored behind a `MemoryStore` port, recalled and injected into the
model context through the session log (SL-1), and shown in a browser Memory view
with a per-fact forget control.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Recall a returning customer's stated facts (Priority: P1)

A customer tells the agent something durable about themselves — a budget, a size,
a preference, or a constraint. In a later session the agent already knows it and
uses it without being told again.

**Why this priority**: Cross-session memory is the harness job the architecture
already reserves (`Memory` port, HR-2); without it every session starts blank and
the "personalization" promise in the README is unmet.

**Independent Test**: Run one turn stating a preference, then a second session for
the same customer; assert the recalled fact is present in the model context of the
second session and that the agent can answer from it.

**Acceptance Scenarios**:

1. **Given** a new customer, **When** they say "I usually wear size M" and the
   turn ends, **Then** the fact "Wears size M" is stored for that customer.
2. **Given** a stored fact and a **new** session for the same customer, **When**
   the customer sends any message, **Then** the recalled facts appear in the
   system context of that session's first model request.
3. **Given** the same customer in a later session, **When** they ask "what do you
   remember about me?", **Then** the answer reflects only stored facts.

---

### User Story 2 - Grounded, deterministic extraction (Priority: P1)

Facts come only from what the customer actually said; extraction is keyless and
deterministic. The agent never invents a fact, and prices/stock/policy are never
turned into memory.

**Why this priority**: Memory is model-visible context; an ungrounded fact is a
hallucination with a longer lifetime than one turn (P4, P8).

**Independent Test**: Feed a corpus of messages to the extractor; assert only
recognized patterns produce facts, that questions and assistant text produce none,
and that the same input always yields the same facts.

**Acceptance Scenarios**:

1. **Given** the message "I'm allergic to wool", **When** extraction runs, **Then**
   a constraint fact "Avoids wool" is produced.
2. **Given** the message "What tents are under $200?", **When** extraction runs,
   **Then** no durable fact is stored from the question.
3. **Given** a message with no durable statement, **When** extraction runs, **Then**
   nothing is stored and the turn is unchanged.
4. **Given** the same fact is stated twice, **When** it is stored again, **Then**
   the store does not duplicate it (RD-2).

---

### User Story 3 - Inspect and forget stored facts (Priority: P2)

The customer can see what is remembered and remove any fact, or clear everything.

**Why this priority**: Memory of a person is sensitive; a visible, reversible
store is the trust contract that makes the feature acceptable.

**Independent Test**: Store two facts, open the Memory view, forget one; assert the
store and the view reflect the removal, and that a forgotten fact no longer
appears in a new session's context.

**Acceptance Scenarios**:

1. **Given** stored facts, **When** the customer opens the Memory view, **Then**
   each fact is listed with its kind and when it was learned.
2. **Given** a listed fact, **When** the customer forgets it, **Then** it is
   removed and does not appear in later sessions.
3. **Given** a customer with no facts, **When** they open the Memory view,
   **Then** an empty state explains that nothing is remembered yet.

---

### User Story 4 - Config-selected and fail-loud (Priority: P3)

The memory store is selected by configuration with a keyless default; an unknown
provider fails at load.

**Independent Test**: Build the store with each provider; assert the memory
provider works keylessly and that an unknown provider is rejected.

**Acceptance Scenarios**:

1. **Given** `memory.provider: sqlite`, **When** the app starts, **Then** facts
   persist across restarts.
2. **Given** an unknown provider, **When** settings load, **Then** it fails loud.

---

### Edge Cases

- **No customer identity**: with no customer id the agent runs without memory and
  never writes facts (no "guest" bucket that would mix customers).
- **Memory store unavailable**: a store error degrades to "no memory" for the
  turn and is traced; the conversation still completes (RD-1).
- **Empty recall**: no stored facts means no memory note is appended; the model
  context is byte-identical to the no-memory case.
- **Very long user text**: extraction only matches bounded phrases; no unbounded
  capture is stored.
- **Fact learned mid-session**: within one session the fact is already in the
  conversation; it is injected into the model context only for sessions that did
  not observe it (avoid duplicate context).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST define a `MemoryStore` capability (service
  definition) for adding, listing, and forgetting a customer's facts.
- **FR-002**: The system MUST provide at least two providers — a keyless in-memory
  provider and a durable SQLite provider — selected by configuration; an unknown
  provider MUST fail loud at load (PB-1).
- **FR-003**: The system MUST extract candidate facts from the **customer's** text
  only, using a deterministic, keyless extractor; model and tool output MUST NOT
  be a source of facts (P4, P8).
- **FR-004**: The extractor MUST recognize a bounded set of durable patterns
  (budget ceiling, size, stated preference, owned/owned-already gear, explicit
  avoidance) and MUST NOT store facts from questions or from statements with no
  durable content.
- **FR-005**: Storing a fact MUST be idempotent per `(customer, kind, value)`;
  re-stating a fact MUST NOT create a duplicate (RD-2).
- **FR-006**: Each session MUST be associated with a customer identifier supplied
  by the client; sessions with no customer id MUST run memory-disabled.
- **FR-007**: When a session for a known customer begins, the system MUST recall
  the customer's facts and record them **in the session log** before building
  model messages, so the model context remains reconstructable from the log
  (SL-1). Recall MUST occur at most once per session.
- **FR-008**: Facts recalled into a session MUST be folded into the model's system
  context; if there are no facts, the model context MUST be unchanged.
- **FR-009**: The system MUST expose the customer's stored facts and a per-fact
  forget (and a forget-all) operation through the web surface (WV-5).
- **FR-010**: Forgetting a fact MUST remove it from the store and from the model
  context of subsequent sessions.
- **FR-011**: Memory recall and extraction MUST each emit a structured span
  (`memory`) under the turn's `trace_id` (SL-2, OB-1).
- **FR-012**: A memory failure MUST NOT fail the turn; it MUST degrade to no
  memory and be observable (RD-1).

### Key Entities *(include if feature involves data)*

- **MemoryFact**: one durable, customer-grounded statement. Attributes: a
  server-issued id, the owning customer id, a `kind`
  (`preference` | `constraint` | `profile`), the fact text, and when it was
  learned.
- **Customer**: the identity that owns facts and sessions. Identified by a
  client-supplied opaque id; it is not a login and holds no credentials.

## UI Requirements *(when the feature is browser-visible; WV-6..WV-8)*

The browser gains a **Memory** view (a fourth tab beside Chat / Traces /
Merchant) that shows the current customer's remembered facts and lets them be
forgotten. The Chat view is unchanged; recalled memory changes the agent's
answers, not the chat chrome.

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | The customer has no stored facts | A short line: nothing is remembered yet; how facts are learned (things you tell the agent) |
| Loading | The Memory view opens and the list is being fetched | A "Loading…" line |
| Success | Facts are loaded | A list of facts; each row shows the fact, its kind, and when it was learned, with a Forget control; a Forget-all control when more than one fact |
| Error | The list fails to load, or a forget fails | An inline error message with a Retry (load) / the row restored (forget) |
| Disabled | A forget is in flight | That row's Forget control is disabled until it resolves |
| No identity | The browser has not established a customer id yet | The Memory view shows the empty state (a customer id is created on first send) |

### Accessibility

- [ ] The Memory tab and Forget controls are keyboard-operable with a visible focus ring.
- [ ] The list is announced politely when it changes (`aria-live`), and a removed row is not silently dropped.
- [ ] Motion respects `prefers-reduced-motion`.
- [ ] Icon-only controls have `aria-label`; text is at least 16px where it is an input.

### Responsive & Theme

- [ ] The Memory view fills the viewport below the header; long fact text wraps and does not cause page-level horizontal scroll from 320px up.
- [ ] The view shares the app's fluid column (`min(80rem, 92%)`).
- [ ] Theme follows `prefers-color-scheme`.

## Web Acceptance

- The header exposes a **Memory** tab; selecting it shows the current customer's facts.
- Telling the agent a durable fact (e.g. "I usually wear size M") and opening the Memory tab shows the learned fact.
- Starting a **new chat** and asking "what do you remember about me?" answers from the stored facts (cross-session recall), without re-stating them.
- Forgetting a fact removes it from the view and from later sessions.

## Observability

- Each turn that recalls or extracts memory emits a `memory` span sharing the
  turn's `trace_id`, with counts and outcomes (recalled, stored, skipped,
  duplicate) — never the full customer id or raw text beyond the redaction limit.
- Memory read/forget API calls are visible in the server log; the Trace Viewer
  continues to render the turn/llm/tool/memory timeline (OB-4).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A fact stated in one session is present in the model context of a
  later session for the same customer in 100% of the gold scenarios.
- **SC-002**: Extraction is deterministic: the same input yields the same facts
  across runs (no model call, no network).
- **SC-003**: Re-stating a fact never increases the stored fact count for that
  customer (idempotent).
- **SC-004**: With memory disabled or empty, the model context equals the
  no-memory baseline (no accidental context drift).
- **SC-005**: The local gate (ruff, pyright, pytest, evals, spec self-review,
  frontend) passes with the feature enabled.

## Assumptions

- The customer id is an opaque, client-generated identifier stored in the
  browser; it is not authentication and is out of scope for security hardening.
- Facts are preferences/constraints/profile only; prices, stock, and policy are
  never memory (they stay grounded in tool results per P4).
- Extraction is deterministic and keyless in v1; an LLM-assisted extractor is
  deferred and must keep the deterministic extractor as its fallback (RD-1).
- The Memory view is consumer-facing; the merchant face is unchanged.
- A single keyless demo customer per browser is sufficient; multi-device identity
  is out of scope.

## Real-World Coverage

- **Input distribution**: durable statements; extraction is a bounded,
  deterministic pattern set, so unknown phrasings are simply not stored.
- **Data quality**: facts are grounded in the customer's own words (P4); storage
  is idempotent per (customer, kind, text).
- **Edge & failure modes**: no customer id → memory disabled; a store error
  degrades to no memory.
- **Scale envelope**: per-customer fact sets; not measured (gap).
- **Degradation**: memory failures never fail the turn (RD-1).
- **Change evidence**: the ablation measures the memory contribution (+0.167).
