# Implementation Plan: Storefront Backend

**Branch**: `004-storefront-backend` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-storefront-backend/spec.md`

## Summary

Introduce a `StorefrontBackend` port (Service Definition) with two providers
(in-memory, SQLite) selected by configuration, and inject it into the
`search_products` tool, replacing the hard-coded catalog. Keeps grounding (P4)
and idempotent seeding (RD-2). No new dependencies (stdlib `sqlite3`).

## Technical Context

**Language/Version**: Python 3.13

**Primary Dependencies**: stdlib `sqlite3`; existing `pydantic` settings; no new
packages

**Storage**: SQLite file under `data/db/` (embedded, DP-6)

**Testing**: `pytest` — unit (memory adapter), integration (SQLite adapter)

**Target Platform**: server (Docker + local)

**Project Type**: web service (backend seam)

**Performance Goals**: catalog is tiny; search is O(n) keyword match

**Constraints**: no behavior change to the model-facing tool; fail loud on bad
config (PB-1)

**Scale/Scope**: five seed products; a seam meant to be replaced by a real
storefront later

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| PB-1 config as contract | provider selected in `settings.yaml`, validated | PASS |
| PB-2 capability seam | Definition (port) + Providers (memory, sqlite) + Consumer (tool) | PASS |
| PB-3 explicit boundaries | factory resolves provider explicitly; no hidden fallback | PASS |
| PB-5 validate at boundaries | validate config; validate SQLite row → `Product` | PASS |
| P4 grounding | only backend-issued ids enter provenance | PASS |
| P5 contract first | port defined before adapters; injected | PASS |
| P6 simplicity | stdlib sqlite3; no ORM | PASS |
| RD-2 idempotent data | `INSERT OR IGNORE` seeding | PASS |
| WV-5 web entry | search still demonstrable in the browser | PASS |
| DP-6 volumes | SQLite under `data/db/` | PASS |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/004-storefront-backend/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/storefront.md
├── tasks.md
└── checkpoint.md / checkpoint.png
```

### Source Code

```text
app/
├── core/
│   ├── types.py            # + Product
│   └── settings.py         # + StorefrontSettings
├── ports/
│   └── storefront.py       # NEW: StorefrontBackend protocol
├── adapters/
│   ├── catalog_seed.py     # NEW: shared seed products
│   ├── storefront_memory.py# NEW: InMemoryStorefront
│   └── storefront_sqlite.py# NEW: SqliteStorefront
├── tools/
│   └── catalog.py          # register_catalog_tools(registry, storefront)
web/
└── main.py                 # build_storefront(settings); wire the tool
tests/
├── unit/test_storefront_memory.py
└── integration/test_storefront_sqlite.py
```

**Structure Decision**: Follow the existing ports/adapters/core layering; the
factory lives at the composition root (`web/main.py`), consistent with
`build_llm`/`build_agent`.

## Complexity Tracking

> No constitution violations; nothing to justify.
