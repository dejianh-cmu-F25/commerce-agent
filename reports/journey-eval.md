# Journey evaluation (real model)

- Cases: **121**
- Tool accuracy: **0.983**
- No-fail rate: **1.0**
- Pass^4: **1.0** (subset 20)
- Model: `deepseek-flash`

## By intent

| intent | pass |
| --- | --- |
| cart | 20/20 |
| discovery | 29/30 |
| injection | 16/16 |
| off_topic | 16/16 |
| policy | 29/30 |
| return | 3/3 |
| wismo | 6/6 |

## Failures

discovery-23, policy-09
