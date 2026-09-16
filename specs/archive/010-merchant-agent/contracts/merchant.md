# Contract: Merchant

## Port (`app/ports/merchant.py`)

```python
class MerchantBackend(Protocol):
    def list_products(self, limit: int = 100) -> list[Product]: ...
    def stage_change(self, product_id: str, kind: str, new_value: float) -> Change: ...
    def pending(self) -> list[Change]: ...
    def apply(self, change_id: str) -> Change | None: ...
```

- `stage_change` returns a `pending` change and MUST NOT modify the product (P3).
- `apply` returns the `applied` change, or `None` if unknown/already applied;
  applying twice does not double-apply (RD-2).

## Provider (`app/adapters/merchant_sqlite.py`)

`SqliteMerchant(path)` — same DB as the storefront; adds `pending_changes`.

## Tools (`app/tools/merchant.py`) — agent-facing

| Tool | Effect |
| --- | --- |
| `list_inventory` | `inventory` component |
| `propose_price_change(product_id, price)` | stages; `pending_changes` component |
| `propose_stock_change(product_id, stock)` | stages; `pending_changes` component |
| `list_pending_changes` | `pending_changes` component |

There is **no** approval tool (P3).

## HTTP (web, host-facing)

- `GET /merchant/inventory` → `{"items": [...]}`
- `GET /merchant/changes` → `{"changes": [...]}`
- `POST /merchant/changes/{id}/apply` → `{"change": {...}}` or 404

## Client

`Merchant` tab: inventory table + pending changes with an **Approve** button
(calls the apply endpoint), refreshed after approval.
