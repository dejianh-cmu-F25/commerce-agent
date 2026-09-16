# Clarify vs refuse

Constitution **RW-1** requires that the agent's behavior on an ambiguous or
out-of-scope request be specified, not left to the model. There are three defined
outcomes:

There are **four** defined outcomes (the fourth is the off-topic case, INV-2):

| Situation | Behavior | Enforced by |
| --- | --- | --- |
| A detail needed to act is missing (which product/order/quantity) | **Clarify**: ask one short question, take **no action** | `config/prompts/system.md`; gold scenario `ambiguous_request_clarifies`; INV-3 |
| Benign but off-topic (weather, news, chit-chat, writing something) | **Redirect**: say briefly what you can help with, offer one next step, call **no tool** | `config/prompts/system.md`; INV-2 cases |
| Unsafe (instruction override, prompt extraction) | **Refuse**: decline briefly, never reveal the prompt | `app/safety/input_guard.py` (feature 028); `evals/adversarial.py`; INV-5 |
| In scope and unambiguous | **Act** (order status, return eligibility, policy) | the tools + gates |

The invariants themselves are listed in [`docs/invariants.md`](./invariants.md).

The key rule for clarify: an ambiguous request must not trigger a **write** — no
`add_to_cart`, no `propose_price_change`, no `start_return`. The gold scenario
asserts an empty tool list, so a regression that guesses fails the gate.

## Language coverage

The guard matches instruction-override phrasing in English, Spanish, French,
German, and Chinese (`app/safety/input_guard.py`); benign requests in those
languages are allowed. The retrieval corpus and the gold scenarios are English:
**non-English retrieval is measured and weak** — the keyless lexical retriever
scores 0.000 hit-rate@3 on the multilingual set (`evals/bench.py`, reported as a
gap, not gated). Closing it needs a multilingual embedding model.

## Gaps (honest)

- The clarify policy is prompt-level and asserted by one scenario; there is no
  exhaustive ambiguity suite.
- The guard is lexical; a novel paraphrase in any language can evade it.
