# Clarify vs refuse

Constitution **RW-1** requires that the agent's behavior on an ambiguous or
out-of-scope request be specified, not left to the model. There are three defined
outcomes:

| Situation | Behavior | Enforced by |
| --- | --- | --- |
| A detail needed to act is missing (which product/order/quantity) | **Clarify**: ask one short question, take **no action** | `config/prompts/system.md`; gold scenario `ambiguous_request_clarifies` |
| Unsafe or out of scope (instruction override, prompt extraction, non-shopping) | **Refuse**: decline briefly, say what you can help with | `app/safety/input_guard.py` (feature 028); `evals/adversarial.py` |
| In scope and unambiguous | **Act** (search, cart, orders, returns, policy) | the tools + gates |

The key rule for clarify: an ambiguous request must not trigger a **write** — no
`add_to_cart`, no `propose_price_change`, no `start_return`. The gold scenario
asserts an empty tool list, so a regression that guesses fails the gate.

## Language coverage

The guard matches instruction-override phrasing in English, Spanish, French,
German, and Chinese (`app/safety/input_guard.py`); benign requests in those
languages are allowed. The retrieval corpus and the gold scenarios are English —
**non-English retrieval quality is not measured** (a residual gap).

## Gaps (honest)

- The clarify policy is prompt-level and asserted by one scenario; there is no
  exhaustive ambiguity suite.
- The guard is lexical; a novel paraphrase in any language can evade it.
