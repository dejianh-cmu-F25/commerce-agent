# Agent Note: Retrieval quality is measured, keylessly, and ablated

Status: implemented (2026-09-13) — feature `022-retrieval-benchmark`

## Problem

The project had an eval harness for agent behavior (gold scenarios) but nothing
that measured the **retrieval** path on its own. Retrieval is the grounding
mechanism (P4), and the project's retrieval choices (TF-IDF vs dense; memory vs
Chroma) had no evidence behind them. The resume needs "I changed X → metric Y".

## Alternatives considered

- **Judge retrieval only through end-to-end scenario pass/fail.** Cheap, but it
  confounds retrieval with the model and tool loop; a change to retrieval would
  be invisible. Rejected.
- **Use an LLM to grade retrieval.** Unnecessary and nondeterministic; retrieval
  has objective labels (the expected document). Rejected.
- **Benchmark only the configured retriever.** Simpler, but no ablation, so no
  "before/after". Rejected: run three configs on one set.
- **Include OpenAI embeddings as a fourth config.** Would show semantic gains, but
  needs a key and spends money; the keyless path must stay the default (P8).
  Deferred; the harness supports adding it later.

## Decision

- **A labeled retrieval set + pure metrics.** `evals/retrieval_set.py` maps 27
  queries (easy/medium/hard) to the expected policy document; hit-rate@k,
  recall@k, and MRR are pure, deterministic functions
  (`app/evaluation/retrieval_metrics.py`).
- **Ablate the retrieval config.** `evals/bench.py` evaluates TF-IDF (`memory`),
  dense+`hash`, and dense+`chroma` on the same set, with a per-difficulty
  breakdown, and fails the gate if any config's hit-rate@3 drops below 0.7.
- **A committed report.** `evals/report.py` renders `evals/report.md` from the
  result artifacts; the report records the command and the metric definitions.
  Raw JSON is regenerated and not committed.
- **Keyless and deterministic.** The `hash` embedding means no key and no network;
  the metrics are identical across runs.

## Consequences

- Retrieval changes now have a measurable effect: TF-IDF hit-rate@3 0.963 vs
  dense 1.000 on the hard subset; the report records this.
- The corpus is tiny, so the overall hit-rate saturates; the per-difficulty
  breakdown (easy/medium/hard) is where the signal is. A larger corpus and a
  semantic embedding config are the natural next steps.
- Adding a query is a data change (HR-11); the benchmark and report pick it up.
- Latency is reported but not gated (single-machine, indicative).
