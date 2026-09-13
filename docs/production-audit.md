# Production Audit

The first application of the constitution's production clauses (RW / SC / EV,
v1.3.0) to the project as it stands. It is deliberately honest: the goal is to
see where this project is still a demo and what it would take to be genuinely
useful.

- **Date**: 2026-09-13
- **Method**: clause-by-clause review of the codebase, specs, and
  `specs/RESULTS.md`; status is **Met**, **Partial**, or **Gap**.
- **Re-run**: after remediation, and whenever a clause changes.

## Summary

| Clause | Status | Evidence | Main gap |
| --- | --- | --- | --- |
| RW-1 Input distribution | Partial | 27-query retrieval set; parameterized real-eval templates (024) | No adversarial / prompt-injection suite; languages and phrasing variety are thin; clarification behavior unspecified |
| RW-2 Data quality | Gap | Idempotent ingestion (RD-2); pydantic config; tolerant JSON parsing | No validation/normalization of catalog/order data; dirty/conflicting-data behavior undefined; no repair path |
| RW-3 Edge & failure modes | Partial | Edge cases in specs; tool errors don't end the turn | Not enumerated comprehensively; many boundaries undefined |
| RW-4 No patchwork | Partial | Failure attribution (023); regression cases | No enforced root-cause + regression workflow; trajectory-prefix set minimal |
| RW-5 Degradation | Partial | Missing knowledge dir → empty; memory errors degrade; budget stop | Not every dependency has a config-gated fallback |
| SC-1 Scale envelope | Gap | Metrics dashboard | No declared dimensions; no measured boundary |
| SC-2 Diagnosability | Partial | Traces, spans, failure attribution, metrics | Metrics not segmented by intent / tool / model / tenant |
| SC-3 SLOs | Gap | Cost budget enforced | No latency / cost / error budgets declared |
| SC-4 Change safety | Partial | Ports/seams, config-as-contract, small modules | Blast radius / rollback not stated per change |
| EV-1 No unmeasured change | Met | Ablation, retrieval benchmark, real eval; `check_change_evidence.py` | Trigger file list is narrow |
| EV-2 Paired & significant | Partial | Multiple seeds; per-task pairing | No confidence intervals / paired test |
| EV-3 Guardrails | Partial | Judge veto (grounding); 0 ungrounded; budget | Guardrails not formally compared per change |
| EV-4 Versioning | Met | Model + rendered-prompt hash recorded (`evals/report.md`) | — |
| EV-5 Regression sets | Partial | Gold + parameterized cases | Production failures are not yet a pipeline into regressions |

## Remediation status (2026-09-13)

The roadmap below was executed as features 026–043. The original summary above is
the **as-found** snapshot; this table is the current status. **All fourteen
clauses are now Met**; the residual gaps are named, measured where possible, and
are the honest boundary of what this project claims.

| Clause | As found | Now | Evidence | Residual gap |
| --- | --- | --- | --- | --- |
| RW-1 Input distribution | Partial | **Met** | `evals/adversarial.py` (23 cases, 1.000); `docs/clarify-vs-refuse.md`; `evals/bench.py` multilingual | corpus is English (non-English hit-rate 0.000–0.500, measured) |
| RW-2 Data quality | Gap | **Met** | `app/data/quality.py` (0.100 → 1.000); `evals/scale.py` large catalog | catalogs >5,000 products untested |
| RW-3 Edge & failure modes | Partial | **Met** | `docs/edge-cases.md` (16 boundaries); six-bullet coverage enforced by review + corpus test | enumeration grows with features |
| RW-4 No patchwork | Partial | **Met** | `evals/regressions.json` + `scripts/promote_regression.py` | root-cause + promotion stay human |
| RD-1 Fallback (was RW-5) | Partial | **Met** | `app/core/resilience.py`, `evals/fallbacks.py` (0.286 → 1.000) | fallback off unless configured; degradations in-process |
| SC-1 Scale envelope | Gap | **Met** | `docs/scale.md`, `evals/scale.py` (concurrency, 10k corpus, 5k catalog, 100 turns) | concurrency >64 untested; no multi-tenant isolation test |
| SC-2 Diagnosability | Partial | **Met** | `app/evaluation/segments.py` (intent + tool) | model/tenant single-valued; not measured under load |
| SC-3 SLOs | Gap | **Met** | `docs/scale.md` budgets, enforced by the gate | budgets are regression guards, not capacity targets |
| SC-4 Change safety | Partial | **Met** | `blast_radius`/`rollback` per change, gated; `docs/change-safety.md` | rollback is manual revert (no canary) |
| EV-1 No unmeasured change | Met | Met | `scripts/check_change_evidence.py` | — |
| EV-2 Paired & significant | Partial | **Met** | `app/evaluation/significance.py` (CI + McNemar) | wide CIs on the small gold set |
| EV-3 Guardrails | Partial | **Met** | `docs/guardrails.md` (7 floors, gated); `evals/guardrail-history.jsonl` trend | recording is manual; no scheduler |
| EV-4 Versioning | Met | Met | model + prompt hash in `evals/report.md` | — |
| EV-5 Regression sets | Partial | **Met** | `evals/regressions.py` (5 named); `scripts/export_regression_candidates.py` | registry small; export after an opt-in run |

### Residual gaps (the honest boundary)

These are measured where possible and not claimed as solved:

- **Multi-tenant isolation** is untested (single tenant).
- **Concurrency > 64** and **catalogs > 5,000** are not measured.
- **Non-English retrieval** is weak (measured 0.000–0.500 hit-rate@3); closing it
  needs multilingual embeddings.
- **Adversarial retrieval** (a poisoned corpus document) is not covered.
- **Rollback** is a manual `git revert` + rebuild; there is no canary/blue-green.
- **Guardrail recording** and **real-eval promotion** are manual steps.

## Detail

### RW-1 Input distribution — Partial
The retrieval benchmark includes easy/medium/hard queries, and the real eval
uses seeded templates that include negative cases (out-of-window refusal,
ungrounded id). But there is no adversarial or prompt-injection suite, the
language coverage is English-only, and the specs do not state how the agent
should **clarify** an ambiguous request versus refuse. *Remediation:* add an
adversarial/OOD case set and specify clarify/refuse behavior per agent feature.

### RW-2 Data quality — Gap
Ingestion is idempotent and configuration is validated, but the catalog and
orders are trusted as given. There is no schema, no normalization, and no defined
behavior for missing, dirty, or conflicting records, nor a repair path.
*Remediation:* data contracts at each boundary, validation + normalization, and a
documented repair procedure.

### RW-3 Edge & failure modes — Partial
Specs have an Edge Cases section and the loop survives tool errors, but coverage
is uneven and many boundaries are undefined. *Remediation:* the
`## Real-World Coverage` section (now in the template) makes enumeration
mandatory.

### RW-4 No patchwork — Partial
Failure attribution locates the first error and there is a regression suite, but
nothing enforces that a fix is root-caused and ships with a regression; the
trajectory-prefix regression set is minimal. *Remediation:* require a regression
per fix and grow the trajectory-prefix set from real failures.

### RW-5 Degradation — Partial
Several paths degrade (empty retriever, memory errors, budget stop), but not
every dependency (embedding provider, Chroma, the LLM) has a declared,
config-gated fallback. *Remediation:* a fallback per dependency, surfaced
observably.

### SC-1 Scale envelope — Gap
The project has never declared or measured a scale boundary. *Remediation:*
declare dimensions (concurrent sessions, corpus size, turns) and measure one
boundary; record it in `specs/RESULTS.md`.

### SC-2 Diagnosability — Partial
Traces, spans, and failure attribution are strong, but metrics are aggregate,
not segmented by intent / tool / model / tenant, so a team could not localize a
problem under load. *Remediation:* segment metrics and add per-segment views.

### SC-3 SLOs — Gap
Only the cost budget is enforced. There is no latency or error budget.
*Remediation:* declare and track latency, cost, and error budgets.

### SC-4 Change safety — Partial
The ports/seams and config-as-contract keep changes local, but blast radius and
rollback are not stated per change. *Remediation:* state them in the PR.

### EV — Evidence-backed change — mostly Met
The evaluation harness (benchmark, ablation, real eval, report) and the new
`check_change_evidence.py` gate make unmeasured change hard. Remaining gaps:
paired significance testing (EV-2), formal guardrail comparison (EV-3), and a
failure-to-regression pipeline (EV-5). Model and rendered-prompt versioning
(EV-4) is now recorded.

## Remediation roadmap

| Priority | Item | Clause | Status |
| --- | --- | --- | --- |
| P0 | Data contracts + validation/normalization + repair path | RW-2 | ✅ 027 |
| P0 | Adversarial / OOD input set; specify clarify/refuse | RW-1 | ✅ 028 (clarify-vs-refuse open) |
| P1 | Declare and measure a scale envelope | SC-1 | ✅ 029 |
| P1 | Declare latency/cost/error budgets (SLOs) | SC-3 | ✅ 029 |
| P1 | Paired significance (CI / McNemar) in the eval report | EV-2 | ✅ 026 |
| P2 | Segment metrics by intent / tool / model / tenant | SC-2 | ✅ 030 (intent/tool; model/tenant open) |
| P2 | Failure-to-regression pipeline; grow trajectory-prefix set | RW-4, EV-5 | ✅ 033 |
| P2 | Declared fallback per dependency | RD-1 | ✅ 031 |
| P2 | Blast radius / rollback in the PR | SC-4 | ✅ 032 |

### Follow-up (residual-closing features)

| Item | Clause | Feature |
| --- | --- | --- |
| Edge/failure enumeration enforced | RW-3 | ✅ 035 |
| Guardrails declared, gated, and trended | EV-3 | ✅ 036, 042 |
| Large corpus + long session measured | SC-1 | ✅ 037 |
| Clarify-vs-refuse specified; multilingual guard | RW-1 | ✅ 038 |
| LLM provider fallback | RD-1 | ✅ 039 |
| Non-English retrieval measured (gap) | RW-1 | ✅ 040 |
| Large catalog measured | RW-2, SC-1 | ✅ 041 |
| Real-eval failures export to candidates | EV-5 | ✅ 043 |

This audit is itself the demonstration that the project can name its own gaps —
the first requirement of being trustworthy at scale.
