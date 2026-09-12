# Data Model: Cart and Checkout

## CartLine (existing, `app/core/session.py`)

| Field | Type |
| --- | --- |
| `product_id` | `str` |
| `title` | `str` |
| `quantity` | `int` |
| `unit_price` | `float` |

## Cart payload (UI component `cart`)

```json
{
  "items": [
    {"product_id": "P-101", "title": "2-Person Tent", "quantity": 2,
     "unit_price": 189.0, "line_total": 378.0, "in_stock": true}
  ],
  "total": 378.0
}
```

## Checkout payload (UI component `checkout`)

```json
{"items": [ … ], "total": 378.0, "charged": false}
```

`charged` is always `false` (P3).

## Tools

| Tool | Parameters | Result |
| --- | --- | --- |
| `add_to_cart` | `product_id`, `quantity` (default 1) | `cart` component or an error |
| `view_cart` | — | `cart` component |
| `render_checkout` | — | `checkout` component |

## Client data parts

| Backend component | Chunk | UI |
| --- | --- | --- |
| `products` | `data-sources` | sources list |
| `cart` | `data-cart` | cart card |
| `checkout` | `data-checkout` | checkout card |
