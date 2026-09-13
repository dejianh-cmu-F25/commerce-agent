# Regressions: from failure to a durable guard

Constitution **RW-4** ("no patchwork") requires that a fix be root-caused and ship
with a regression; **EV-5** requires that failures become regressions. This is the
pipeline.

## The registry

`evals/regressions.json` is a committed list of named regressions. Each entry has:

| Field | Meaning |
| --- | --- |
| `id` | stable identifier |
| `source` | where the failure came from (incident, audit clause, feature) |
| `root_cause` | **why** it happened — required |
| `check` | the name of a keyless check in `evals/regressions.py` |

The `check` is resolved from a fixed map, so a promoted entry cannot inject code
and a broken reference fails the gate (loudly, not silently).

## The workflow

1. **A failure is observed** — a red gold scenario, a real-eval failure
   (`evals/results-real.json`), or a production incident.
2. **Root-cause it.** Write the cause, not the symptom. If you cannot state the
   cause, you do not yet have a fix.
3. **Promote it:**
   ```bash
   uv run python scripts/promote_regression.py \
     --id dense_outage_falls_back \
     --source "audit RD-1 / feature 031" \
     --root-cause "a vector-store outage raised out of the knowledge tool" \
     --check dense_failure_falls_back
   ```
   Promotion **refuses an empty root cause** and is idempotent by `id`.
4. **Run the gate.** `evals/regressions.py` runs every registered check and fails
   the gate on any failure; the coverage is rendered into `evals/report.md`.

## Adding a check

A regression references a check by name; if the name does not exist the gate
fails. To add a genuinely new guard, add a keyless async function to
`evals/regressions.py` and register it in `CHECKS`.

## Gaps (honest)

- Promotion is manual; there is no automatic export of real-eval failures into the
  registry (the real eval prints failures, but a human promotes them).
- The set is small (5); it grows as failures are root-caused, which is the point.
