# Data Model: Storefront Backend

## Product (domain type, `app/core/types.py`)

| Field | Type | Notes |
| --- | --- | --- |
| `id` | `str` | server-issued; the grounding handle (P4) |
| `title` | `str` | |
| `price` | `float` | |
| `stock` | `int` | |
| `tags` | `list[str]` | used for keyword match |

`in_stock` is derived (`stock > 0`), not stored.

## SQLite schema (`storefront_sqlite`)

```sql
CREATE TABLE IF NOT EXISTS products (
    id     TEXT PRIMARY KEY,
    title  TEXT NOT NULL,
    price  REAL NOT NULL,
    stock  INTEGER NOT NULL,
    tags   TEXT NOT NULL          -- comma-separated
);
```

Seeding: `INSERT OR IGNORE INTO products(...) VALUES (...)` for each seed product,
so restarts never duplicate rows (RD-2).

## Config (`StorefrontSettings`)

| Field | Type | Default | Notes |
| --- | --- | --- | --- |
| `provider` | `"memory" \| "sqlite"` | `"sqlite"` | validated; unknown fails at load |
| `sqlite_path` | `str` | `"./data/db/storefront.sqlite"` | created if missing |

Env overrides: `STOREFRONT_PROVIDER`, `STOREFRONT_SQLITE_PATH`.

## Mapping to the tool result

`search` returns `list[Product]`; the tool maps each to
`{id, title, price, in_stock}` for the model and the `products` UI component —
identical to the current shape (FR-007).
