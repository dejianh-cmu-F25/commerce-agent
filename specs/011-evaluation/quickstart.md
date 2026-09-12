# Quickstart: Evaluation Harness

## Run

```sh
uv run python evals/run.py        # prints a report; exit 0 = all pass
scripts/ci.sh --fast              # includes the eval step
```

## Add a scenario

Edit `evals/scenarios.py`: add a `Scenario` with the scripted `turns`
(`tool_turn(...)`, `text_turn(...)`) and the expected `expect_tools` /
`expect_components` / `expect_cart`. No runner changes needed.

## Notes

- Keyless: only the model is scripted; the loop, tools, and stores are real.
- Assertions are deterministic outcomes only (never prose) — TT-2.
