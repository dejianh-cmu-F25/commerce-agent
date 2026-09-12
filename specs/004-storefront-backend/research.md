# Research: Storefront Backend

## D1. Port shape

**Decision**: `StorefrontBackend` with `search(query, limit) -> list[Product]` and
`get(product_id) -> Product | None`. `Product` is a dataclass in
`app/core/types.py` (dependency-free, importable by core and ports).

**Rationale**: Minimal capability the tool needs today; `get` supports later
features (cart/checkout) without a new seam. P6: no speculative methods.

**Alternatives considered**: a generic `query(spec)` (rejected: over-general);
`list_all()` (rejected: unused).

## D2. SQLite via stdlib

**Decision**: Use `sqlite3` directly; a `products` table with a primary key on
`id`; seed with `INSERT OR IGNORE`.

**Rationale**: No new dependency, embedded, file-based (DP-6), and idempotent
seeding is one clause (RD-2).

**Alternatives considered**: SQLAlchemy/ORM (rejected: dependency and ceremony for
one table); JSON file (rejected: no transactional/idempotent story).

## D3. Shared seed data

**Decision**: Move the current five products into `app/adapters/catalog_seed.py`
as `SEED_PRODUCTS: list[Product]`; both adapters use it.

**Rationale**: One source for seed data; the memory adapter stays a valid
provider for keyless runs (P8).

## D4. Factory at the composition root

**Decision**: `build_storefront(settings) -> StorefrontBackend` in `web/main.py`,
alongside `build_llm`/`build_agent`. Unknown provider raises (validated earlier by
pydantic `Literal`, so it fails at load — PB-1).

**Rationale**: Explicit resolve step (PB-3); the loop/tool never choose a provider.

## D5. Tool injection

**Decision**: `register_catalog_tools(registry, storefront)`; `_search_products`
calls the backend and remembers returned ids. The model-facing spec and the
`products` UI component payload are unchanged (FR-007).

**Rationale**: No behavior change; provenance stays server-issued (P4).

## D6. Default provider

**Decision**: default `sqlite` (real persistence), with `memory` available for
keyless/tests.

**Rationale**: Demonstrates the seam with real data; `memory` keeps the
no-dependency demo path (P8).
