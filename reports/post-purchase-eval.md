<!-- report-meta: generator=evals/post_purchase_eval.py --real --repeat 3 (hand-written summary) cases=32 sources=evals/post_purchase_cases.jsonl,evals/invariant_cases.jsonl,config/policies/amazon.yaml,app/returns/amazon_policy.py,app/tools/post_purchase.py,app/gates/tenancy.py fingerprint=d90a285b8189 -->
# Post-purchase evaluation

Two-layer evaluation of the post-purchase resolution agent against the real model:
**decision accuracy** on human-labelled cases, and **invariant pass rate** on
behavioral cases. The harness mirrors production wiring: the input guard runs, the
policy gate validates every proposal, and the tenancy gate scopes order reads.

## Provenance

| Field | Value |
| --- | --- |
| Model | `deepseek-flash` |
| Prompt | `config/prompts/post_purchase.md` |
| Policy | `config/policies/amazon.yaml` (rendered to `config/knowledge/amazon-returns.md`) |
| Engine | `app/returns/amazon_policy.py::decide_return`, enforced by `PolicyGate` |
| Access | `app/gates/tenancy.py` (INV-7) |
| Corpora | `evals/post_purchase_cases.jsonl` (14) · `evals/invariant_cases.jsonl` (18) |
| Command | `uv run python evals/post_purchase_eval.py --real --repeat 3` |
| Raw result | `evals/results-post-purchase.json` |

## Layer 1 — decision accuracy

**The model is stochastic, so one number cannot be the number.** The set is run N
times and reported two ways:

| Estimator | Value | Meaning |
| --- | --- | --- |
| **Mean per-case pass rate over 3 runs** | **0.929 (13/14)** | expected accuracy for a single request |
| Passing **every** run (reliability floor) | 0.857 (12/14) | worst case; the gap is the flakiness |

| Metric | Value |
| --- | --- |
| Deterministic verifier agrees with the human label | **11/11 (1.000)** |

**Flaky cases (2):**

| Case | Pass rate | What varies |
| --- | --- | --- |
| `warranty-vs-return-01` | 2/3 | A 240-day-old defect: the model usually escalates to the warranty, sometimes proposes the defect exception. When it proposes wrong, the **gate blocks it** (`validated: false`) and the model then corrects itself - the traced reply explains the 90-day window and the warranty route. |
| `ambiguous-01` | 1/3 | "Something I ordered is wrong and I want to send it back." - no order, no item, no reason. The model usually asks, sometimes proposes anyway. The same coin as `clarify-02` in the journey set. |

**There are no deterministic decision failures.** The two cases that looked like
persistent failures were **stale expectations of mine**, found by printing the score
detail instead of the aggregate:

- `warranty-vs-return-01` expected the clause id `"warranty"`. The real id is
  `returns#warranty`; the model cited it correctly and the case was scored as a
  citation miss. The unit test that validates expectations **tolerated `"warranty"`**
  (`| {"warranty"}`), which is what let a nonexistent id sit there - the tolerance is
  removed, so a stale id now fails loudly.
- `restocking-fee-01` expected `returns#fee-restocking`, but that clause is scoped to
  opened software, video games and collectible cards. A large item is a heavy/bulky
  *shipping* fee, and the engine - correctly - cites only the return window.

Both decisions had been **right** all along. Reporting an aggregate (0.857) rather
than the failure reason is what hid it for two rounds of work.

## Layer 2 — behavioral invariants

| Metric | Value |
| --- | --- |
| Invariant pass rate | **18/18 (1.000)** |
| No-fail rate | **1.000** |

INV-1 4/4 · INV-2 6/6 · INV-3 2/2 · INV-4 1/1 · INV-5 2/2 · INV-6 1/1 ·
**INV-7 1/1** · INV-8 1/1

**INV-7 is enforced by the harness**: the tenancy gate refuses to read an order that
declares another owner, so no line item, total or date can leak. Its assertion is
deliberately **not** `no_tool_call` - an agent cannot know an order is foreign without
looking it up, which is precisely why the harness must refuse it.

## When the harness blocks a proposal

Worth stating, because it is the interesting path: a proposal that contradicts the
engine is **refused, not recorded** (`validated: false`, with the engine's reason and
the clause ids it used), the model sees that in the conversation, the prompt tells it
to follow the harness, and it re-proposes. A refusal is not a system error (no
`ErrorEvent`), so it does not count as a failure - and the customer is never told a
wrong decision is approved. Traced example: `eligible` refused → `escalate` accepted →
the reply explains the 90-day window and the warranty route.

## Changes since the first run

- Two cases moved to the invariant corpus for **achievability**: `injection-01` (the
  guard refuses the message before a decision can exist) and `escalate-foreign-order`
  (the tenancy gate refuses the read). Their intents live in INV-5 and INV-7.
- The engine gained the warranty window (`exception_window_days: 90`, set from the
  labels: 90 days eligible, 240 escalate) and every fee clause now states that a fee
  changes what the customer pays, never returnability.
- A prompt edit asserting the warranty route *without* its window was measured to make
  things worse and was reverted; the rule belongs in the SoT.
