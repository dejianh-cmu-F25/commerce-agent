# Tasks: Closed-Loop Shopping Agent

**Feature**: `046-closed-loop` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Completed (this change)

- [x] T000 Spec + plan written (`specs/046-closed-loop/spec.md`, `plan.md`)
- [x] T001 Supersede `014-post-purchase` and `045-shopping-agent`

## Planned (tracked; not part of this change)

| # | Task | Requirement | Deliverable |
| --- | --- | --- | --- |
| T100 | Policy SoT + renderer | FR-007, FR-010 | `config/policies/amazon.yaml`, `app/returns/render.py` |
| T101 | `decide_return` runtime gate | FR-008 | `app/gates/policy.py`, `app/returns/eligibility.py` |
| T102 | Dual-run legacy vs new gate | FR-008 | `evals/engine_agreement.py` |
| T103 | MCP storefront server | FR-001, FR-016 | `app/mcp/storefront.py` |
| T104 | MCP customer-accounts server | FR-006, FR-013 | `app/mcp/customer_accounts.py` |
| T105 | MCP checkout server (ACP-sim) | FR-005 | `app/mcp/checkout.py` |
| T106 | Reviews'23 import (~200–500) | FR-002 | `scripts/import_catalog.py` |
| T107 | `search_products` + ESCI benchmark | FR-002, SC-007 | `app/tools/catalog.py`, `evals/retrieval_esci.py` |
| T108 | Cart adapter (Shopify Storefront) | FR-004 | `app/adapters/shopify_cart.py` |
| T109 | ACP-sim checkout adapter | FR-005, SC-006 | `app/adapters/acp_checkout.py`, `evals/acp_cases.jsonl` |
| T110 | Simulated auth + tenancy gate | FR-013, SC-008 | `app/ports/auth.py`, `app/gates/tenancy.py` |
| T111 | Journey prompt (procedure only) | FR-001, FR-010 | `config/prompts/journey.md` |
| T112 | Rewire `web/main.py` | FR-001 | `web/main.py` |
| T113 | Remove legacy path | Migration step 4 | delete `orders.start_return`, `returns/policy.py` |
| T114 | Pass^k + τ-bench + AgentDojo | SC-009 | `evals/passk.py`, `evals/injection.py` |
| T115 | Error attribution | Evaluation | `evals/attribution.py` |
| T116 | Closed-loop UI | SC-010 | `frontend/src/components/app/*` |
| T117 | Provenance + audit + docs | Data Provenance | `docs/data-provenance.md` |

## Dependencies

- P1 (MCP) depends on P0 (policy SoT + engine).
- P2/P3/P4 depend on P1.
- P5 depends on P0–P4.
- P6 depends on P1–P4; P7 runs throughout.

## Notes

- Every phase is independently deliverable, evaluable, and gets its own change-log
  entry (EV-1/EV-6) and rollback point.
- The project halts for human review at ¥10 cumulative model spend (HR-12).
