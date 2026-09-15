<!-- report-meta: generator=evals/bench_routing.py --write cases=244 sources=evals/discovery_cases.jsonl,evals/attribute_cases.jsonl,evals/bench_routing.py fingerprint=906a3289437d -->
# Discovery: routing between two indexes (phase 3)

Enrichment trades lexical precision for attribute recall, so a single index forces
every query onto one side of that trade. `search_products(evidence=...)` lets the
query choose.

## The ceiling (keyless)

| | lexical rule set (216) | attribute (28) |
| --- | ---: | ---: |
| plain index | 0.991 | 0.179 |
| enriched index | 0.954 | 0.893 |

Weighted by the two classes:

| Strategy | hit@10 over both sets |
| --- | ---: |
| always plain | 0.898 |
| always enriched | 0.947 |
| **oracle-routed** | **0.979** |

## The model's routing

- Cases: 6 per class; routing accuracy **0.583**.

| Class | routed to enriched | routed to plain | no search |
| --- | ---: | ---: | ---: |
| attribute | 1 | 1 | 4 |
| lexical | 0 | 6 | 0 |

An attribute query sent to the plain index retrieves as if the evidence were not
there, and a lexical query sent to the enriched one pays the dilution: the matrix
is where those two mistakes are counted.

### This number is not yet a routing accuracy

**4/6 attribute cases produced no search at all**, so
the figure above mostly measures the input rather than the model's judgement:
`evals/attribute_cases.jsonl` holds *search queries* (e.g. 'Amazon Fashion
runs small'),
and passing one as a customer request is odd enough that the agent asks for
clarification - defensible behaviour, and not what this bench means to score.
The lexical half is clean (every case routed to the plain index), because those
queries read like requests.

**What is established:** the ceiling (oracle routing 0.979 against 0.947 for
always-enriched) and that the flag is honoured end to end. **What is not:**
whether the model sets `evidence` correctly for attribute requests. That needs
the attribute corpus rewritten as requests, which is a follow-up rather than
a re-interpretation of this number.
