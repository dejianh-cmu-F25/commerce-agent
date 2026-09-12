# Contract: Cart tools

## `app/tools/cart.py`

```python
def register_cart_tools(registry: ToolRegistry, storefront: StorefrontBackend) -> None: ...
```

### `add_to_cart(product_id, quantity = 1)`

- If `product_id` is not in `session.provenance` (`session.knows`) → `ToolResult`
  with `status="error"` and a message telling the model to search first; the cart
  is unchanged (P4).
- Else fetch the product from the storefront; if `None` → error.
- Clamp `quantity` to ≥ 1; increment an existing line or append a new one.
- Return `ToolResult(component="cart", payload=cart_payload(session))`.

### `view_cart()`

- Return `ToolResult(component="cart", payload=cart_payload(session))`.

### `render_checkout()`

- Return `ToolResult(component="checkout", payload=checkout_payload(session))`
  where `charged` is always `false` (P3). Never charges, never places an order.

## Payload builders

```python
def cart_payload(session) -> dict   # {"items": [...], "total": float}
def checkout_payload(session) -> dict  # {"items": [...], "total": float, "charged": False}
```

`line_total = unit_price * quantity`; `total` is the sum of line totals.

## Client (`frontend/src/lib/transport.ts`)

`UIComponent` names map to data parts: `products → data-sources`,
`cart → data-cart`, `checkout → data-checkout`. `AgentDataTypes` gains `cart`
and `checkout` (each `{ items: CartItem[]; total: number }`).
