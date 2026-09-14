# Plan: Closed-Loop Shopping Agent

**Feature**: `046-closed-loop` | **Spec**: [spec.md](./spec.md) | **Tasks**: [tasks.md](./tasks.md)

## Summary

Turn the post-purchase-only agent into a **closed-loop** shopping agent: discovery →
cart → checkout (ACP-sim) → order → WISMO → return/exchange → policy Q&A → account.
One agent, one tool-calling loop, one harness. The model proposes; the harness
disposes; money never moves without a human.

## Key decisions

| # | Decision | Why |
| --- | --- | --- |
| 1 | **Tool-calling, not a skill router** | the model selects tools; a per-intent script is brittle and duplicates the loop |
| 2 | **Policy single source of truth** (`config/policies/`) + **derived** views | the current 4 hand-maintained copies drift; one source makes drift structurally impossible |
| 3 | **Policy exposed as a tool** (`search_policies`) | the model must retrieve and cite clauses, not read hardcoded prompt rules |
| 4 | **Runtime validation** (`decide_return` inside the write path) | "harness disposes" must hold at runtime, not only in the offline eval |
| 5 | **Same pipeline, config-switched adapters** | replace the wiring/engine/prompt/catalog default; keep ports + keyless fallbacks (P8) |
| 6 | **MCP tool surface** | portable; aligns with Shopify's official Storefront/Customer MCP capability set |
| 7 | **Checkout + auth simulated** (ACP-conformant) | demonstrate the protocol without real money or OAuth |
| 8 | **Small import (~200–500 products)** | keep CI fast and model cost bounded |
| 9 | **Evaluation = keyless + sampled model + Pass^k + τ-bench + AgentDojo** | scale without cost; external comparability |

## Architecture

```
Surfaces   web(SSE) · CLI
MCP        ① storefront  ② customer-accounts  ③ checkout(ACP-sim)
Harness    policy_eligibility gate · approval gate · deterministic engine ·
           invariants · input guard · budget · tracer
Ports      llm · catalog · cart · checkout · post_purchase · policy ·
           retriever · auth · tracer · session · cost
Adapters   deepseek|mock · reviews23|seed · shopify|memory · acp_sim · dense|tfidf
Core       loop · session log(SL-1) · settings · prompts
SoT        policies · catalog · orders · customers
```

Dependencies point inward; adapters implement ports and are injected by config
(PB-1/PB-2).

## Policy: single source of truth

```
SoT  config/policies/<retailer>.yaml   (clause_id, version, effective_from,
     source_url, retrieved_at, category, paraphrase, rules)
  ├─ render → config/knowledge/policies/*.md   (build artifact, not hand-edited)
  ├─ load   → decide_return(engine)             (runtime validation)
  ├─ expose → MCP search_policies               (retrieval + citation)
  └─ delete → settings.returns.window_days      (no third copy)
prompt holds only the decision *procedure*, never the numbers/tags/fees
```

## Migration (legacy → closed loop)

| Step | Action | Acceptance |
| --- | --- | --- |
| 1 | Add the policy SoT + `decide_return` gate; **dual-run** against the legacy gate | agreement = 100% |
| 2 | Rewire `web/main.py` to the new tool set + journey prompt | smoke passes |
| 3 | Verify (invariants + decision set + integration) | no regression |
| 4 | Remove legacy (`orders.start_return`, `returns/policy.py`, `ReturnEligibilityGate`, `settings.returns.window_days`) | no references |
| 5 | One change-log entry + rollback point per step | gate green |

## Phases

| Phase | Deliverable | Acceptance |
| --- | --- | --- |
| **P0** | Policy SoT + renderer + `decide_return` runtime gate | dual-run agreement; version-conflict cases pass |
| **P1** | 3 MCP servers + ports/adapters | MCP contract tests pass |
| **P2** | Reviews'23 import (~200–500) + `search_products` + ESCI benchmark | hit@k ≥ TF-IDF baseline |
| **P3** | Shopify cart adapter + ACP-sim checkout | ACP conformance; no charge |
| **P4** | Simulated auth + tenancy gate | INV-7 refusals 100% |
| **P5** | Pass^k(4) + τ-bench + AgentDojo + error attribution | report produced within budget |
| **P6** | Closed-loop UI | full journey click-through |
| **P7** | Provenance / audit / docs | audit clean |

## Evaluation

- **Keyless (gate)**: ESCI retrieval, engine decisions, engine-vs-policy agreement,
  ACP conformance, invariants, injection (keyless parts).
- **Model (sampled)**: decision accuracy, citation support, Pass^k (k=4 on a small
  subset), τ-bench retail, AgentDojo, fault attribution.
- **Budget**: per-run cap (`EVAL_MAX_COST_CNY`); the project halts for human review
  at ¥10 cumulative.

## Risks & rollback

| Risk | Mitigation |
| --- | --- |
| Migration regression | dual-run + stepwise switch + a rollback point per step |
| Model cost (Pass^k ×4) | small stratified subset + hard budget cap |
| License (Reviews'23) | attribute, do not redistribute, research use only |
| Shopify network/limits | port + keyless fallback; integration tests opt-in |

## Traceability

Spec-covered clauses this feature implements: P3, P4, P5, P7, P8, PB-1, PB-2, SL-1,
SL-2, WV-1/3/5/6/7/8/9, OB-1..5, HR-8/9/10/12, RD-1, RD-2, RW-1..4, SC-1..4,
EV-1..5. Gate-covered: P1, EV-1/6, DR-1..5, TT-1..3, GH-4.
