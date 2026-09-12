# Contract: StorefrontBackend

## Port (`app/ports/storefront.py`)

```python
class StorefrontBackend(Protocol):
    def search(self, query: str, limit: int) -> list[Product]: ...
    def get(self, product_id: str) -> Product | None: ...
```

Rules:
- `search` returns at most `limit` products, ranked by keyword match; an empty
  query returns `[]` (never the whole catalog).
- `limit` is clamped to `[1, 50]`.
- Returned `id`s are the only ids the caller may put into the session (P4).
- The port does not know about sessions, the model, or the web layer.

## Providers

| Provider | Module | Notes |
| --- | --- | --- |
| `memory` | `app/adapters/storefront_memory.py` | seeded from `SEED_PRODUCTS` |
| `sqlite` | `app/adapters/storefront_sqlite.py` | stdlib `sqlite3`; idempotent seed |

## Factory (`web/main.py`)

```python
def build_storefront(settings: Settings) -> StorefrontBackend: ...
```

- `memory` → `InMemoryStorefront(SEED_PRODUCTS)`
- `sqlite` → `SqliteStorefront(settings.storefront.sqlite_path)` (creates + seeds)
- Unknown provider cannot occur: `StorefrontSettings.provider` is a `Literal`
  validated at load (PB-1).

## Consumer (`app/tools/catalog.py`)

```python
def register_catalog_tools(registry: ToolRegistry, storefront: StorefrontBackend) -> None: ...
```

- `search_products` calls `storefront.search(query, limit)`.
- `session.remember_ids([p.id for p in results])`.
- Tool result content and the `products` UI component payload keep their current
  shape.
