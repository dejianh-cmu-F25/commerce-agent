# Contract: Evaluation harness

## `evals/scenarios.py`

```python
@dataclass
class Scenario:
    name: str
    user_text: str
    turns: list[MockTurn]
    expect_tools: list[str]
    expect_components: list[str] = field(default_factory=list)
    expect_cart: list[tuple[str, int]] = field(default_factory=list)


SCENARIOS: list[Scenario]
```

## `evals/run.py`

```python
async def run_all() -> list[EvalResult]: ...
def main() -> int: ...  # 0 if all pass, 1 otherwise
```

- `run_all` builds, per scenario, a real `Agent` with a scripted `MockLLMClient`
  and real tools (catalog + cart over an in-memory storefront; merchant over a
  temp SQLite DB), runs one turn, and asserts:
  - `[ToolCallStarted.name] == scenario.expect_tools`
  - `[UIComponent.component] == scenario.expect_components`
  - `session.cart` quantities == `scenario.expect_cart`
- It never inspects assistant text (TT-2).

## Gate

`scripts/ci.sh` runs `uv run python evals/run.py` after the tests; a non-zero exit
fails the gate.
