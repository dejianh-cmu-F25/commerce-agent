# Tasks: Full-Journey Shopping Agent

**Feature**: `045-shopping-agent` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Post-purchase (implemented in this change)

- [x] T001 FR-001/FR-004/FR-005 — `app/ports/post_purchase.py`, `app/adapters/shopify_post_purchase.py`
- [x] T002 FR-005 — `app/returns/clauses.py`, `app/returns/eligibility.py`, `config/policies/policies.yaml`
- [x] T003 FR-003/FR-006 — `app/tools/post_purchase.py` (`get_order_status`, `list_returnable_items`, `propose_return_decision`)
- [x] T004 FR-007/FR-008/FR-009/FR-010 — `app/safety/input_guard.py`, `docs/invariants.md`, `app/evaluation/invariants.py`
- [x] T005 FR-011 — `docs/degradation.md`, `app/core/resilience.py`
- [x] T006 Evaluation — `evals/post_purchase_eval.py`, `evals/post_purchase_cases.jsonl`, `evals/invariant_cases.jsonl`, `reports/post-purchase-eval.md`
- [x] T007 Tests — `tests/unit/test_return_eligibility.py`, `tests/unit/test_invariants.py`, `tests/unit/test_shopify_post_purchase.py`, `tests/integration/test_shopify_live.py`

## Discovery (planned — tracked, not part of this change)

| # | Task | Requirement | Files |
| --- | --- | --- | --- |
| T101 | Catalog port + ESCI adapter | FR-002 | `app/ports/catalog.py`, `app/adapters/catalog_esci.py` |
| T102 | Discovery tools (`search_products`) | FR-002 | `app/tools/discovery.py` |
| T103 | Intent routing (discovery vs post-purchase) | FR-001 | `config/prompts/` |
| T104 | ESCI retrieval benchmark + discovery cases | FR-002, SC-005 | `evals/retrieval_esci.py`, `evals/discovery_cases.jsonl` |
| T105 | Tests | — | `tests/unit/test_catalog_esci.py`, `tests/unit/test_discovery_tools.py` |
| T106 | ESCI attribution | — | `docs/data-provenance.md` |

## Dependencies

- Post-purchase is complete; discovery is independent (a new port/adapter).
- The invariant layer is shared; a discovery change must not regress it.
