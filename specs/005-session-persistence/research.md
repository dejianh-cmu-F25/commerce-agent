# Research: Session Persistence

## D1. Port shape

**Decision**: `SessionRepository` with `create()`, `get(id)`, `get_or_create(id)`,
and `save(session)`. This matches what the web layer already needs.

**Rationale**: The consumer (web) creates or loads a session and saves it after a
turn. No speculative methods.

**Alternatives considered**: an event-append API (`append(session_id, event)`)
(rejected: the loop mutates the in-memory `Session`; saving the whole session is
simpler and idempotent).

## D2. Append-only storage with a stable sequence

**Decision**: `session_events(session_id, seq, kind, payload)` with
`PRIMARY KEY(session_id, seq)`; `save` inserts each event with `INSERT OR IGNORE`
by its index. Events are never updated (SL-1, RD-2).

**Rationale**: The event order is the model's view; a stable `seq` preserves it
and makes re-saving idempotent.

**Alternatives considered**: store the whole log as one JSON blob (rejected:
rewrites the log on every save; weaker append-only story).

## D3. Serialization of session events

**Decision**: `kind` + JSON `payload`. Kinds: `user`, `assistant`, `tool_result`.
Assistant carries `text` + `tool_calls` (`id`, `name`, `arguments`); tool_result
carries `call_id`, `name`, `content`, `status`. Unknown kinds fail loud.

**Rationale**: Explicit and versionable; a new event type extends the mapping.

**Alternatives considered**: `pickle` (rejected: unsafe/opaque); a schema library
(rejected: dependency for three shapes).

## D4. Provenance and cart

**Decision**: `session_provenance(session_id, product_id)` and
`session_cart(session_id, product_id, title, quantity, unit_price)`; `save`
replaces them (they are derived state, not the log).

**Rationale**: Resume restores grounding (P4) and, later, the cart.

## D5. When to save

**Decision**: the web layer saves the session once per turn, in the SSE stream's
`finally` block (after `TurnEnd`).

**Rationale**: One write per turn; the log is complete at that point. A crash
mid-turn loses only the in-flight turn.

## D6. Factory and default

**Decision**: `build_session_store(settings)` in `web/main.py`; default
`sqlite` (`data/db/sessions.sqlite`), `memory` for keyless/tests.

**Rationale**: Explicit resolve (PB-3); mirrors the storefront factory.
