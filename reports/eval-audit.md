<!-- report-meta: generator=evals/eval_audit.py --write cases=1004 sources=/Users/dejianhuang/Documents/AI_Agent/commerce-agent/evals/journey_eval.py,/Users/dejianhuang/Documents/AI_Agent/commerce-agent/evals/synth_cases.jsonl,/Users/dejianhuang/Documents/AI_Agent/commerce-agent/evals/post_purchase_cases.jsonl,/Users/dejianhuang/Documents/AI_Agent/commerce-agent/evals/invariant_cases.jsonl,/Users/dejianhuang/Documents/AI_Agent/commerce-agent/evals/discovery_cases.jsonl,/Users/dejianhuang/Documents/AI_Agent/commerce-agent/evals/attribute_cases.jsonl fingerprint=1e193183b2fd -->

# Evaluation-set audit

- Corpora: **7** · cases: **1004**
- Checks: duplicate ids/messages, prompt pollution (8-gram), coverage, sliced results.

## Corpus sizes

| Corpus | Cases | What it grounds |
| --- | ---: | --- |
| `attribute` | 28 | attribute queries labelled by review text (what enrichment buys) |
| `discovery_rule` | 216 | retrieval hit@10 on product metadata |
| `esci` | 500 | nDCG@10 against human ESCI relevance labels |
| `invariant` | 18 | behavioural guardrails (INV-1..8) |
| `journey` | 195 | end-to-end tool-use behaviour (the headline accuracy) |
| `post_purchase` | 14 | return decisions vs the policy engine |
| `synth` | 33 | novel phrasings of the same intents (CheckList MFT) |

## Coverage matrix (intent × corpus)

| Corpus | INV-1 | INV-2 | INV-3 | INV-4 | INV-5 | INV-6 | INV-7 | INV-8 | answer_status | brand | broke after | cart | category_price | clarify | colour | discovery | eligible | escalate | flimsy | hard to use | ineligible | injection | leaks | multi | negative | off_topic | policy | poor quality | return | runs small | smells | stopped working | title_substring | too heavy | too tight | wismo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `attribute` |  |  |  |  |  |  |  |  |  |  | 3 |  |  |  |  |  |  |  | 3 | 1 |  |  | 3 |  |  |  |  | 3 |  | 3 | 3 | 3 |  | 3 | 3 |  |
| `discovery_rule` |  |  |  |  |  |  |  |  |  | 75 |  |  | 29 |  | 37 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 75 |  |  |  |
| `esci` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `invariant` | 4 | 6 | 2 | 1 | 2 | 1 | 1 | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `journey` |  |  |  |  |  |  |  |  |  |  |  | 20 |  | 3 |  | 55 |  |  |  |  |  | 16 |  | 6 | 10 | 14 | 45 |  | 12 |  |  |  |  |  |  | 14 |
| `post_purchase` |  |  |  |  |  |  |  |  | 2 |  |  |  |  | 1 |  |  | 7 | 2 |  |  | 2 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `synth` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 12 |  |  |  |  |  |  |  |  |  |  | 10 |  | 6 |  |  |  |  |  |  | 5 |

## Embedded corpora

`synth` is excluded from the duplicate checks: it is the generator input for `journey`, so every synth case reappears there by construction.

## Duplicate ids

None.

## Duplicate messages

- `attribute` (within): attr-runs-small-1, attr-runs-small-2, attr-runs-small-3
- `attribute` (within): attr-too-tight-1, attr-too-tight-2
- `attribute` (within): attr-leaks-1, attr-leaks-2
- `attribute` (within): attr-smells-1, attr-smells-2, attr-smells-3
- `attribute` (within): attr-broke-after-1, attr-broke-after-2
- `attribute` (within): attr-flimsy-2, attr-flimsy-3
- `attribute` (within): attr-poor-quality-1, attr-poor-quality-2, attr-poor-quality-3

## Invariance pairs (same after case/punctuation folding)

- `journey`: noisy-policy-1-lowercase, policy-01
- `journey`: noisy-policy-2-no_punctuation, policy-02
- `journey`: noisy-policy-3-lowercase, policy-03
- `journey`: noisy-policy-4-no_punctuation, policy-04
- `journey`: noisy-policy-5-no_punctuation, policy-05
- `attribute`: attr-runs-small-1, attr-runs-small-2, attr-runs-small-3
- `attribute`: attr-too-tight-1, attr-too-tight-2
- `attribute`: attr-leaks-1, attr-leaks-2
- `attribute`: attr-smells-1, attr-smells-2, attr-smells-3
- `attribute`: attr-broke-after-1, attr-broke-after-2
- `attribute`: attr-flimsy-2, attr-flimsy-3
- `attribute`: attr-poor-quality-1, attr-poor-quality-2, attr-poor-quality-3

## Prompt pollution (8-gram overlap with config/prompts)

None — no case shares an 8-word span with a prompt.

## Sliced results (last journey run, real model)

- model `deepseek-flash` · cases **197** · tool accuracy **0.97** · no-fail **1.0**
- strong-signal **168/173** · weak-signal **23/24** · Pass^4 **1.0**

| Intent | Passed |
| --- | ---: |
| `cart` | 20/20 |
| `clarify` | 2/3 |
| `discovery` | 54/55 |
| `injection` | 16/16 |
| `multi` | 5/6 |
| `negative` | 10/10 |
| `off_topic` | 14/14 |
| `policy` | 44/45 |
| `return` | 10/12 |
| `reviews` | 2/2 |
| `wismo` | 14/14 |

**Failures:** discovery-03, policy-09, lang-03, multi-clarify, clarify-02, synth-05-05

## Notes

- `synth` is the generator input for `journey`, so its cases legitimately reappear there; it is excluded from the duplicate checks.
