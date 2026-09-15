# Journey evaluation (real model)

- Cases: **151**
- Tool accuracy: **0.96**
- No-fail rate: **1.0**
- Pass^4: **1.0** (subset 20)
- Model: `deepseek-flash`

## By intent

| intent | pass |
| --- | --- |
- Strong-signal pass: **124/127**
- Weak-signal pass (non-English / noisy): **21/24**

| intent | pass |
| --- | --- |
| cart | 20/20 |
| discovery | 42/43 |
| injection | 16/16 |
| multi | 5/6 |
| off_topic | 16/16 |
| policy | 34/35 |
| return | 3/6 |
| wismo | 9/9 |

## Failures

discovery-23, policy-09, lang-01, lang-02, lang-03, multi-clarify
