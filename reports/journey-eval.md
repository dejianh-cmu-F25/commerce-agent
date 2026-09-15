<!-- report-meta: generator=evals/journey_eval.py --real cases=197 sources=evals/journey_eval.py,evals/synth_cases.jsonl fingerprint=d47a3aaa8fb8 -->

# Journey evaluation (real model)

- Cases: **197**
- Tool accuracy: **0.97**
- No-fail rate: **1.0**
- Pass^4: **1.0** (subset 20)
- Model: `deepseek-flash`

## By intent

| intent | pass |
| --- | --- |
- Strong-signal pass: **168/173**
- Weak-signal pass (non-English / noisy): **23/24**

| intent | pass |
| --- | --- |
| cart | 20/20 |
| clarify | 2/3 |
| discovery | 54/55 |
| injection | 16/16 |
| multi | 5/6 |
| negative | 10/10 |
| off_topic | 14/14 |
| policy | 44/45 |
| return | 10/12 |
| reviews | 2/2 |
| wismo | 14/14 |

## Failures

discovery-03, policy-09, lang-03, multi-clarify, clarify-02, synth-05-05
