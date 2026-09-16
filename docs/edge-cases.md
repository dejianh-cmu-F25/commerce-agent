# Edge & failure boundaries

Constitution **RW-3** requires that edge and failure modes be enumerated with a
defined behavior each. This is the canonical cross-cutting list; a feature spec
adds only feature-specific boundaries. Enforcement is a guard or a test — never
"we thought about it".

| Boundary | Defined behavior | Enforced by |
| --- | --- | --- |
| Empty user message | allowed; the turn runs normally | `tests/unit/test_loop.py` |
| Oversized input (> `max_input_chars`) | refused (`too_long`), no model call | `app/safety/input_guard.py`, `evals/adversarial.py` |
| Prompt injection / override | refused (`injection`), no tool call | `app/safety/input_guard.py`, regression `prompt_injection_refused` |
| Unknown tool name | error `ToolResult`, the turn continues | `app/core/loop.py`, `tests/unit/test_loop.py` |
| Malformed tool JSON | parsed to `{}`; the tool validates and errors | `app/core/loop.py` `_parse_arguments` |
| Ungrounded product/order id | rejected; nothing is added | gold scenario `ungrounded_add_rejected` |
| Dirty price/stock/title | normalized or the row is skipped (repair) / raises (strict) | `app/data/quality.py`, `evals/data_quality.py` |
| Missing knowledge directory | empty corpus; retrieval returns `[]` | `app/knowledge/ingest.py`, `evals/fallbacks.py` |
| Dense retrieval / vector-store failure | degrades to keyless lexical, recorded | `app/core/resilience.py`, `evals/fallbacks.py` |
| LLM provider failure | surfaced `ErrorEvent`; the turn ends `reason=error` | `app/core/loop.py`, `evals/fallbacks.py` |
| Cap exceeded (only when `budget.enabled`) | the turn stops with `BudgetExceeded`; by default spend is recorded and reported with no in-app cap | `app/ports/cost_meter.py` (HR-12) |
| Return outside the policy window | blocked by the gate, no refund | `app/gates/returns.py`, gold scenario `return_out_of_window` |
| Merchant write without approval | staged only; never applied (P3) | `app/gates/provenance.py`, `tests/unit/test_merchant.py` |
| Duplicate ingestion / re-seed | idempotent by id (no duplicates) | `INSERT OR IGNORE`, `tests/unit/test_orders.py` |
| Concurrency (≤ 64 keyless ops) | flat latency, 0 errors | `evals/scale.py`, `docs/scale.md` |
| Session restart | resumed by id from the log (SL-1) | `tests/integration/`, `docs/architecture.md` |

## How a feature adds a boundary

Add a row here (behavior + enforcement) and, if it touches inputs/data/model/
retrieval, a bullet in the spec's `## Real-World Coverage`. The self-review
(`scripts/spec_review.py`) fails a spec whose coverage omits a bullet or leaves it
empty.

## Gaps (honest)

- **Multi-tenant isolation** is untested (single tenant).
- **Long-session memory** (100+ turns) is untested.
- **Large corpus** is measured at 10,000 chunks (`docs/scale.md`); beyond that is
  untested.
- **Large catalog** is measured at 5,000 products (`docs/scale.md`); beyond that
  is untested.
- **Long session** is measured at 100 turns (`docs/scale.md`); longer is untested.
- **Adversarial retrieval queries** (poisoned corpus) are not covered.
- **Non-English retrieval** is measured at 0.000 hit-rate@3 over the English
  corpus (`evals/bench.py`, reported as a gap); closing it needs multilingual
  embeddings.
