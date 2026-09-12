# Implementation Plan: Merchant Agent

**Branch**: `010-merchant-agent` | **Date**: 2026-09-13 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/010-merchant-agent/spec.md`

## Summary

Add a `MerchantBackend` port (list inventory, stage changes, list pending, apply)
with a SQLite provider sharing the storefront DB. Expose merchant **tools** for
the agent to list and **propose** (never approve), and HTTP endpoints for the web
to list and **approve** (P3). Add a Merchant view.

## Technical Context

**Language/Version**: Python 3.13 + TypeScript/React 19

**Primary Dependencies**: stdlib `sqlite3`; existing seams

**Storage**: the storefront SQLite file + a `pending_changes` table

**Testing**: `pytest` (unit staging/apply; API apply), Playwright checkpoint

**Target Platform**: server + browser

**Project Type**: web service

**Performance Goals**: trivial

**Constraints**: no model tool to approve (P3); no new dependencies

## Constitution Check

| Clause | Check | Result |
| --- | --- | --- |
| P3 model proposes, harness disposes | propose stages; approval is human-only | PASS |
| PB-1 config as contract | merchant uses the storefront path from settings | PASS |
| PB-2 capability seam | Definition (port) + Provider (sqlite) + Consumers (tools, web) | PASS |
| P5 / PB-5 | validate at the boundary (price > 0, stock ≥ 0, known product) | PASS |
| RD-2 | applying twice does not double-apply | PASS |
| WV-5 | a Merchant web view | PASS |

## Project Structure

```text
app/
├── core/types.py            # + Change
├── ports/merchant.py        # NEW: MerchantBackend
├── adapters/merchant_sqlite.py  # NEW: SqliteMerchant
└── tools/merchant.py        # NEW: list_inventory, propose_* (no approve)
web/main.py                  # build_merchant; merchant endpoints
frontend/src/
├── lib/merchant.ts          # API helpers + types
├── components/app/merchant-view.tsx
└── App.tsx                  # Merchant tab
tests/unit/test_merchant.py
tests/integration/test_merchant_api.py
```

## Complexity Tracking

> No constitution violations; nothing to justify.
