# Journey evaluation (real model)

- Cases: **197**
- Tool accuracy: **0.949**
- No-fail rate: **1.0**
- Pass^4: **1.0** (subset 20)
- Model: `deepseek-flash`

## By intent

| intent | pass |
| --- | --- |
- Strong-signal pass: **165/173**
- Weak-signal pass (non-English / noisy): **22/24**

| intent | pass |
| --- | --- |
| cart | 20/20 |
| discovery | 55/55 |
| injection | 16/16 |
| multi | 5/6 |
| negative | 10/10 |
| off_topic | 16/16 |
| policy | 46/47 |
| return | 4/12 |
| wismo | 15/15 |

## Failures

policy-09, lang-01, lang-03, multi-clarify, synth-05-00, synth-05-01, synth-05-02, synth-05-03, synth-05-04, synth-05-05
