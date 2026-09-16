# Agent Note: Pluggable gates at one choke point

Status: implemented (2026-09-16) — feature `046-closed-loop` (hardening)

## Problem

A gate is decision-only (P3) and `ToolRegistry.execute` is the only executor, but the
gate was invoked **inside** each handler and wired at each surface. So enforcement
depended on remembering to inject it: `app/mcp/server.py` registered the
customer-accounts tools with no policy or tenancy gate, and the runtime "model
proposes, harness disposes" guarantee was simply absent on that surface (WP-6).
Adding a gate meant editing every tool (or every call site), which is the opposite
of a plug-in.

## Alternatives considered

- **Leave the wiring as is.** It works where it is remembered; it silently does
  nothing where it is not (the MCP surface is the proof). Rejected.
- **Tool-centric declaration** (each tool lists its gates). Explicit, but adding a
  cross-cutting gate still means editing every relevant tool; rejected in favour of
  a gate declaring its own applicability.
- **A generic middleware framework (decorators, DI, AOP).** More machinery than the
  problem needs, and the hard part (building the gate context from domain facts) is
  not solved by the wrapper (P6). Rejected.
- **An external policy engine (OPA / Cedar / Cerbos).** The right answer at
  multi-service scale, but over-built here; the existing ADR already rejected a
  configurable rule engine, and this change does not revisit that (it does not make
  the *rule structure* data). Rejected for now.
- **Fail closed on every `write` tool.** Wider than the risk: staged and simulated
  writes (checkout session, merchant proposals) would be blocked. Scoped to
  `proposal` / `irreversible` instead.

## Decision

- **Gates run at the single choke point.** `ToolRegistry.execute` selects the
  applicable gates and runs them **before** the handler; a block returns the gate's
  exact payload/status, so behaviour is unchanged.
- **A gate declares where and when it applies.** `applies_to` (tool names and/or an
  effect class) and `priority`; `GateSet.select` matches, `order_gates` resolves the
  order **explicitly** (an unknown name fails loud, PB-1/PB-3). Adding a gate is one
  class plus one line in `build_gate_set` — no tool change.
- **Fail closed for money-adjacent tools.** A `proposal` / `irreversible` tool with
  no covering gate is refused; a CI meta-test asserts the production set covers them.
- **One factory.** `app/gates/factory.build_gate_set` builds the standard set
  (provenance, tenancy, approval, policy) from `settings.gates`; web and MCP both use
  it, so the bypass cannot recur.
- **HITL becomes a gate.** `complete_checkout`'s inline `approved` check is now
  `ApprovalGate`.
- **A tool may supply the gate context.** Order-reading tools provide a `context`
  builder that resolves the order (for tenancy) and the facts (for policy); the
  proposal tool consumes the resolved context to attach the engine's clauses.

## Consequences

- Enforcement no longer depends on the wiring site; a new surface that uses the
  factory is gated automatically.
- The engine's clauses still reach the proposal (the gate's `cited_clauses` are
  attached), so decision accuracy and citation support are unchanged.
- `ToolRegistry()` with no gate set is unchanged, so the ~50 existing build sites
  (tests, ablations) keep working; the ablations now toggle gates by passing a
  `GateSet` instead of by monkeypatching a module global.
- Cost: the registry builds a gate context for every call when a gate set is present;
  the default builder is cheap and only tools with a domain `context` fetch anything.
- A gate can no longer be added by editing a tool, which is the point: the tool no
  longer knows its gates.
