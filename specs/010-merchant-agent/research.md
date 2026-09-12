# Research: Merchant Agent

## D1. Staging model

**Decision**: a `pending_changes` table in the storefront DB. `stage_change`
inserts a `pending` row; `apply` reads it, updates `products`, and marks it
`applied` in one transaction.

**Rationale**: P3 (no effect until approval) and RD-2 (no double-apply) are easy
to guarantee transactionally.

## D2. Approval is human-only

**Decision**: the agent gets `list_inventory` and `propose_*` tools only. There is
**no** `apply_change` tool; approval is `POST /merchant/changes/{id}/apply` from
the web.

**Rationale**: P3 — the model must not be able to approve its own write.

## D3. One storefront DB

**Decision**: `SqliteMerchant` opens the same file as the storefront
(`settings.storefront.sqlite_path`) and manages `products` writes plus
`pending_changes`.

**Rationale**: a single source of truth; no sync between two stores.

## D4. Validation

**Decision**: reject unknown product ids; require `price > 0` and `stock ≥ 0`;
store the old value at staging time so the UI can show the diff.

## D5. UI

**Decision**: a Merchant tab (like Traces) listing inventory and pending changes
with Approve buttons; it uses the HTTP API directly.

**Rationale**: approval is a host action, independent of the chat.
