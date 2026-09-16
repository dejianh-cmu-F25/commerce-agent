# Data Model: Merchant Agent

## Change (`app/core/types.py`)

| Field | Type |
| --- | --- |
| `id` | `str` |
| `product_id` | `str` |
| `kind` | `"price" \| "stock"` |
| `old_value` | `float` |
| `new_value` | `float` |
| `status` | `"pending" \| "applied"` |
| `created_at` | `str` (ISO) |

## SQLite (`pending_changes`)

```sql
CREATE TABLE IF NOT EXISTS pending_changes (
    id         TEXT PRIMARY KEY,
    product_id TEXT NOT NULL,
    kind       TEXT NOT NULL,      -- price | stock
    old_value  REAL NOT NULL,
    new_value  REAL NOT NULL,
    status     TEXT NOT NULL,      -- pending | applied
    created_at TEXT NOT NULL
);
```

`products` is the existing table (written on `apply`).

## Payloads

| Component | Shape |
| --- | --- |
| `inventory` | `{"items": [{"id","title","price","stock","in_stock"}]}` |
| `pending_changes` | `{"changes": [Change]}` |

## HTTP

| Method | Path | Effect |
| --- | --- | --- |
| GET | `/merchant/inventory` | list products |
| GET | `/merchant/changes` | list pending changes |
| POST | `/merchant/changes/{id}/apply` | apply a change (404 unknown) |
