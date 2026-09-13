# Feature Specification: Storefront Backend

**Feature Branch**: `004-storefront-backend`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Introduce a `StorefrontBackend` port with in-memory and SQLite
adapters, config-selected, replacing the in-memory catalog stand-in used by
`search_products`. Keep server-issued ids for grounding and make seeding
idempotent.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Search reads from a real backend (Priority: P1)

A customer asks for a product. The agent's `search_products` tool reads from a
`StorefrontBackend` instead of a hard-coded list, and only server-issued product
ids enter the session (grounding).

**Why this priority**: The catalog is the source of truth for prices and stock;
grounding (P4) and every later commerce feature depend on it.

**Independent Test**: Register the tool against a backend, run a turn, and assert
the tool result and provenance come from the backend.

**Acceptance Scenarios**:

1. **Given** a backend with products, **When** the customer searches, **Then** the
   tool returns matching products and the session remembers their ids.
2. **Given** a query with no matches, **When** the tool runs, **Then** it returns
   an empty result and the agent does not invent products.

---

### User Story 2 - The backend is configurable (Priority: P1)

The operator chooses the storefront implementation in configuration; a missing or
invalid choice fails loud at startup.

**Why this priority**: PB-1 (config as contract) and PB-2 (capability seam).

**Independent Test**: Load settings with each provider; assert the factory returns
the matching adapter; assert an unknown provider is rejected at load.

**Acceptance Scenarios**:

1. **Given** `storefront.provider: memory`, **When** the app starts, **Then** the
   in-memory adapter is used.
2. **Given** `storefront.provider: sqlite`, **When** the app starts, **Then** the
   SQLite adapter is used and the database is created/seeded.
3. **Given** an unknown provider, **When** settings load, **Then** it fails with a
   clear error (no silent fallback).

---

### User Story 3 - Seeding is idempotent (Priority: P2)

Starting the app repeatedly does not duplicate catalog rows.

**Why this priority**: RD-2 (idempotent data management) and safe restarts.

**Independent Test**: Seed twice into the same SQLite file; assert the row count
is unchanged.

**Acceptance Scenarios**:

1. **Given** a seeded database, **When** the app starts again, **Then** the product
   count is unchanged and no duplicate ids exist.

### Edge Cases

- Empty query: return no results (do not return the whole catalog).
- `limit` out of range: clamp to a sane bound.
- SQLite file path is unwritable: fail loud at startup, not on the first search.
- A product is removed from the seed: existing rows are not silently deleted
  (updates/deletes are explicit, per RD-2).

## Requirements *(mandatory)*

- **FR-001**: A `StorefrontBackend` port MUST define the capability: `search(query,
  limit) -> list[Product]` and `get(product_id) -> Product | None`.
- **FR-002**: The port MUST have at least two providers: in-memory and SQLite.
- **FR-003**: The provider MUST be selected by `config/settings.yaml` and validated;
  an unknown provider MUST fail loud at load (PB-1).
- **FR-004**: `search_products` MUST read from the injected backend; the hard-coded
  catalog list MUST be removed from the tool.
- **FR-005**: Only server-issued product ids MUST enter the session provenance (P4).
- **FR-006**: SQLite seeding MUST be idempotent (no duplicates on restart) (RD-2).
- **FR-007**: The tool MUST preserve its current model-facing contract (name,
  parameters, result shape) and UI component (`products`) so behavior is unchanged.
- **FR-008**: The backend MUST be injected at composition (no global singleton), so
  tests can substitute it (P5).
- **FR-009**: A backend-only feature MUST still be demonstrable through the existing
  web entry (WV-5).

### Key Entities

- **Product**: `id` (server-issued), `title`, `price`, `stock`, `tags`; `in_stock`
  is derived.
- **StorefrontBackend**: the capability (search, get).
- **StorefrontSettings**: `provider` (`memory` | `sqlite`), `sqlite_path`.

## UI Requirements

This feature does not change the browser surface; the states are unchanged from
003.

| State | Trigger | What the user sees |
| --- | --- | --- |
| Empty | Load, no messages | Unchanged from 003 |
| Streaming | Message sent | Unchanged; `search_products` reads from the backend |
| Success | Turn ends | Unchanged; sources show backend products |
| Error | Failure | Unchanged |

## Web Acceptance

Open `/`, ask for a tent. The `search_products` step completes and the sources
list the same product(s) as before — now served from the configured backend
(SQLite by default). `/readyz` still reports ready.

## Observability

No new events; the existing `ToolCallStarted`/`ToolResult`/`UIComponent` stream is
unchanged. Structured traces arrive with feature 080 (SL-2).

## Success Criteria *(mandatory)*

- **SC-001**: A turn that searches products returns the same results as before,
  read from the backend (parity).
- **SC-002**: Unit tests cover the in-memory adapter; integration tests cover the
  SQLite adapter (seed, search, get, idempotent re-seed).
- **SC-003**: Switching `storefront.provider` changes the adapter with no code
  change; an unknown provider fails at load.
- **SC-004**: No product id reaches the session that did not come from the backend.

## Assumptions

- The seed catalog is the same five products currently in `app/tools/catalog.py`.
- SQLite is embedded (file-based) and lives under `data/db/` (DP-6 volumes).
- Retrieval/vector search is out of scope (features 008+); this is the storefront
  system of record, not the knowledge base.
- `search` is a simple keyword match for now; ranking quality is not in scope.

## Real-World Coverage

- **Input distribution**: product search queries; an empty query returns nothing.
- **Data quality**: the catalog is seeded idempotently; ids are server-issued.
- **Edge & failure modes**: an unknown id returns `None`; switching provider is
  config-only; an unknown provider fails loud.
- **Scale envelope**: a tiny seeded catalog; the system envelope is measured in `docs/scale.md`.
- **Degradation**: the `memory` provider is the keyless fallback.
- **Change evidence**: parity tests (`tests/integration/test_storefront_sqlite.py`).
