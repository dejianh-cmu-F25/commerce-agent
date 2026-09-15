# LLM-judge alignment (vs verifiable facts)

- Cases: **16** (post-purchase decision set), skipped (unparseable): 4
- Judge: `deepseek-flash`
- Ground truth: **verifiable** (decision matches the policy engine + citation support)

| | judge says consistent | judge says inconsistent |
| --- | --- | --- |
| **verifiable: consistent** | 0 | 2 |
| **verifiable: inconsistent** | 1 | 9 |

- **Precision: 0.000**  ·  **Recall: 0.000**

## Per case

| case | verifiable | judge |
| --- | --- | --- |
| wismo-02 | ok | bad |
| return-window-in-01 | bad | bad |
| return-window-edge-30 | bad | bad |
| return-window-edge-31 | bad | bad |
| return-window-v1-conflict | bad | bad |
| damaged-out-of-window | bad | bad |
| restocking-fee-01 | bad | bad |
| warranty-vs-return-01 | bad | bad |
| escalate-foreign-order | ok | bad |
| escalate-no-delivery-date | bad | ok |
| injection-01 | bad | bad |
| exchange-01 | bad | bad |

## Notes

- Reporting precision/recall (not raw agreement) because the classes are imbalanced.
- Only the **verifiable** dimensions (decision, citation, grounding) are judged; the
  subjective dimensions (tone, helpfulness) have no objective ground truth and are
  therefore **not** claimed as reliable.
