# LLM-judge alignment (vs verifiable facts)

- Cases: **16** (post-purchase decision set), skipped (unparseable): 0
- Judge: `deepseek-flash`
- Ground truth: **verifiable** (decision matches the policy engine + citation support)

| | judge says consistent | judge says inconsistent |
| --- | --- | --- |
| **verifiable: consistent** | 1 | 13 |
| **verifiable: inconsistent** | 0 | 2 |

- **Precision: 1.000**  ·  **Recall: 0.071**

## Per case

| case | verifiable | judge |
| --- | --- | --- |
| wismo-01 | ok | bad |
| wismo-02 | ok | bad |
| return-window-in-01 | ok | bad |
| return-window-edge-30 | ok | bad |
| return-window-edge-31 | ok | bad |
| return-window-v1-conflict | ok | bad |
| final-sale-01 | ok | bad |
| damaged-01 | ok | bad |
| damaged-out-of-window | ok | bad |
| restocking-fee-01 | bad | bad |
| warranty-vs-return-01 | bad | bad |
| ambiguous-01 | ok | bad |
| escalate-foreign-order | ok | ok |
| escalate-no-delivery-date | ok | bad |
| injection-01 | ok | bad |
| exchange-01 | ok | bad |

## Notes

- Reporting precision/recall (not raw agreement) because the classes are imbalanced.
- Only the **verifiable** dimensions (decision, citation, grounding) are judged; the
  subjective dimensions (tone, helpfulness) have no objective ground truth and are
  therefore **not** claimed as reliable.

## Interpretation — the judge is NOT usable as-is

The judge was given the order facts, a policy extract, the recorded proposal and
the answer, and asked one binary question (consistent / not). Against the
**verifiable** labels it scored **precision 1.000, recall 0.071**: it called 13
of the 14 verifiably-consistent answers inconsistent.

The likely cause is visible in the prompt: the assistant's answers cite policy
clause ids (`returns#window-default`) that the judge's extract does not enumerate,
so the judge reads a correct citation as "asserts a rule not in the extract".

**Decision: do not gate on the judge.** The deterministic checks (decision
matches the engine, citations ⊆ engine clauses, ids grounded) remain the primary
gate — they are exact and free. The judge is recorded here as an **unvalidated,
exploratory** signal; adopting it would require calibrating the prompt against
the verifiable subset until recall is acceptable (Hamel Husain: a judge you have
not validated is worse than no judge, because it launders noise into a metric).
