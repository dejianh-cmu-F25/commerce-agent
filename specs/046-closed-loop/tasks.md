# Tasks: Closed-Loop Shopping Agent

**Feature**: `046-closed-loop` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Deliverable paths below are the paths that exist on disk; where the plan named a file
that was never created (or was consolidated), the actual path is given instead.

## Completed

- [x] T000 Spec + plan written (`specs/046-closed-loop/spec.md`, `plan.md`)
- [x] T001 Supersede `014-post-purchase` and `045-shopping-agent`
- [x] T100 Policy SoT + renderer — `config/policies/amazon.yaml`, `app/returns/render.py`,
  `app/returns/amazon_policy.py`
- [x] T101 `decide_return` runtime gate — `app/gates/policy.py` (the plan's
  `app/returns/eligibility.py` was folded into `amazon_policy.py`)
- [x] T102 Dual-run legacy vs new gate — `evals/engine_agreement.py` (SC-003: 11/11)
- [x] T103 MCP storefront server — `app/mcp/server.py:build_storefront_server`
  (one module holds all three servers; the plan's three files were consolidated)
- [x] T104 MCP customer-accounts server — `app/mcp/server.py:build_customer_accounts_server`
- [x] T105 MCP checkout server (ACP-sim) — `app/mcp/server.py:build_checkout_server`
- [x] T106 Catalog + reviews import — `scripts/import_catalog.py`, `scripts/import_reviews.py`
- [x] T107 `search_products` + retrieval benchmarks — `app/tools/catalog.py`,
  `evals/bench_discovery.py`, `evals/esci_rerank.py`
- [x] T108 Cart adapter — `app/ports/cart.py`, `app/adapters/cart_factory.py`,
  `app/adapters/cart_session.py`, `app/adapters/cart_shopify.py`
  (the plan's `app/adapters/shopify_cart.py` was never created under that name).
  **Live Storefront path is unverified** — no `SHOPIFY_STOREFRONT_TOKEN` exists for this
  store; request shapes and mapping are covered against a MockTransport. See
  `docs/shopify-setup.md`.
- [x] T109 ACP-sim checkout adapter — `app/adapters/acp_checkout.py`,
  `evals/acp_conformance.py` (not `evals/acp_cases.jsonl`)
- [x] T110 Simulated auth + tenancy gate — `app/ports/auth.py`, `app/gates/tenancy.py`
- [x] T111 Journey prompt (procedure only) — `config/prompts/journey.md`
- [x] T112 Rewire `web/main.py` — `web/main.py:build_agent`
- [x] T114 Pass^k + τ-bench + AgentDojo — `evals/passk.py`, `evals/agentdojo_injection.py`
  (not `evals/injection.py`)
- [x] T115 Error attribution — `app/evaluation/failure.py`, `evals/passk.py`
  (not `evals/attribution.py`)
- [x] T116 Closed-loop UI — `frontend/src/components/app/*` (10 components)
- [x] T117 Provenance + audit + docs — `docs/data-provenance.md`, `docs/architecture.md`

## Deliberate divergences

- [x] T113 Remove legacy path — **the path is gone; the modules are not.**
  Removed (verified): nothing in `app/` or `web/` wires the legacy order tools, so no user
  or agent can reach the legacy path any more, and `docs/architecture.md` marks it
  deprecated.
  Retained, deliberately: `app/returns/policy.py` is the reference implementation in
  `evals/engine_agreement.py` — the source of the SC-003 "engine vs label 11/11" evidence
  — so deleting it would remove evidence rather than debt. `app/tools/orders.py` and
  `app/gates/returns.py` are dead in the app but still exercised by `evals/agent_eval.py`
  (which also carries the T115 attribution evidence) and by
  `tests/integration/test_order_tools.py` / `tests/unit/test_orders.py`. Physically
  deleting that cluster therefore touches a shipped eval and two test files and is left
  as its own deliberate cleanup, not folded into a cart change.

## Notes

- Every phase is independently deliverable, evaluable, and gets its own change-log
  entry (EV-1/EV-6) and rollback point.
- The project halts for human review at ¥10 cumulative model spend (HR-12).
- `specs/046-closed-loop/review.md` still lists 7 MANUAL clauses awaiting sign-off.

## Hardening — pluggable gates (2026-09-16)

- [x] H1 Gate mechanism — `app/gates/base.py` (`Effect`, `Applicability`, `GateResult`
  with `status`/`payload`/`component`, `GateContext` plugin fields), `app/gates/registry.py`
  (`GateSet`, `order_gates` with explicit order + fail-loud), `app/gates/pipeline.py`
  (clause aggregation, `hit_policy`).
- [x] H2 Registry enforcement — `ToolRegistry(gates=…)` runs the applicable gates at
  `execute`, fail-closed for `proposal`/`irreversible`, `ToolResult.blocked_by`,
  per-tool `context`/`consumes_context`/`id_args`.
- [x] H3 Approval as a gate — `app/gates/approval.py` replaces the inline HITL check
  in `complete_checkout`.
- [x] H4 One factory on every surface — `app/gates/factory.py:build_gate_set`; `web/main.py`
  and `app/mcp/server.py` build from it (closes WP-6).
- [x] H5 Config — `settings.gates` (`hit_policy`, `order`, `disabled`) + `config/settings.yaml`.
- [x] H6 Observability — the loop records the blocking gate on the tool span.
- [x] H7 Tests — `tests/unit/test_gate_registry.py`, `tests/unit/test_gate_coverage.py`
  (meta-test), `tests/integration/test_mcp_gates.py`; evals migrated to pass `GateSet`.
- [x] H8 Evidence — `specs/change-log.json` #119; the reports that declare the changed
  files refreshed (`reports/agentdojo.md`, `reports/post-purchase-eval.md`).
