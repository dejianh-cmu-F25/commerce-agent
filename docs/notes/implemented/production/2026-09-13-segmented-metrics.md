# Agent Note: Metrics are segmented by intent and by tool

Status: implemented (2026-09-13) — feature `030-segmented-metrics`

## Problem

The evaluation reported aggregate numbers: "11/12 scenarios", "Pass@1 0.833". An
aggregate tells you *that* something regressed, never *where*. Under load, a team
that cannot localize a failure stalls — SC-2 was only partially met (traces and
first-error attribution existed; the metrics did not segment).

## Alternatives considered

- **Infer the segment from the tool list.** Fragile: a scenario that calls
  `list_orders` is an *orders* job, not a *list_orders* job. Rejected.
- **Segment only in the real (paid) eval.** Then localization is unavailable in
  the gate and costs money. Rejected.
- **Declare an `intent` per scenario and reuse the sink's tool status.** Chosen.

## Decision

- **Each gold scenario declares an `intent`** (the customer job: `search`,
  `cart`, `checkout`, `orders`, `returns`, `merchant`, `knowledge`, `skills`,
  `memory`).
- **The runner records each tool call's name and status** from the existing
  `ToolResult` events — no new tracing.
- **`app/evaluation/segments.py`** (pure): `by_intent` (pass rate) and `by_tool`
  (calls, errors, error rate). `evals/run.py` writes them to the keyless
  artifact; `evals/report.md` renders them; `check_results.py` validates them.

## Consequences

- A regression now names its intent and its tool (e.g., `returns` → `start_return`)
  instead of only lowering the aggregate.
- The by-tool error rate makes a by-design error (`ungrounded_add_rejected`) and
  a real one equally visible and distinguishable by segment.
- **Residual gaps** (documented in `docs/diagnosability.md`): model and tenant
  segmentation are not implemented (single model, single tenant), and segments
  are measured keylessly, not under the concurrency in `docs/scale.md`.
