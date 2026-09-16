<!-- report-meta: generator=external tau-bench run (no local corpus) cases=20 sources= fingerprint=da39a3ee5e6b -->

# τ-bench (retail): external benchmark

- Domain: **retail** (tool + policy + simulated user)
- Tasks: **20** (subset of the 115-task retail test split)
- Model: `deepseek-chat` (agent + user simulator), temperature 0
- **Pass^1: 0.850** (17/20 solved)
- Run at: 2026-09-15T10:55:58+00:00

## Per-task reward

| task | reward |
| --- | --- |
| 0 | 1.0 |
| 1 | 1.0 |
| 2 | 1.0 |
| 3 | 1.0 |
| 4 | 1.0 |
| 5 | 1.0 |
| 6 | 1.0 |
| 7 | 1.0 |
| 8 | 1.0 |
| 9 | 1.0 |
| 10 | 1.0 |
| 11 | 1.0 |
| 12 | 1.0 |
| 13 | 1.0 |
| 14 | 1.0 |
| 15 | 1.0 |
| 16 | 1.0 |
| 17 | 0.0 |
| 18 | 0.0 |
| 19 | 0.0 |

## Notes

- τ-bench is the canonical external benchmark for tool-agent-user interaction with
  policies; it is **not** our harness. Running it with the project's model gives an
  external reference for the model choice, independent of our own evals.
- This is a **20-task subset**, so it is not directly comparable to the published
  115-task leaderboard numbers; it is a real, reproducible external datapoint.
- The benchmark ships its own policy and tools; our project's harness is measured
  separately by `evals/journey_eval.py`.
