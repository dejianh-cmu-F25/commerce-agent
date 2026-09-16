# Feature Specification: Parameterized Eval Cases

**Feature Branch**: `024-parameterized-cases`

**Created**: 2026-09-13

**Status**: Draft

**Input**: Make the real-model eval discriminate by replacing the fixed cases
with parameterized templates (budget, multi-item, refusal, ungrounded, policy)
whose parameters vary by seed, paired across seeds.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Parameterized, paired cases (Priority: P1)

Each template yields a concrete case per seed with different parameters (item,
budget, order, fake id, topic), while the template's **name** stays stable so
reliability aggregates across seeds.

**Why this priority**: The book's parameterized design prevents memorization and
makes cross-seed comparison fair; the current fixed cases saturate at 1.0.

**Independent Test**: Build cases for several seeds and assert the names are
stable and at least one parameter differs between seeds.

**Acceptance Scenarios**:

1. **Given** two seeds, **When** cases are built, **Then** the template names
   match and the parameters differ.
2. **Given** the same seed, **When** cases are built twice, **Then** they are
   identical (reproducible).

---

### User Story 2 - Harder, outcome-checked cases (Priority: P1)

Cases check harder outcomes: a budget ceiling on rendered products, a multi-item
cart, a refused out-of-window return, a rejected ungrounded id, and a grounded
policy answer.

**Independent Test**: The predicates reject a wrong outcome (e.g., a product over
budget, a rendered return for O-1002, an added fake id).

**Acceptance Scenarios**:

1. **Given** a budget case, **When** the agent shows only items over budget,
   **Then** the case fails.
2. **Given** an out-of-window return, **When** a return is rendered, **Then** the
   case fails.

---

### Edge Cases

- **Seed larger than the parameter list**: parameters cycle deterministically.
- **Model refusal phrasing**: the predicate uses outcome (component/cart), not
  prose, except for a topic keyword in the policy case.
- **Keyless gate**: unaffected (the real runner is opt-in).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST build cases from templates with parameters chosen
  deterministically by seed; template names MUST be stable across seeds.
- **FR-002**: The predicate MUST support: essential tools/components, cart
  contents, required answer substrings, forbidden components, an empty-cart
  requirement, a maximum price on rendered products, and a minimum cart size.
- **FR-003**: Templates MUST cover: budget search, multi-item cart, out-of-window
  refusal, ungrounded id, and a policy question.
- **FR-004**: The real runner MUST use `build_cases(seed)` per seed and aggregate
  reliability per template.
- **FR-005**: Case construction MUST be pure and reproducible.

### Key Entities

- **RealCase**: a concrete, outcome-checked case (template name + parameters).
- **build_cases(seed)**: the template instantiation for a seed.

## Observability

- The report's per-template reliability and failure attribution already cover the
  cases; no new span.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Template names are stable across seeds; parameters vary.
- **SC-002**: The real run reports per-template Pass@1/Pass@k/Pass^k over the
  parameterized set.
- **SC-003**: At least one template discriminates (pass rate < 1.0) **or** the
  report records that the set is saturated (honest).
- **SC-004**: The keyless gate still passes.

## Assumptions

- The real runner stays opt-in and budget-capped.
- Parameter lists are small and hand-curated; large-scale generation is out of
  scope.

## Measured Results

Per template (DeepSeek, 3 seeds; dated snapshot):

| Template | Pass@1 | Pass@k | Pass^k |
| --- | ---: | ---: | ---: |
| `budget_search` | 1.000 | 1.000 | 1.000 |
| `multi_item_cart` | 0.000 | 0.000 | 0.000 |
| `add_named_item` | 1.000 | 1.000 | 1.000 |
| `policy_question` | 1.000 | 1.000 | 1.000 |
| `refuse_out_of_window` | 1.000 | 1.000 | 1.000 |
| `ungrounded_rejected` | 1.000 | 1.000 | 1.000 |

Overall Pass@1 **0.833** (95% CI [0.611, 1.000]) / Pass^k **0.833** — the metric
discriminates (no longer saturated).

- Source: `evals/report.md`; aggregate: [`specs/RESULTS.md`](../RESULTS.md).

## Real-World Coverage

- **Input distribution**: seeded templates (budget, multi-item, named item,
  policy, refusal, ungrounded); adversarial phrasing is out of scope (gap).
- **Data quality**: construction is pure and reproducible; results are snapshots.
- **Edge & failure modes**: outcome failures are attributed as `incomplete`.
- **Scale envelope**: 6 templates × N seeds; the system envelope is measured in `docs/scale.md`.
- **Degradation**: n/a (evaluation harness).
- **Change evidence**: the per-template results are the change evidence.
