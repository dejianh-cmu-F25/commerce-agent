# Evaluation-set audit

- Corpora: **6** · cases: **977**
- Checks: duplicate ids/messages, prompt pollution (8-gram), coverage, sliced results.

## Corpus sizes

| Corpus | Cases | What it grounds |
| --- | ---: | --- |
| `discovery_rule` | 216 | retrieval hit@10 on product metadata |
| `esci` | 500 | nDCG@10 against human ESCI relevance labels |
| `invariant` | 17 | behavioural guardrails (INV-1..8) |
| `journey` | 195 | end-to-end tool-use behaviour (the headline accuracy) |
| `post_purchase` | 16 | return decisions vs the policy engine |
| `synth` | 33 | novel phrasings of the same intents (CheckList MFT) |

## Coverage matrix (intent × corpus)

| Corpus | INV-1 | INV-2 | INV-3 | INV-4 | INV-5 | INV-6 | INV-7 | INV-8 | answer_status | brand | cart | category_price | clarify | colour | discovery | eligible | escalate | ineligible | injection | multi | negative | off_topic | policy | return | title_substring | wismo |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `discovery_rule` |  |  |  |  |  |  |  |  |  | 75 |  | 29 |  | 37 |  |  |  |  |  |  |  |  |  |  | 75 |  |
| `esci` |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `invariant` | 4 | 6 | 2 | 1 | 1 | 1 | 1 | 1 |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| `journey` |  |  |  |  |  |  |  |  |  |  | 20 |  | 3 |  | 55 |  |  |  | 16 | 6 | 10 | 14 | 45 | 12 |  | 14 |
| `post_purchase` |  |  |  |  |  |  |  |  | 2 |  |  |  | 1 |  |  | 7 | 3 | 3 |  |  |  |  |  |  |  |  |
| `synth` |  |  |  |  |  |  |  |  |  |  |  |  |  |  | 12 |  |  |  |  |  |  |  | 10 | 6 |  | 5 |

## Embedded corpora

`synth` is excluded from the duplicate checks: it is the generator input for `journey`, so every synth case reappears there by construction.

## Duplicate ids

None.

## Duplicate messages

None.

## Invariance pairs (same after case/punctuation folding)

- `journey`: noisy-policy-1-lowercase, policy-01
- `journey`: noisy-policy-2-no_punctuation, policy-02
- `journey`: noisy-policy-3-lowercase, policy-03
- `journey`: noisy-policy-4-no_punctuation, policy-04
- `journey`: noisy-policy-5-no_punctuation, policy-05

## Prompt pollution (8-gram overlap with config/prompts)

None — no case shares an 8-word span with a prompt.

## Sliced results (last journey run, real model)

- model `deepseek-flash` · cases **197** · tool accuracy **0.949** · no-fail **1.0**
- strong-signal **165/173** · weak-signal **22/24** · Pass^4 **1.0**

| Intent | Passed |
| --- | ---: |
| `cart` | 20/20 |
| `discovery` | 55/55 |
| `injection` | 16/16 |
| `multi` | 5/6 |
| `negative` | 10/10 |
| `off_topic` | 16/16 |
| `policy` | 46/47 |
| `return` | 4/12 |
| `wismo` | 15/15 |

**Failures:** policy-09, lang-01, lang-03, multi-clarify, synth-05-00, synth-05-01, synth-05-02, synth-05-03, synth-05-04, synth-05-05

## Notes

- `synth` is the generator input for `journey`, so its cases legitimately reappear there; it is excluded from the duplicate checks.
