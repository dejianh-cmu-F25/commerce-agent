# Data provenance

Every number in `reports/` rests on a corpus. This says where each one comes from,
whether it is **real** or **generated**, what its licence is, how to rebuild it, and
what breaks without it. The rule the project holds itself to: a claim states its
source, and a fixture that stands in for real data is **labelled as a fixture**.

## Summary

| Corpus | Origin | Real or generated | Licence / access | In git |
| --- | --- | --- | --- | --- |
| Product catalog (3,000) | Amazon Reviews'23 item metadata | **Real** (sampled) | research dataset, not redistributed | no |
| Product reviews (6,548) | Amazon Reviews'23 review text | **Real** (sampled) | research dataset, not redistributed | no |
| Return/shipping policy | Amazon help pages (link + archived link in the SoT) | **Real**, paraphrased and cited | public web page | **yes** (`config/policies/amazon.yaml`) |
| ESCI queries (500) | Amazon Shopping Queries Dataset, `tasksource/esci` | **Real**, human relevance labels | Apache-2.0 | no (fetched by the benchmark) |
| Rule-set cases (216) | derived from the real catalog by deterministic rules | **Generated**, label provable from the data | project | **yes** |
| Attribute cases (28) | generated from real review text | **Generated**, label **is** the review text | project | **yes** |
| Journey cases | authored + LLM-synthesised phrasings + noise variants | **Generated** (phrasings), tools are real | project | **yes** |
| Post-purchase cases (15 + 18) | authored, human-labelled | **Generated**, hand-labelled | project | **yes** |
| Orders | created in the dev store through the Admin API | **Generated**, but real fulfillment objects | project | no |
| Keyless fixtures (`SEED_PRODUCTS`, demo orders) | authored for offline runs | **Generated fixtures** | project | **yes** |

## Details

### Product catalog — **real**
3,000 products (28 categories × 100) streamed from Amazon Reviews'23 metadata and
imported into the Shopify dev store with `scripts/import_catalog.py` (idempotent
`productSet`, tagged `imported:reviews23` and `category:<name>`). Titles, brands,
prices, categories and the feature lists are the dataset's. **There is no stock
data** — every product reports `inventoryItem.tracked=false`, and the mapper treats
untracked inventory as available, so the catalog's stock is a default, not a fact
(which is why `in_stock_only` filters nothing today).

- Rebuild: `uv run python scripts/import_catalog.py` (needs Shopify credentials), then
  `uv run python scripts/sync_catalog.py` to write the retrieval index.
- Index: `data/discovery/products.json` — the document fields plus the `sku` that
  joins a product to its reviews. Gitignored.

### Reviews — **real**
6,548 review rows (title, body, rating, helpful votes, verified, timestamp) exported
from Amazon Reviews'23 into `data/reviews/reviews.sqlite` by
`scripts/import_reviews.py`. Reviews are keyed by the parent ASIN, which the catalog
carries as the product SKU. 86% survive cleaning (`app/reviews/clean.py`); the rest
are markup-only, bare ratings, or too short to contain a claim.

- Rebuild: `uv run python scripts/import_reviews.py`. Gitignored (research licence).

### Policy — **real, paraphrased, cited**
`config/policies/amazon.yaml` is the single source of truth: versioned clauses
(`2026-09` active, `2020-06` superseded) each with an id, paraphrase, machine-readable
rules and the **URL it came from**. The prose the model reads is *rendered* from it
(`app/returns/render.py`), so prose and engine cannot disagree and a superseded
version is never even present in the corpus.

### ESCI — **real, human labels**
500 US queries sampled (`seed=0`) from `tasksource/esci` (Apache-2.0). Each query
carries its own candidates with E/S/C/I relevance labels, which is what makes it the
project's only *external* ground truth for ranking.

- Rebuild: `uv run python evals/esci_bench.py` downloads and caches to `data/esci/`.

### Generated evaluation sets — label provenance
- **Rule set (216)**: each case is produced by a rule over the catalog
  (title substring, brand, colour, category+price ceiling), so its expected ids are
  *derivable* from the data and the set cannot favour a particular retriever.
- **Attribute set (28)**: each case's label is the review text itself — a product is a
  true positive for "runs small" because a customer wrote "runs small". No human
  judgement is encoded.
- **Journey set**: hand-written intents, plus LLM-synthesised phrasings
  (`evals/synth_cases.py`, cached to `synth_cases.jsonl`) and deterministic noise
  variants (`evals/noise.py`). The agent it drives is the real one.
- **Post-purchase set**: hand-labelled decisions, checked against the policy engine
  (`verifier_agrees_with_label`).

### Orders — **generated, real objects**
`scripts/seed_orders.py` creates orders in the dev store through
`orderCreate` → `fulfillmentCreate` → `fulfillmentEventCreate(DELIVERED)`, so
delivery dates are real fulfillment events rather than a hand-set attribute. The
*orders* are ours; the mechanics are the platform's. Fixture orders used by the
keyless evals are labelled fixtures (`evals/order_fixtures.py`).

## What a fresh clone can and cannot run

`data/` is gitignored apart from the policy SoT and the case files, so:

| Without rebuilding | Needs a rebuild first |
| --- | --- |
| `make ci-fast` (keyless: ruff, pyright, pytest, all keyless evals, report checks) | `evals/bench_discovery.py`, `bench_attribute.py`, `esci_rerank.py` (catalog + reviews), `journey_eval.py --real`, `post_purchase_eval.py --real` |

The rebuild order is: `import_catalog.py` → `sync_catalog.py` → `import_reviews.py` →
`seed_orders.py`. The reports that depend on those corpora say so in their
`report-meta` line, and `scripts/check_reports.py` fails when one of them has moved
underneath a report that quotes it.
