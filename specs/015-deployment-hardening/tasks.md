# Tasks: Deployment Hardening

**Feature**: `015-deployment-hardening` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

Legend: `[P]` = parallelizable.

## Phase 1 — Config contract

- [x] T001 Rewrite `.env.example` to the exact `_ENV_OVERRIDES` keys with comments
- [x] T002 Rewrite `docker-compose.yml` env to the real names; keep data/log volumes

## Phase 2 — Smoke test

- [x] T003 `scripts/smoke_container.sh` (keyless run; health/readyz/SPA/chat/non-root; cleanup)
- [x] T004 `scripts/ci.sh --with-image`: build, then run the smoke test
- [x] T005 `Makefile`: `smoke-image` target

## Phase 3 — Tests + verify

- [x] T006 [P] `tests/unit/test_deploy_config.py` (env/compose parity; `.dockerignore` excludes `.env`)
- [x] T007 `docs/architecture.md` or README deployment note; Agent Note
- [x] T008 `scripts/ci.sh --fast`; `make ci-image`; browser checkpoint against the container; review; PR

## Dependencies

- T001/T002 before T006.
- T003/T004/T005 before T008.
- T008 last.
