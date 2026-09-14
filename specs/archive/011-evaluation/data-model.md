# Data Model: Evaluation Harness

## Scenario (`evals/scenarios.py`)

| Field | Type | Notes |
| --- | --- | --- |
| `name` | `str` | unique |
| `user_text` | `str` | the customer message |
| `turns` | `list[MockTurn]` | the scripted model turns |
| `expect_tools` | `list[str]` | ordered tool names |
| `expect_components` | `list[str]` | ordered UI component types |
| `expect_cart` | `list[tuple[str, int]]` | `(product_id, quantity)` |

## EvalResult (`evals/run.py`)

| Field | Type |
| --- | --- |
| `name` | `str` |
| `ok` | `bool` |
| `failures` | `list[str]` |

## Gold set (initial)

| Scenario | Tools | Components | Cart |
| --- | --- | --- | --- |
| `search_only` | `search_products` | `products` | — |
| `add_to_cart` | `search_products`, `add_to_cart` | `products`, `cart` | `[("P-101", 1)]` |
| `ungrounded_add_rejected` | `add_to_cart` | — | — |
| `checkout_render` | `search_products`, `add_to_cart`, `render_checkout` | `products`, `cart`, `checkout` | `[("P-101", 1)]` |
| `merchant_stage` | `propose_price_change` | — | — (price unchanged) |
