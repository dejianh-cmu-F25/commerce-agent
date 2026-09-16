# Query routing between two indexes (design, not yet built)

The C/D/E measurements produced a trade that a single index cannot serve:

| Query class | plain documents | enriched documents | Δ |
| --- | ---: | ---: | ---: |
| Lexical rule set (216) | **0.991** | 0.954 | −0.037 |
| Attribute queries (28, review-labelled) | 0.179 | **0.893** | **+0.714** |

Enrichment buys attribute recall and costs lexical precision, so "always enriched"
and "never enriched" are both wrong for a mixed query stream. The blended crossover
sits near a 5% attribute share (`reports/discovery-attribute.md`), which is why the
shipped configuration enables enrichment - but the honest fix for a store that knows
its queries is to keep **both indexes** and send each query to the one that fits.

## Design

**Model declares, harness routes.** The model already extracts a price ceiling and a
category as tool arguments (`search_products`), so the query class is the same kind of
signal:

```
search_products(query="running shoes that don't run small", evidence=true)
```

- `evidence: false` (default) → the **plain** index: title, vendor, type, tags.
- `evidence: true` → the **enriched** index: the same plus the feature list and cleaned
  review snippets.

Two `CatalogIndex` instances are built at startup from the same snapshot; the tool
picks one per call. Nothing else changes: ids are the same, so the cart, the reviews
tool and the tenancy path are unaffected, and the harness keeps deciding - a model
flag selects an index, it cannot invent a document.

## Why not a classifier

A deterministic classifier over attribute words would be a keyword list pretending to
be understanding, and it would need its own eval. Letting the model set the flag costs
no extra call (it is a tool argument) and is measurable the same way the price/category
constraints are: **does the flag get set when it should?**

## Measurement plan (what would make this more than a design)

1. **Routing accuracy**: on the 28 attribute cases and the 216 lexical cases, measure
   how often the model sets `evidence=true` for the former and `false` for the latter.
   Report the confusion matrix, not a single number.
2. **Routed vs always-plain vs always-enriched** on the union of both sets: routed
   should sit close to the better of the two per class, which is the whole claim.
3. **Cost/latency**: the enriched index is the same size and the same tfidf search, so
   the expected delta is startup time and memory, not per-query latency - measure both
   rather than asserting it.

## What would make it unnecessary

If the store's query mix is known and lopsided, one index is simpler: keep plain when
attribute queries are under ~5% of traffic, enriched when they dominate. Routing earns
its complexity only when both classes are materially present - which is a claim about
traffic, so it needs traffic, or at least the confusion matrix above.
