# Implementation Plan: Full-Journey Shopping Agent

**Branch**: `045-shopping-agent` | **Date**: 2026-09-14 | **Spec**: [spec.md](./spec.md)

## Summary

One agent, two workflows under one harness: **discovery** (Amazon ESCI catalog,
planned) and **post-purchase** (Shopify orders + a real policy, implemented). The
model proposes; the harness disposes; behavioral invariants are enforced.

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P1 spec is the source of truth | this spec defines the feature | PASS |
| P3 model proposes, harness disposes | `propose_return_decision` has no side effect; approval is out of the tool set | PASS |
| P4 grounding | facts come only from tool results; provenance tracked | PASS |
| PB-1 config as contract | providers selected in `settings.yaml` | PASS |
| RD-1 graceful fallback | per-dependency fallbacks (`docs/degradation.md`) | PASS |
| RW-1..RW-4 | `## Real-World Coverage` complete | PASS |
| SC-1..SC-4 | scale/SLOs/diagnosability/change-safety | PASS |
| EV-1..EV-6 | change log + two-layer evaluation | PASS |

## Project Structure

```text
app/ports/post_purchase.py        # [done]  order/return contract
app/ports/catalog.py              # [planned] discovery contract
app/adapters/shopify_client.py    # [done]  Admin GraphQL transport
app/adapters/shopify_post_purchase.py  # [done]
app/adapters/post_purchase_memory.py   # [done] keyless fixture
app/adapters/catalog_esci.py      # [planned]
app/returns/{clauses,eligibility}.py   # [done]
app/tools/post_purchase.py        # [done]
app/tools/discovery.py            # [planned]
app/evaluation/invariants.py      # [done]
config/prompts/{post_purchase,discovery}.md
config/policies/policies.yaml     # [done]
config/knowledge/policies/        # [done] real policy (cited)
evals/{post_purchase_eval,retrieval_esci}.py
reports/post-purchase-eval.md     # [done]
```

## Design decisions

- **One harness, two workflows.** Routing is intent-based; the invariant layer is
  shared, which is the proof that the harness generalizes.
- **Real system of record.** Shopify (orders) and ESCI (catalog + labels) over
  hand-written fixtures.
- **Model proposes, harness disposes.** The deterministic verifier
  (`app/returns/eligibility.py`) checks the model's proposal; refunds are human.
- **Two-tier testing.** Large deterministic layers (ESCI retrieval, decision
  engine) are keyless and cheap; the model runs on a stratified sample under a
  cost cap.
- **Policy as versioned, citable clauses**, derived from a real, cited policy.

## Blast radius & rollback

- **Blast radius**: adds the discovery workflow and a second real data source;
  the post-purchase path and the harness are unchanged in behavior.
- **Rollback**: revert the squash-merge commit + rebuild; config-gated providers
  can be disabled (`resilience.fallback_enabled`, `knowledge.provider`).

## Complexity Tracking

No constitution violations. The two-workflow design is justified by the single
customer journey and the shared harness.
