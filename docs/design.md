# Design: a post-purchase resolution agent

This document is the front door to the project: the problem, the decisions, the
**alternatives rejected**, and how quality is measured. Read it before the code.

---

## Problem

Post-purchase support is where e-commerce brands lose money in two directions at
once:

- **Volume.** "Where is my order" (WISMO) is 30–50% of DTC support contacts at
  roughly $4–$15 each; returns and refunds are the next-largest driver.
- **Risk.** A wrong refund is a direct loss; a wrong refusal is churn. The
  decision depends on **policy** (versioned, with exceptions) and **order state**
  (which must be verified, not taken from the customer's word).

A generic "RAG chatbot" does not survive this: it answers from text without
verifying order state, and it cannot be trusted with money. The hard part is not
retrieval — it is the **decision**, the **verification**, and the **guardrails**.

## Scope

**One journey, deep:** a post-purchase resolution agent that

1. **answers WISMO** from the real order record, and
2. **decides return/refund eligibility** from the policy + the order, drafts the
   customer reply, and **proposes** the action.

Writes are proposals: the agent may create a return **request** (`REQUESTED`); a
human approves it. The agent never issues a refund.

**Designed expansion surface** (see "Expansion ladder"): product discovery over
Amazon ESCI, then order modification, exchanges, warranty, proactive delay
notices. One harness, many workflows.

## Key decisions

| # | Decision | Why |
|---|---|---|
| 1 | **One workflow, deep** — not a broad assistant | Breadth dilutes; interviewers reward depth. RAND: successful AI projects are scoped so tightly that drift is barely possible. |
| 2 | **Real system of record** — Shopify Admin GraphQL API | Real schema, pagination, rate limits, GraphQL cost, and the real returns state machine. Far more credible than a hand-written fixture. |
| 3 | **Reads open, writes gated** | The agent proposes; the harness disposes. Refunds are irreversible and money-adjacent, so a human approves. |
| 4 | **Policy as versioned, citable clauses** | The most common real failure is citing a superseded policy. Clauses with `effective_from` make version conflicts a first-class, testable case. |
| 5 | **Decision eval, human-labeled, with citation support** | The model's *judgment* is the load-bearing part; it must be measured, not asserted. |
| 6 | **Keyless default, real model opt-in** | Reproducible without a key (P8) and still able to produce real evidence on a budget. |
| 7 | **Budget enforced in the harness** | Runaway loops are a top production failure; a hard cap is cheap insurance. |

## Alternatives rejected

- **A broad "shopping + merchant" assistant.** Looks impressive, proves little:
  the AI stops being load-bearing (most logic is CRUD), and no single workflow is
  deep enough to defend. Rejected in favor of one journey.
- **Pure RAG ("answer from the docs").** No order verification, no decision, no
  guardrail — the exact failure mode the industry reports. Rejected.
- **Let the agent issue refunds directly.** Irreversible and money-adjacent; a
  single bug is a real loss. Rejected: the agent proposes, a human approves.
- **Scrape a large policy corpus.** Volume adds noise and licensing risk without
  adding signal; the failure we care about is *version conflict*, which a curated
  versioned corpus tests better. Rejected in favor of curated clauses.
- **Mock-only evaluation.** Produces numbers that prove nothing about the real
  model. Rejected: real-model runs are opt-in but normal, with recorded traces.
- **Rely on the system prompt to ignore injected content.** Prompts are
  suggestions; the Replit incident showed that. Rejected: the harness enforces
  (input guard, tool-result-as-data, path/authority checks).

## Architecture (in one screen)

```
Surfaces      web/ (SSE), CLI
Capabilities  app/tools (WISMO, return eligibility), app/gates (propose → approve)
Adapters      shopify_client, shopify_post_purchase, post_purchase_memory,
              llm (deepseek | mock), policy retriever, tracer, session store
Ports         post_purchase, llm, retriever, tracer, session_store, cost_meter
Core          loop, session log (SL-1), settings, prompts
```

Dependencies point inward; adapters implement ports and are injected by config.

## Evaluation

**Case schema** (`evals/post_purchase_cases.jsonl`):

```json
{"case_id": "return-window-edge-01",
 "message": "I got my tent 32 days ago, can I still return it?",
 "order_fixture": "order-1001",
 "expected_decision": "ineligible",
 "expected_policy_refs": ["returns#return-window"],
 "notes": "Outside 30-day window; no exception stated."}
```

**Slices:** by intent (WISMO / return / exchange / warranty), by difficulty, by
policy version.

**Metrics:** decision accuracy, **policy-citation support** (does the cited clause
actually support the decision?), escalation precision/recall, cost per task, p95
latency, containment rate.

**Guardrail cases:** injection in the message or a product title, a superseded
policy as the only match, an order id that belongs to another customer, and a
refund amount that does not match the record.

**Artifacts a reviewer can open:** `evals/post_purchase_cases.jsonl`,
`reports/compare.md`, `traces/redacted/`, and this document.

## Expansion ladder

| Layer | Workflow | Status |
|---|---|---|
| L0 core | WISMO + return/refund eligibility | building |
| L1 | product discovery over **Amazon ESCI** (human relevance labels) | planned (phase 4) |
| L2 | order modification, exchange, warranty, proactive delay notices | roadmap |
| L3 | merchant-side ops | out of scope |

## What is real vs demo (be honest)

- **Real:** the Shopify API, the schema, the returns state machine, the policy
  structures, the evaluation methodology, and the harness.
- **Test data:** the development store's catalog and orders are generated demo
  data. Do not claim otherwise.
- **No real users.** This is a portfolio project, not a deployed product; say so.

## Next

Phase 0 is complete: domain primer, Shopify read adapter, versioned policy
corpus, this design doc. Phase 1 adds the WISMO and return-eligibility tools, the
human-labeled decision set, and the first eval report.
