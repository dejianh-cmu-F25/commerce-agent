# Agent Note: Customer memory is logged, grounded, and harness-owned

Status: implemented (2026-09-13) — feature `013-customer-memory`

## Problem

The architecture reserves a `Memory` port and the harness's "memory" job, but no
implementation existed: every session started blank. Adding cross-session
personalization raises three cross-cutting questions that outlive the feature:

1. **How can memory be model-visible without breaking SL-1?** Model messages are
   built only from the session log; injecting recalled facts out-of-band would
   create a second context-construction path.
2. **Who writes memory, and from what?** A model-proposed fact is an ungrounded
   claim with a long lifetime; commerce already treats grounding as the trust
   boundary (P4).
3. **What is the identity?** Cross-session memory needs a stable customer, but
   the app has no login and must stay keyless.

## Alternatives considered

- **Inject memory as an extra system message outside the log.** Simplest to
  write, but it breaks SL-1: `derive_messages` would no longer be the single
  construction path, and replay could not reproduce what the model saw. Rejected.
- **Let the model call a `remember` tool.** Flexible, but it makes the model the
  author of durable personal facts — ungrounded and hard to audit. Rejected in
  favor of harness-driven extraction from the customer's own text.
- **LLM-assisted extraction from the start.** Better recall of fuzzy statements,
  but it adds a model call, cost, and nondeterminism for a capability that a
  bounded pattern set covers. Deferred; the deterministic extractor is the
  required fallback (RD-1).
- **A single shared "guest" memory bucket.** Avoids identity plumbing, but it
  would mix customers' facts — a privacy failure. Rejected: no customer id means
  memory is disabled, never shared.
- **Server-assigned identity via a cookie.** More robust across devices, but adds
  a session/cookie concern to a keyless demo. Deferred; the opaque client id is
  enough for v1.

## Decision

- **Recalled facts are recorded in the log.** The loop appends a `MemoryNote`
  event at most once per session, before building messages; `derive_messages`
  folds `MemoryNote` into the system message. A session with no facts gets no
  note, so its context is byte-identical to the no-memory baseline.
- **The harness owns writes.** A deterministic, keyless extractor
  (`app/memory/extract.py`) derives a bounded set of durable facts from the
  customer's text only; questions and chatter produce nothing. The model never
  writes memory.
- **Identity is an opaque client id.** The browser generates `customer_id` and
  sends it on `/chat`; sessions without one run memory-disabled. It is not
  authentication and holds no credentials.
- **Forget is first-class.** A `MemoryStore` exposes add/list/forget/forget-all,
  surfaced through `/memory` endpoints and a Memory tab.

## Consequences

- Memory is reproducible: the model context remains a pure function of the
  session log, so traces and replay still describe exactly what the model saw.
- Memory failures degrade to "no memory" and are traced; they never fail a turn
  (RD-1), and the extractor adds no model cost (HR-12).
- Extraction recall is intentionally conservative: it recognizes explicit,
  bounded statements and will miss nuanced ones. Improving recall means adding
  patterns or the deferred LLM extractor behind the same port.
- The session schema gained `customer_id` (migrated in place) and a `MemoryNote`
  event kind; older databases upgrade on open.
- A client can only read/forget memory for the id it presents. With no auth this
  is a demo-level trust model, recorded here as a known boundary.
