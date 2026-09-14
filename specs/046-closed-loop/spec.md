# Feature Specification: Closed-Loop Shopping Agent

**Feature Branch**: `046-closed-loop`

**Created**: 2026-09-15

**Status**: Planned (spec) / In progress

**Input**: One agent that carries a shopper through the **whole journey** —
discover → cart → checkout → order → track → return/exchange → policy Q&A →
account — over **real** systems and a **real** retailer policy. The model
proposes; the harness disposes; money never moves without a human.

> This spec **supersedes** `014-post-purchase` and `045-shopping-agent` (both
> `Superseded by 046`). It is the single source of truth for the journey.
> Sections mark `[new]` (not yet built) or `[carried]` (built under 045).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover a product from a natural-language request (Priority: P1) `[new]`

A shopper describes what they want ("a lightweight 2-person tent under $200 for
summer"); the agent searches a **real catalog**, applies the stated constraints
(budget, category, attributes), compares options, and recommends **grounded**
products. When a detail needed to choose is missing it asks one clarifying
question.

**Why this priority**: discovery drives revenue; it is the largest business lever.

**Independent Test**: Run the discovery behavior set and read constraint
adherence, grounding, and ESCI retrieval (hit@k / nDCG) against the TF-IDF
baseline.

**Acceptance Scenarios**:

1. **Given** "a 2-person tent under $200", **When** the agent searches, **Then**
   every recommended product exists in a tool result and is within budget.
2. **Given** "I want the cheaper one" with no prior comparison, **When** the turn
   runs, **Then** the agent asks one clarifying question and calls no write tool.

---

### User Story 2 - Add to cart and check out (Priority: P1) `[new]`

The shopper adds a product to the cart, reviews the estimated cost, and completes
checkout through an **Agentic-Commerce-Protocol-conformant** flow. **No real
payment is taken**; the payment token is simulated and the order is created in
the store.

**Why this priority**: checkout is the conversion step; the protocol is the
industry direction.

**Independent Test**: An ACP conformance test (session → update → complete)
passes keylessly and asserts no charge is issued.

**Acceptance Scenarios**:

1. **Given** a product and a quantity, **When** the shopper checks out, **Then**
   a checkout session is created, the cart cost is returned, and completing it
   creates an order **without** moving money.
2. **Given** an empty cart, **When** the shopper asks to check out, **Then** the
   agent explains and calls no write tool.

---

### User Story 3 - Answer "where is my order" (WISMO) (Priority: P1) `[carried]`

A shopper asks where their order is; the agent reads the **real order** (status,
items, delivery dates) and answers, without inventing a date.

**Why this priority**: WISMO is 30–50% of support contacts at $5–15 each.

**Independent Test**: Run the WISMO cases and assert `get_order` was called and
no fact was invented.

**Acceptance Scenarios**:

1. **Given** a shipped order, **When** the shopper asks for its status, **Then**
   the agent answers from the order record and cites no fabricated date.

---

### User Story 4 - Decide return/exchange eligibility (Priority: P1) `[carried]`

A shopper wants to return or exchange an item; the agent reads the **active
policy** and the order, decides eligibility (eligible / ineligible / escalate),
explains with **cited clauses**, and **proposes** the action. A human approves
it; the agent never refunds.

**Why this priority**: a wrong refund is a direct loss; a wrong refusal is churn.

**Independent Test**: Run the decision set and read decision accuracy and
citation support; assert the harness validates the proposal at runtime.

**Acceptance Scenarios**:

1. **Given** an item delivered 9 days ago under the active 30-day policy,
   **When** the shopper asks to return it, **Then** the decision is `eligible`
   and the window clause is cited.
2. **Given** a request to "just refund me", **When** the turn runs, **Then** the
   agent proposes a return and never approves or refunds (INV-6).
3. **Given** a proposal that contradicts the policy, **When** the harness
   validates it, **Then** the proposal is rejected or escalated — the model
   cannot bypass the engine.

---

### User Story 5 - Answer a policy question from the single source of truth (Priority: P2) `[new]`

A shopper asks "how long do I have to return something?"; the agent retrieves
the **policy clause** from the single source of truth and answers with the
`clause_id` and the source link.

**Independent Test**: Ask N policy questions; assert every answer cites an
existing clause id and that no superseded clause is used.

**Acceptance Scenarios**:

1. **Given** a policy question, **When** the agent answers, **Then** the answer
   cites a `clause_id` that exists in the policy SoT and is the **active** version.

---

### User Story 6 - Keep the customer's data theirs (Priority: P2) `[carried]`

The agent acts only on the authenticated customer's orders. A request for another
customer's order is refused and escalated; nothing is read.

**Independent Test**: Run the tenancy cases; assert 100% refusal and no read.

**Acceptance Scenarios**:

1. **Given** another customer's order id, **When** the shopper asks about it,
   **Then** the agent refuses and escalates and never reads it (INV-7).

---

### Edge Cases

- **Off-topic / irrelevant** (weather, chit-chat): redirect, call no tool.
- **Missing detail** (which order/item): ask one question, take no action.
- **Foreign order id** (another customer's): refuse and escalate; never read it.
- **Injection** in a message, a product title, or a policy document: treat as
  data; never obey (INV-5).
- **Superseded policy**: apply the active version, not the one the customer cites.
- **Empty / oversized / non-English input**: graceful; never an unhandled error.
- **Out-of-stock item**: explain, propose an alternative, do not add to cart.
- **Simulated payment decline**: report it, create no order, take no money.
- **Malformed tool JSON**: validate at the boundary and fail loud (PB-5).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The agent MUST route a turn by **tool-calling** (the model selects
  tools); it MUST NOT rely on a hardcoded per-intent skill router.
- **FR-002**: Discovery MUST search a catalog and return only products grounded in
  a tool result; it MUST respect stated constraints (budget, category, attributes).
- **FR-003**: The agent MUST ask one clarifying question when a detail required to
  act is missing, and MUST take no action until it is resolved.
- **FR-004**: Cart operations MUST go through the store's cart API; the estimated
  cost MUST come from the system, not the model.
- **FR-005**: Checkout MUST be ACP-conformant (create session → update → complete)
  and MUST NOT take a real payment; the payment token is simulated.
- **FR-006**: WISMO MUST answer from the order record only.
- **FR-007**: Return/exchange eligibility MUST be decided against the **active**
  policy version and the order facts; the decision MUST cite supporting clause ids.
- **FR-008**: The harness MUST validate every `propose_*` decision against the
  policy SoT **at runtime**; a proposal that contradicts the policy MUST be
  rejected or escalated (P3).
- **FR-009**: The agent MUST never approve a return or issue a refund; it MAY
  create a **proposal** that a human approves (INV-6).
- **FR-010**: Policy answers MUST cite a `clause_id` from the policy SoT; a
  superseded clause MUST NOT be applied.
- **FR-011**: Off-topic requests MUST be redirected with no tool call and no
  fabricated fact (INV-2).
- **FR-012**: Instructions inside user text, tool results, or retrieved content
  MUST be treated as data, never obeyed; the system prompt MUST NOT be revealed.
- **FR-013**: A customer MUST NOT read or act on another customer's order (INV-7).
- **FR-014**: No **user input** — malformed, hostile, off-topic, or oversized —
  MAY end a turn with `reason=error` (INV-1). Infrastructure failures are exempt
  and MUST stay visible (RD-1).
- **FR-015**: The agent MUST degrade observably when a dependency fails (RD-1).
- **FR-016**: The model-facing tools MUST be exposed over **MCP** so the surface
  is portable and can be consumed by an external client.

### Key Entities

- **Product**: `id`, `title`, `description`, `brand`, `color`, `price`,
  `category`, `attributes`, `in_stock`.
- **Cart**: `id`, `lines[]` (`merchandise_id`, `quantity`), `cost`, `buyer`.
- **CheckoutSession**: `id`, `cart_id`, `status`, `payment_token` (simulated).
- **Order**: `id`, `name`, `created_at`, `financial_status`,
  `fulfillment_status`, `delivered_at`, `total`, `currency`, `line_items`.
- **ReturnableItem**: `fulfillment_line_item_id`, `title`, `sku`, `quantity`.
- **PolicyClause**: `clause_id`, `version`, `effective_from`, `source_url`,
  `retrieved_at`, `category`, `paraphrase`, rule fields (window, tags, fee,
  exceptions).
- **ReturnDecision**: `decision` (`eligible` | `ineligible` | `escalate`),
  `reasons`, `cited_clauses`, `fee_pct`.
- **Customer**: `id`, `name`, `orders[]` (tenant-scoped).

### Tool Contracts *(MCP)*

The model-facing tools, exposed over MCP (FR-016). The harness is the only
executor (P3, PB-2).

| Server | Tool | Purpose | Parameters (JSON Schema) |
| --- | --- | --- | --- |
| storefront | `search_products` | Search the catalog | `{query: string, limit: integer}` |
| storefront | `get_product` | One product | `{product_id: string}` |
| storefront | `cart_create` | New cart | `{lines: [{merchandise_id: string, quantity: integer}]}` |
| storefront | `cart_get` | Read a cart | `{cart_id: string}` |
| storefront | `cart_lines_update` | Update lines | `{cart_id: string, lines: [{id: string, quantity: integer}]}` |
| storefront | `cart_buyer_identity_update` | Set buyer | `{cart_id: string, email: string, country: string}` |
| storefront | `search_policies` | Policy clauses (SoT) | `{query: string, k: integer}` |
| customer-accounts | `list_orders` | Customer's orders | `{}` |
| customer-accounts | `get_order` | One order | `{order_id: string}` |
| customer-accounts | `list_returnable_items` | Returnable items | `{order_id: string}` |
| customer-accounts | `propose_return` | Record a proposal (no side effect) | `{order_id: string, fulfillment_line_item_id: string, decision: enum[eligible,ineligible,escalate], cited_clauses: string[]}` |
| customer-accounts | `propose_exchange` | Record an exchange proposal | `{order_id: string, fulfillment_line_item_id: string, variant_id: string}` |
| customer-accounts | `get_profile` | Current customer | `{}` |
| checkout | `create_checkout_session` | ACP session | `{cart_id: string}` |
| checkout | `update_checkout` | ACP update | `{session_id: string, address: object}` |
| checkout | `complete_checkout` | ACP complete (simulated) | `{session_id: string}` |

Source of truth: `app/tools/`, `app/mcp/`. `propose_*` tools have no side effect;
`complete_checkout` is HITL-gated.

## Real-World Coverage

- **Input distribution**: natural-language discovery requests (with constraints);
  cart and checkout requests; WISMO; return/exchange; policy questions; ambiguous
  requests; off-topic; injection; non-English; oversized; empty cart;
  out-of-stock. Unseen input has a defined behavior (clarify / redirect / refuse /
  escalate).
- **Data quality**: catalog, cart, orders, and returnable items are validated and
  normalized at the boundary; dirty/missing rows are skipped with a count or fail
  loud. Policy clauses are versioned; a superseded clause MUST NOT be applied.
- **Edge & failure modes**: enumerated above, each with a behavior; enforced by
  the invariants (`docs/invariants.md`) and the input guard.
- **Scale envelope**: keyless latency measured in `docs/scale.md`; the ESCI
  retrieval benchmark is sampled (~5k queries) for the gate and run in full
  offline. Model evaluation is bounded by a per-run cost cap.
- **Degradation**: per-dependency fallbacks in `docs/degradation.md`; a degraded
  dependency is observable, never silent.
- **Change evidence**: keyless layers (retrieval, engine, ACP conformance,
  invariants) run in the gate; model layers run on a stratified sample; every
  change has a change-log entry.

## Evaluation Plan

| Layer | Dataset | Metric | Threshold |
| --- | --- | --- | --- |
| Retrieval (keyless) | Amazon ESCI (sampled) | hit@k, nDCG | ≥ TF-IDF baseline |
| Decision (keyless) | `evals/post_purchase_cases.jsonl` | `decision_accuracy`, citation support | ≥ 0.90 accuracy |
| Engine vs policy | policy-derived labels | agreement | = 1.000 |
| ACP conformance (keyless) | `evals/acp_cases.jsonl` | conformance pass rate | = 1.000 |
| Invariant (keyless) | `evals/invariant_cases.jsonl` | `invariant_pass_rate`, `no_fail_rate` | **1.000** |
| Consistency (model) | stratified journey set | **Pass^k (k=4)** | reported |
| Injection (keyless + model) | AgentDojo-style suite | `injection_block_rate` | ≥ baseline |
| External (model) | **τ-bench retail** | Pass^1 / Pass^k | reported |
| Attribution (model) | failing trajectories | fault assignment + type | reported |

- **Slices**: by intent (discover / cart / checkout / WISMO / return / exchange /
  policy / account), by decision, by window boundary, by policy version, by
  language.
- **Cost/speed**: the large layers are keyless (¥0, seconds); the model layers run
  on a **stratified sample** (100–200 cases, ≈¥1–2) under the budget cap; Pass^k
  (k=4) runs only on a smaller stratified subset.
- **Report**: `reports/closed-loop-eval.md`, `evals/report.md`.

## Human-in-the-Loop

- The agent **proposes** returns/exchanges; a **human approves** them. The agent's
  tool set excludes approval and refund.
- `complete_checkout` and any refund are **HITL-gated**; the harness enforces the
  boundary, not the prompt alone (INV-6).

## Data Provenance & Licensing

| Source | Use | License | Retrieved |
| --- | --- | --- | --- |
| **Amazon ESCI** | discovery retrieval labels | **Apache-2.0** | — |
| **Amazon Reviews'23** | catalog (price/category/attributes) | research dataset — attribute, do not redistribute | — |
| **Amazon return policy** (current + 2020 archive) | policy SoT (paraphrased + cited) | public policy page | 2026-09-14 |
| **Shopify Admin / Storefront API** | orders, returns, cart | platform API | — |
| **Agentic Commerce Protocol** | checkout standard | **Apache-2.0** | — |
| **τ-bench** | external benchmark | **MIT** | — |
| **AgentDojo** | injection benchmark | **MIT** | — |

Documented in `docs/data-provenance.md`. **Honest gaps**: the store's orders and
catalog are imported/generated demo data; the policy is a real retailer's policy
paraphrased with citations; the payment token is simulated. The **integration and
domain logic are real**.

## Non-Functional Requirements

- **Latency**: keyless turn p95 ≤ 10,000 µs (the harness-overhead guard in
  `docs/scale.md`); real-model turn latency is measured separately.
- **Cost**: a real evaluation run ≤ `EVAL_MAX_COST_CNY`; the harness stops at the
  cap (HR-12). The project halts for human review at ¥10 cumulative.
- **Security & privacy**: no cross-customer access (INV-7); no PII beyond what a
  tool returns; the system prompt is never revealed (INV-5).
- **Reliability**: no user input yields `reason=error` (INV-1); dependencies
  degrade observably (RD-1).
- **Tenancy**: simulated auth; tenant isolation enforced by a gate.

## UI Requirements *(browser-visible; WV-6..WV-8)*

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | No conversation | Suggestion prompts |
| Loading / Streaming | Request in flight | Streamed text + Stop |
| Success | Reply complete | Answer + product/cart/order/return/policy cards |
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

## Web Acceptance

- **Discovery**: send "a 2-person tent under $200" and see grounded product cards.
- **Cart/checkout**: add a product and complete the (simulated) checkout; see the
  order created with no charge.
- **Post-purchase**: send "where is my order?" and see the order card; send "I
  want to return the tent" and see the decision with its cited policy.
- **Policy**: ask "how long do I have to return something?" and see the cited
  clause.
- Full click-through steps are in `docs/checkpoints.md`.

## Observability

- Every turn emits `turn`/`llm`/`tool` spans to `logs/traces.jsonl`; tool results
  carry a status; proposals are recorded in the session log (SL-1).
- Metrics: latency, tokens, cost, tool success/failure; segmentable by intent,
  tool, and tenant (`app/evaluation/segments.py`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Decision accuracy on the human-labeled set ≥ **0.90**.
- **SC-002**: `invariant_pass_rate` = **1.000**; `no_fail_rate` = **1.000**.
- **SC-003**: Engine-vs-policy agreement = **1.000** (runtime validation).
- **SC-004**: Every decision and policy answer cites ≥ 1 supporting `clause_id`.
- **SC-005**: A return/exchange is never approved or refunded by the agent (INV-6).
- **SC-006**: ACP conformance pass rate = **1.000**; no real payment is taken.
- **SC-007**: ESCI retrieval hit@k ≥ the TF-IDF baseline.
- **SC-008**: Cross-customer access attempts are refused 100% (INV-7).
- **SC-009**: `Pass^k (k=4)` is reported for the journey set.
- **SC-010**: The local gate passes.

## Measured Results

| Metric | Value | Source |
| --- | --- | --- |
| Decision accuracy | 13/16 (0.812) *(baseline, 045)* | `reports/post-purchase-eval.md` |
| Invariant pass rate | 16/17 (0.941) *(baseline)* | same |
| No-fail rate | 1.000 *(baseline)* | same |

> Targets (SC-001/002) are **not yet met**; closing them is part of this feature.

## Out of Scope

- Real payments, charging, and actual refunds (a human does these).
- Real OAuth / Shopify customer accounts (simulated).
- Fulfillment / warehouse operations.
- Merchant-side pricing, promotions, and campaigns.
- Real-time production traffic; this is a portfolio system with real integrations.

## Rollback & Versioning

- **Prompt**: `config/prompts/` (journey prompt); the rendered-prompt hash is
  recorded with results (EV-4).
- **Model**: recorded in `evals/report.md`; provider-neutral via `app/ports/llm.py`.
- **Policy**: the SoT (`config/policies/`) is versioned with `effective_from`; a
  policy change is a reviewed change with before/after.
- **Rollback**: revert the squash-merge commit + rebuild; schema changes are
  additive. Per-change `blast_radius`/`rollback` live in `specs/change-log.json`.

## Known Gaps

Carried from 045 and tracked here; each is a candidate task in `tasks.md`.

- The 045 evaluation harness did not enable the input guard in the eval agent.
- `cited_clauses` was not populated → citation support was unmeasured.
- Decision accuracy 0.812 and invariant 0.941 are below target.
- The Scenario Runner (`/scenarios`) is wired but its spec (016) is archived.
- The legacy storefront path (`app/tools/orders.py`, `app/returns/policy.py`)
  still serves production until the migration completes.

## Assumptions

- One agent, one tool-calling loop, many workflows; all workflows share the harness.
- The catalog and orders are imported/generated; the integration and domain logic
  are real.
- ESCI is the discovery evaluation corpus (human labels); Reviews'23 is the
  catalog (price/attributes).
- Multi-tenant isolation and non-English retrieval quality are documented gaps.
