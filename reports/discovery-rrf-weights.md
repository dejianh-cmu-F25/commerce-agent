# Discovery: RRF weights (feature 046, step A5)

- Rule set: **216** cases, split **101 train / 115 val** by a stable hash of the case id.
- `rrf_k=60`, candidates per leg `20`, K=10.
- Weights are **selected on train** and the table reports **val**, so the val column is not tuned-on (Qdrant's train/val protocol).

## Grid (hit@10 / MRR)

| weights (sparse:dense) | train hit@10 | train MRR | **val hit@10** | val MRR | val recall |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1:1 ← | 0.990 | 0.839 | **0.983** | 0.818 | 0.803 |
| 2:1 | 0.990 | 0.831 | **0.991** | 0.819 | 0.804 |
| 3:1 | 0.990 | 0.834 | **0.991** | 0.810 | 0.803 |
| 5:1 | 0.990 | 0.827 | **0.991** | 0.813 | 0.804 |
| 3:0.5 | 0.990 | 0.831 | **0.991** | 0.814 | 0.805 |
| 5:0.5 | 0.990 | 0.826 | **0.991** | 0.814 | 0.804 |

## Full-set baselines (same 216 cases)

| config | hit@10 | recall@10 | MRR |
| --- | ---: | ---: | ---: |
| `tfidf` | 0.991 | 0.817 | 0.820 |
| `hybrid-openai` | 0.986 | 0.803 | 0.824 |
| `hybrid-openai-w1:1` | 0.986 | 0.803 | 0.824 |

## What this says

- **Train cannot discriminate**: every weighting scores 0.990 hit@10 there, so the selection step is uninformative and the 'selected' row is merely the default. The val column is reported **for information** - picking the row that wins on val would be tuning on the held-out half.
- On val, down-weighting the dense leg lifts hit@10 0.983 (1:1) -> 0.991 (2:1), reproducing Qdrant's warning that equal weights let the weaker retriever drag the fusion down.
- Even so, weighting only **catches up** to pure lexical (0.986 -> 0.991 on val, vs tfidf 0.991 full-set): the dense leg adds no top-10 hit the lexical leg did not already have on this corpus.

**Decision:** the live discovery path ships on `tfidf` - it matches or beats the weighted fusion, needs no embedding call per query, and has no provider dependency. The weighted hybrid stays wired, and is what the enriched-document step re-measures (recall has room there).

The unweighted row is the shipped default before this step; the baselines are full-set, so they are not directly comparable to a split column.
