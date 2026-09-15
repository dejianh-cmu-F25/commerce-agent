<!-- report-meta: generator=evals/judge.py cases=15 sources=evals/post_purchase_cases.jsonl,evals/judge.py fingerprint=88880c2edfe9 -->

# LLM-judge alignment (vs verifiable facts)

- Cases: **15** (post-purchase decision set), skipped (unparseable): 0
- Judge: `deepseek-flash`
- Ground truth: **verifiable** (decision matches the policy engine + citation support)

| | judge says consistent | judge says inconsistent |
| --- | --- | --- |
| **verifiable: consistent** | 3 | 10 |
| **verifiable: inconsistent** | 0 | 2 |

- **Precision: 1.000**  ·  **Recall: 0.231**

## Per case

| case | verifiable | judge |
| --- | --- | --- |
| wismo-01 | ok | bad |
| wismo-02 | ok | bad |
| return-window-in-01 | ok | bad |
| return-window-edge-30 | ok | ok |
| return-window-edge-31 | ok | bad |
| return-window-v1-conflict | ok | bad |
| final-sale-01 | ok | ok |
| damaged-01 | ok | bad |
| damaged-out-of-window | ok | bad |
| restocking-fee-01 | bad | bad |
| warranty-vs-return-01 | bad | bad |
| ambiguous-01 | ok | bad |
| escalate-foreign-order | ok | ok |
| escalate-no-delivery-date | ok | bad |
| exchange-01 | ok | bad |

## Notes

- Reporting precision/recall (not raw agreement) because the classes are imbalanced.
- Only the **verifiable** dimensions (decision, citation, grounding) are judged; the
  subjective dimensions (tone, helpfulness) have no objective ground truth and are
  therefore **not** claimed as reliable.
