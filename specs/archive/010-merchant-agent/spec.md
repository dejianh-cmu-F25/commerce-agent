# Feature Specification: Merchant Agent

**Feature Branch**: `010-merchant-agent`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Add the operator face: merchant tools to list inventory and propose
price/stock changes that are **staged, not applied**; a human approves via the web
(`POST /merchant/changes/{id}/apply`). Enforce P3 (model proposes, host disposes).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review inventory (Priority: P1)

An operator can list the catalog with prices and stock.

**Independent Test**: `list_inventory` returns the products; the Merchant view
renders them.

**Acceptance Scenarios**:

1. **Given** the catalog, **When** the operator lists inventory, **Then** the
   products (id, title, price, stock) are shown.

---

### User Story 2 - Propose a change (staged, not applied) (Priority: P1)

The operator (via the agent) proposes a price or stock change. The change is
**staged**: the product is unchanged until a human approves it.

**Why this priority**: P3 — the model proposes; the host disposes.

**Independent Test**: Propose a change and assert the product is unchanged and a
pending change exists.

**Acceptance Scenarios**:

1. **Given** a product, **When** a price change is proposed, **Then** a pending
   change is recorded and the product's price is unchanged.
2. **Given** an unknown product id, **When** a change is proposed, **Then** it is
   rejected.

---

### User Story 3 - Approve a change (Priority: P1)

A human approves a staged change in the web UI; only then is it applied to the
catalog. The agent has no tool to approve.

**Independent Test**: Apply a pending change via the API and assert the product
is updated and the change is marked applied.

**Acceptance Scenarios**:

1. **Given** a pending change, **When** it is approved, **Then** the product is
   updated and the change is no longer pending.
2. **Given** the agent's tools, **When** the model tries to apply a change,
   **Then** no such tool exists (approval is human-only).

### Edge Cases

- A price ≤ 0 or a negative stock: rejected.
- Approving an unknown or already-applied change: 404 / error, no double-apply.
- A proposed change for a product that no longer exists: rejected at staging.

## Requirements *(mandatory)*

- **FR-001**: A `MerchantBackend` port MUST define `list_products`,
  `stage_change`, `pending`, and `apply`.
- **FR-002**: `stage_change` MUST record a pending change and MUST NOT modify the
  product (P3).
- **FR-003**: `apply` MUST update the product and mark the change applied;
  applying twice MUST NOT double-apply.
- **FR-004**: The agent MUST expose merchant tools to list inventory and propose
  changes, but **no** tool to approve them (P3).
- **FR-005**: The web MUST expose `GET /merchant/inventory`,
  `GET /merchant/changes`, and `POST /merchant/changes/{id}/apply`.
- **FR-006**: Proposals and approvals MUST be visible in a Merchant view.
- **FR-007**: Changes MUST persist (RD) and be validated (price > 0, stock ≥ 0).
- **FR-008**: The consumer chat MUST be unaffected.

### Key Entities

- **Change**: `id`, `product_id`, `kind` (`price` | `stock`), `old_value`,
  `new_value`, `status` (`pending` | `applied`), `created_at`.
- **MerchantBackend**: the capability (list, stage, pending, apply).

## UI Requirements

### UI States

| State | Trigger | What the user sees |
| --- | --- | --- |
| Inventory | Merchant view | Products with price and stock |
| Pending changes | Merchant view | Staged changes with an Approve action |
| Empty | No pending changes | "No pending changes." |
| Applied | Approve clicked | The change moves out of pending; the product updates |

## Web Acceptance

Open **Merchant**: the inventory is listed and (after asking the agent to change a
price) the pending change appears with an Approve button. Approve it: the price
updates in the inventory and the change leaves the pending list.

## Observability

Merchant turns emit the existing spans (007); tool spans show `list_inventory` /
`propose_*`. Approval is an HTTP call, not a model action.

## Success Criteria *(mandatory)*

- **SC-001**: A proposed change does not modify the product until approved.
- **SC-002**: Approving a change updates the product and clears it from pending.
- **SC-003**: The agent has no approval tool (P3), verified by inspection and a
  test.
- **SC-004**: The Merchant view lists inventory and pending changes and can apply
  them.

## Assumptions

- One merchant identity (no auth) for the demo.
- The merchant backend shares the storefront's SQLite file.
- Approval is a human web action; the agent may only propose.

## Real-World Coverage

- **Input distribution**: operator instructions to change price/stock.
- **Data quality**: changes are validated (price > 0, stock ≥ 0) and staged.
- **Edge & failure modes**: unknown product → error; double-apply is a no-op (RD-2).
- **Scale envelope**: single operator; the system envelope is measured in `docs/scale.md`.
- **Degradation**: the merchant backend is SQLite-backed; a write failure surfaces as an error.
- **Change evidence**: model/prompt changes update `specs/RESULTS.md` (EV-1).
