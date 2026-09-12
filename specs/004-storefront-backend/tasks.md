# Tasks: Storefront Backend

**Feature**: `004-storefront-backend` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Domain + port

- [x] T001 Add `Product` dataclass to `app/core/types.py`
- [x] T002 Add `StorefrontBackend` protocol in `app/ports/storefront.py`
- [x] T003 Add `StorefrontSettings` + env overrides in `app/core/settings.py`
- [x] T004 [P] Add `config/settings.yaml` `storefront:` section

## Phase 2 — Providers

- [x] T005 Move seed products to `app/adapters/catalog_seed.py`
- [x] T006 [P] `InMemoryStorefront` in `app/adapters/storefront_memory.py`
- [x] T007 [P] `SqliteStorefront` in `app/adapters/storefront_sqlite.py` (idempotent seed)
- [x] T008 `build_storefront(settings)` in `web/main.py`

## Phase 3 — Consumer

- [x] T009 `register_catalog_tools(registry, storefront)`; remove the hard-coded list
- [x] T010 Wire the backend into `build_agent` / `create_app`

## Phase 4 — Tests

- [x] T011 [P] Unit: `tests/unit/test_storefront_memory.py`
- [x] T012 [P] Integration: `tests/integration/test_storefront_sqlite.py` (seed, search, get, idempotent re-seed)
- [x] T013 Update `tests/unit/test_loop.py` for the new registration signature

## Phase 5 — Verify & deliver

- [x] T014 `scripts/ci.sh --fast` (ruff/format, pyright, pytest, spec_review, verify_notes, frontend)
- [x] T015 Browser checkpoint + `checkpoint.png` + `checkpoint.md`
- [x] T016 Update `docs/architecture.md` if the wiring changes
- [x] T017 Commit and open the PR

## Dependencies

- T002 before T006/T007/T009.
- T008/T009 before T010.
- T011–T013 after T006/T007/T009.
- T014–T017 last.
