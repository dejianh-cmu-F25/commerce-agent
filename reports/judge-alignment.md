<!-- report-meta: generator=evals/judge.py cases=14 sources=evals/post_purchase_cases.jsonl,evals/judge.py fingerprint=9a241983cd54 -->

# LLM-judge alignment (vs verifiable facts)

- Cases: **14** (post-purchase decision set), skipped (unparseable): 0
- Judge: `deepseek-flash`
- Ground truth: **verifiable** (decision matches the policy engine + citation support)

| | judge says consistent | judge says inconsistent |
| --- | --- | --- |
| **verifiable: consistent** | 1 | 13 |
| **verifiable: inconsistent** | 0 | 0 |

- **Precision: 1.000**  ·  **Recall: 0.071**

## Per case

| case | verifiable | judge |
| --- | --- | --- |
| wismo-01 | ok | bad |
| wismo-02 | ok | bad |
| return-window-in-01 | ok | bad |
| return-window-edge-30 | ok | bad |
| return-window-edge-31 | ok | ok |
| return-window-v1-conflict | ok | bad |
| final-sale-01 | ok | bad |
| damaged-01 | ok | bad |
| damaged-out-of-window | ok | bad |
| restocking-fee-01 | ok | bad |
| warranty-vs-return-01 | ok | bad |
| ambiguous-01 | ok | bad |
| escalate-no-delivery-date | ok | bad |
| exchange-01 | ok | bad |

## Notes

- Reporting precision/recall (not raw agreement) because the classes are imbalanced.
- Only the **verifiable** dimensions (decision, citation, grounding) are judged; the
  subjective dimensions (tone, helpfulness) have no objective ground truth and are
  therefore **not** claimed as reliable.
