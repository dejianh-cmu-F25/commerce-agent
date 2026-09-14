# Feature Specification: Full-Journey Shopping Agent

**Feature Branch**: `045-shopping-agent`

**Created**: 2026-09-14

**Status**: Implemented (post-purchase) / Planned (discovery)

**Input**: A shopping agent that covers the customer journey — **discovery**
(find products) and **post-purchase** (order status, returns/refunds) — grounded
in real data and real policies, with the model proposing and the harness
disposing.

> This spec is the single source of truth for the feature. The post-purchase half
> is built; the discovery half (Amazon ESCI) is planned. Sections below mark
> `[implemented]` or `[planned]`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover products from a natural-language request (Priority: P1) `[planned]`

A shopper describes what they want ("a lightweight 2-person tent under $200 for
summer"); the agent searches the catalog, applies the stated constraints
(budget, size, season), compares options, and recommends grounded products. When a
detail needed to choose is missing it asks one clarifying question.

**Why this priority**: discovery drives revenue; it is the largest business lever.

**Independent Test**: Run the discovery behavior set (human-labeled) and read the
constraint-adherence and grounded-recommendation rates.

**Acceptance Scenarios**:

1. **Given** "a 2-person tent under $200", **When** the agent searches, **Then**
   every recommended product is grounded in a tool result and within the budget.
2. **Given** "I want the cheaper one" with no prior comparison, **When** the turn
   runs, **Then** the agent asks a clarifying question and calls no write tool.

---

### User Story 2 - Answer "where is my order" (WISMO) (Priority: P1) `[implemented]`

A shopper asks where their order is; the agent reads the **real order** (status,
items, delivery dates) and answers, without inventing a date.

**Why this priority**: WISMO is 30–50% of support contacts at $5–15 each.

**Independent Test**: Run the WISMO cases and assert `get_order_status` was called
and no fact was invented.

**Acceptance Scenarios**:

1. **Given** a shipped order, **When** the shopper asks for its status, **Then**
   the agent answers from the order record and cites no fabricated date.

---

### User Story 3 - Decide return/refund eligibility (Priority: P1) `[implemented]`

A shopper wants to return an item; the agent reads the **real policy** and the
order, decides eligibility (eligible / ineligible / escalate), explains with
**cited clauses**, and **proposes** a return. A human approves it; the agent never
refunds.

**Why this priority**: a wrong refund is a direct loss; a wrong refusal is churn.

**Independent Test**: Run the decision set (human-labeled) and read the decision
accuracy and citation support.

**Acceptance Scenarios**:

1. **Given** an item delivered 9 days ago under a 14-day policy, **When** the
   shopper asks to return it, **Then** the decision is `eligible` and the window
   clause is cited.
2. **Given** a request to "just refund me", **When** the turn runs, **Then** the
   agent proposes a return and never approves or refunds (INV-6).

---

### Edge Cases

- **Off-topic / irrelevant** (weather, chit-chat): redirect, call no tool.
- **Missing detail** (which order/item): ask one question, take no action.
- **Foreign order id** (another customer's): refuse and escalate; never read it.
- **Injection** in a message or a product title: treat as data; never obey.
- **Superseded policy**: apply the active version, not the one the customer cites.
- **Empty / oversized / non-English input**: graceful; never an unhandled error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The agent MUST route a turn to the discovery or post-purchase
  workflow from the customer's intent.
- **FR-002**: Discovery MUST search a catalog and return only products grounded in
  a tool result; it MUST respect stated constraints (budget, category, attributes).
- **FR-003**: The agent MUST ask one clarifying question when a detail required to
  act is missing, and MUST take no action until it is resolved.
- **FR-004**: WISMO MUST answer from the order record only.
- **FR-005**: Return eligibility MUST be decided against the **active** policy
  version and the order facts; the decision MUST cite the supporting clause ids.
- **FR-006**: The agent MUST never approve a return or issue a refund; it MAY
  create a return **request** (`REQUESTED`) that a human approves (INV-6).
- **FR-007**: Off-topic requests MUST be redirected with no tool call and no
  fabricated fact (INV-2).
- **FR-008**: Instructions inside user text or retrieved content MUST be treated as
  data, never obeyed; the system prompt MUST NOT be revealed (INV-5).
- **FR-009**: A customer MUST NOT read or act on another customer's order (INV-7).
- **FR-010**: No **user input** — malformed, hostile, off-topic, or oversized —
  MAY end a turn with `reason=error` (INV-1). Infrastructure failures are exempt
  and MUST stay visible (RD-1).
- **FR-011**: The agent MUST degrade observably when a dependency fails (RD-1).

### Key Entities

- **Order**: `id`, `name`, `created_at`, `financial_status`,
  `fulfillment_status`, `delivered_at`, `total`, `currency`, `line_items`.
- **ReturnableItem**: `fulfillment_line_item_id`, `title`, `sku`, `quantity`.
- **PolicyClause**: `id`, `version`, `effective_from`, `text`, and rule fields
  (window, non-returnable tags, restocking fee, exception reasons).
- **ReturnDecision**: `decision` (`eligible` | `ineligible` | `escalate`),
  `reasons`, `cited_clauses`, `restocking_fee_pct`.
- **Product** `[planned]`: `id`, `title`, `description`, `brand`, `color`,
  `price`, `relevance` (ESCI E/S/C/I, from the benchmark only).

## Tool Contracts

The model-facing tools and their JSON schemas (the harness is the only executor).

| Tool | Purpose | Parameters (JSON Schema) |
| --- | --- | --- |
| `get_order_status` | Read one order | `{order_id: string}` |
| `list_returnable_items` | List returnable line items | `{order_id: string}` |
| `propose_return_decision` | Record a proposal (no side effect) | `{order_id: string, fulfillment_line_item_id: string, decision: enum[eligible,ineligible,escalate], cited_clauses: string[]}` |
| `search_products` `[planned]` | Search the catalog | `{query: string, limit: integer}` |

Source of truth: `app/tools/post_purchase.py`, `app/tools/registry.py`. A tool
that changes state is registered only where the gates allow it; `propose_*` tools
have no side effect.

## Real-World Coverage

- **Input distribution**: natural-language discovery requests (with constraints);
  WISMO and return requests; ambiguous requests; off-topic; injection; non-English;
  oversized. Unseen input has a defined behavior (clarify / redirect / refuse /
  escalate).
- **Data quality**: orders and returnable items are validated and normalized at
  the Shopify boundary (`app/data/quality.py`); dirty/missing rows are skipped
  with a count or fail loud (`data.quality`). Policy clauses are versioned;
  a superseded clause MUST NOT be applied.
- **Edge & failure modes**: enumerated above, each with a behavior; enforced by
  the invariants (`docs/invariants.md`) and the input guard.
- **Scale envelope**: keyless latency measured in `docs/scale.md`; the ESCI
  retrieval benchmark is sampled (5k queries) for the gate and run in full
  offline. Model evaluation is bounded by a per-run cost cap.
- **Degradation**: per-dependency fallbacks in `docs/degradation.md`; a degraded
  dependency is observable, never silent.
- **Change evidence**: two-layer evaluation (`reports/post-purchase-eval.md`);
  retrieval benchmark (ESCI) `[planned]`; every change has a change-log entry.

## Evaluation Plan

Two layers, because they answer different questions (see `docs/invariants.md`).

| Layer | Dataset | Metric | Threshold |
| --- | --- | --- | --- |
| Decision | `evals/post_purchase_cases.jsonl` (human-labeled) | `decision_accuracy`, `policy_citation_support` | ≥ 0.90 accuracy; citations non-empty |
| Invariant | `evals/invariant_cases.jsonl` | `invariant_pass_rate`, `no_fail_rate` | **1.000** |
| Retrieval `[planned]` | Amazon ESCI (5k sampled; 130k full) | hit@k, nDCG | ≥ TF-IDF baseline; report vs dense |
| Discovery behavior `[planned]` | `evals/discovery_cases.jsonl` (human-labeled, ~100) | constraint adherence, grounding | ≥ 0.90 |

- **Slices**: by intent, by decision, by window boundary, by policy version, by
  language.
- **Cost/speed**: the large layers are keyless (¥0, seconds); the model layers run
  on a **stratified sample** (100–200 cases, ≈¥1–2, 1–2 min) under the budget cap.
- **Report**: `reports/post-purchase-eval.md`, `evals/report.md`.

## Human-in-the-Loop

- The agent **proposes** a return; a **human approves** it
  (`returnApproveRequest`). The agent's tool set excludes approval and refund.
- Any state-changing action outside the proposal is out of the agent's authority
  (INV-6); the harness enforces it, not the prompt alone.

## Data Provenance & Licensing

| Source | Use | License | Retrieved |
| --- | --- | --- | --- |
| **Shopify Admin API** (dev store) | orders, returnable items | platform API | 2026-09-14 |
| **Retailer policy** (public page) | return rules | public policy page; rules paraphrased + cited | 2026-09-14 |
| **Amazon ESCI** `[planned]` | discovery retrieval labels | **Apache-2.0** | — |

Documented in `docs/shopify-setup.md` and (planned) `docs/data-provenance.md`.
Test data (the dev store's catalog/orders) is generated; the **integration and
domain logic are real** — stated honestly.

## Non-Functional Requirements

- **Latency**: post-purchase p95 ≤ 2 s keyless (`docs/scale.md`); model turns
  bounded by `max_turns`.
- **Cost**: a real evaluation run ≤ `EVAL_MAX_COST_CNY`; the harness stops at the
  cap (HR-12).
- **Security & privacy**: no cross-customer access (INV-7); no PII beyond what a
  tool returns; the system prompt is never revealed (INV-5).
- **Reliability**: no user input yields `reason=error` (INV-1); dependencies
  degrade observably (RD-1).
- **Tenancy**: single-tenant for now; multi-tenant isolation is a documented gap.

## Out of Scope

- Payments, charging, and **actual refunds** (a human does these).
- Fulfillment/warehouse operations.
- Merchant-side pricing, promotions, and campaigns.
- Real-time production traffic; this is a portfolio system with real integrations.

## Rollback & Versioning

- **Prompt**: `config/prompts/post_purchase.md` (and `discovery.md` `[planned]`);
  the rendered-prompt hash is recorded with results (EV-4).
- **Model**: recorded in `evals/report.md`; provider-neutral via `app/ports/llm.py`.
- **Policy**: versioned clauses with `effective_from`; a policy change is a
  reviewed change with before/after.
- **Rollback**: revert the squash-merge commit + rebuild; SQLite schema changes are
  additive. Per-change `blast_radius`/`rollback` live in `specs/change-log.json`.

## Observability

- Every turn emits `turn`/`llm`/`tool` spans to `logs/traces.jsonl`; tool results
  carry a status; the return proposal is recorded in the session log (SL-1).
- Metrics: latency, tokens, cost, tool success/failure; segmentable by intent and
  tool (`app/evaluation/segments.py`).

## Web Acceptance

- **Post-purchase**: send "where is my order?" and see the order card; send "I
  want to return the tent" and see the decision with its cited policy.
- **Discovery** `[planned]`: send "a 2-person tent under $200" and see grounded
  product cards.
- Full click-through steps are in `docs/checkpoints.md`.

## UI Requirements

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | No conversation | Suggestion prompts |
| Loading / Streaming | Request in flight | Streamed text + Stop |
| Success | Reply complete | Answer + product/order/return cards + sources |
| Error | Request fails | Inline message with Retry |
| Disabled | Empty or in-flight input | Send disabled |

### Accessibility

- [x] Keyboard-operable with a visible focus ring; Enter submits
- [x] Streamed updates announced with `aria-live`
- [x] Motion respects `prefers-reduced-motion`
- [x] Interactive elements labeled; text inputs ≥ 16px

### Responsive & Theme

- [x] Shell fills the viewport; no page-level horizontal scroll from 320px
- [x] One aligned column, fluid width (~92%, capped ~80rem)
- [x] Theme follows `prefers-color-scheme`

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Decision accuracy on the human-labeled set ≥ **0.90**.
- **SC-002**: `invariant_pass_rate` = **1.000**; `no_fail_rate` = **1.000**.
- **SC-003**: Every decision cites at least one supporting policy clause.
- **SC-004**: A return is never approved or refunded by the agent (INV-6 holds).
- **SC-005** `[planned]`: ESCI retrieval hit@k ≥ the TF-IDF baseline on the sampled
  benchmark; discovery constraint adherence ≥ 0.90.
- **SC-006**: The local gate passes.

## Measured Results

| Metric | Value | Source |
| --- | --- | --- |
| Decision accuracy | 13/16 (0.812) | `reports/post-purchase-eval.md` |
| Invariant pass rate | 16/17 (0.941) | same |
| No-fail rate | 1.000 | same |
| Cost per full run | ≈ CNY 0.20 | same |

## Assumptions

- One agent, two workflows; discovery and post-purchase share the harness.
- The dev store's data is generated; the integration and domain logic are real.
- ESCI is the discovery corpus because it carries human relevance labels; the
  Shopify catalog does not.
- Multi-tenant isolation and non-English retrieval quality are documented gaps.
