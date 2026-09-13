# Diagnosability

Constitution **SC-2** requires that every failure be attributable (trace + first
error) and that metrics be **segmentable** (by intent, tool, model, tenant) so a
team can localize a problem under load.

## What exists

- **Traces & spans**: every turn emits `turn` / `llm` / `tool` spans
  (`app/core/tracing.py`, `logs/traces.jsonl`); `GET /traces` renders them.
- **First-error attribution**: `app/evaluation/failure.py` labels the first error
  (feature 023), so a failed run is attributed, not just "failed".
- **Segmented metrics** (feature 030): the keyless gold run is grouped
  - **by intent** — the customer job (`search`, `cart`, `orders`, `returns`, …),
  - **by tool** — calls and error rate per tool name,
  and rendered into `evals/report.md` (`## Segmented metrics`). A regression shows
  which intent and which tool it lives in, not just an aggregate pass rate.

Run it directly:

```bash
uv run python evals/run.py
```

## Gaps (honest)

- **Model**: only one model is in the keyless run; the real eval records the
  model but does not yet split metrics per model (there is one).
- **Tenant**: the harness is single-tenant (`EVAL_CUSTOMER`); there is no
  per-tenant segmentation test.
- **Under load**: segmentation is measured keylessly, not under the concurrency
  in `docs/scale.md`; combining them (segments at 64 concurrent) is future work.
