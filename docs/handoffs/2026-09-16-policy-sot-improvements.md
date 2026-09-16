# Handoff: harden the return-policy SoT, engine, and gate (feature 046)

- **Date**: 2026-09-16
- **Status**: ready for implementation (WP-A is decision-gated — see "Do not start")
- **Prepared by**: research pass on behalf of Dejian Huang (`dejianh@andrew.cmu.edu`)
- **Branch**: `046-closed-loop`
- **Related**: `specs/046-closed-loop/` (spec + plan + tasks), feature `020-gates`,
  `docs/notes/implemented/architecture/2026-09-13-gates.md`,
  `docs/notes/implemented/architecture/2026-09-13-post-purchase.md`

---

## 0. Read this first (repo state)

The working tree is **dirty**: 13 files are modified but uncommitted, several of them
the exact files this handoff touches (`app/returns/amazon_policy.py`,
`config/policies/amazon.yaml`, `config/knowledge/amazon-returns.md`,
`app/tools/post_purchase.py`, `app/gates/base.py`, `app/gates/tenancy.py`,
`web/main.py`). The in-flight work adds `exception_window_days` to the SoT, the
tenancy gate wiring, and fee-paraphrase wording.

**Before starting:**

1. Run `git status` and `git diff` and read every change.
2. Commit or stash that work first, or build on top of it — **do not clobber it.**
3. Re-derive the line numbers below; they were captured mid-flight on 2026-09-16 and
   will shift once the in-flight work lands. Symbols/anchors are given so you can find
   them regardless.

---

## 1. Objective

Make the return-policy subsystem **fail-closed, schema-validated, auditable, and
uniformly enforced**, using patterns proven by OPA/Cedar/Cerbos/DMN (see §6). This is
**not** a rewrite: the current design (single SoT → deterministic engine → runtime
gate) is sound and maps directly onto the industry "policy decision point" pattern.
The work is hardening the seams.

### Non-goals

- Replacing the engine with OPA/Cedar/Cerbos. That is over-built for this project
  (and directly conflicts with the gate ADR — see WP-A).
- Changing the user-visible decision vocabulary (`eligible` / `ineligible` /
  `escalate`) unless WP-A is approved.
- Real money movement — checkout stays simulated (P3).

---

## 2. Ground rules (do not violate)

These are normative in `.specify/memory/constitution.md`. Cite the clause in your
change-log entry.

| Clause | Meaning for this work |
| --- | --- |
| **P1** | Spec is the source of truth — update the spec/tasks alongside code. |
| **P3** | Model proposes, harness disposes; gates never mutate state. Do not let a gate or engine write. |
| **P4** | Grounding — only server-issued ids; facts come from tool results. |
| **HR-4** | The return decision is **deterministic**; the model never decides. Preserve this. |
| **SC-4 / docs/change-safety.md** | State **blast radius** and **rollback** per change. |
| **EV / docs/production-conventions.md** | Engine/module changes need before/after evidence in `specs/RESULTS.md` / `evals/report.md`; guardrails must not regress. |
| **P6** | No generic framework. Prefer the smallest seam that works. |

**Two existing decisions constrain you — honor them or supersede them explicitly:**

1. `2026-09-13-gates.md` rejects "a policy engine with configurable rules"
   ("Over-built for this project"). WP-A would revisit this; it needs a new ADR.
2. `specs/046-closed-loop/plan.md:51` says `delete → settings.returns.window_days`
   ("no third copy"). WP-3 enforces this for the restocking list.

---

## 3. Work packages

Priority: **P0** blocks other work; **P1** correctness/audit; **P2** consistency; **P3**
future. Each WP: problem → change → acceptance → blast radius → rollback → evidence.

### WP-1 (P0) · Validate the SoT against a schema

**Problem.** `AmazonClause.rules` is a free-form `dict` (`app/returns/amazon_policy.py`,
`@dataclass AmazonClause`, `rules: dict`). A typo in a rule key (e.g. `window_day:` for
`window_days:`) is silently ignored at runtime and changes eligibility with no error.
Cedar validates policies against a schema at authoring time; Cerbos has `cerbos compile`;
OPA has `opa check`.

**Change.**

- Add a JSON Schema for `config/policies/*.yaml`
  (required: `retailer`, `active_version`, `sources[].id/url`, `versions.<name>.effective_from`,
  `versions.<name>.clauses[].id/category/paraphrase/rules`; `active_version` must name an
  existing version; every clause `source` must resolve in `sources`).
- Add `scripts/check_policy.py` that validates the SoT and exits non-zero with an
  actionable message (offending path + expected type).
- Wire it into `scripts/ci.sh` (next to the existing engine dual-run step).

**Acceptance.**

- A deliberately malformed SoT (unknown rule key, missing `effective_from`, dangling
  `source`) fails the script with a precise path.
- The current SoT passes.

**Blast radius.** `config/policies/` + `scripts/ci.sh` only; no runtime behavior change.
**Rollback.** `git revert` (additive; no data migration).
**Evidence.** New unit test `tests/unit/test_policy_schema.py`; change-log entry.

---

### WP-2 (P1) · Fail closed when the policy is incomplete

**Problem.** `_window_days` returns `_Window(0, "")` when neither
`returns#window-category` nor `returns#window-default` is present
(`app/returns/amazon_policy.py`, `_window_days`). The engine then computes `age > 0` and
returns `INELIGIBLE` citing the empty string `""`. A missing clause therefore produces a
**confident, wrong, citation-less denial** instead of an escalation.

Secondary: in the exception branch, `delivered_at is None` skips the age check and
returns `ELIGIBLE` ("no window, no fee"), whereas the non-exception path returns
`ESCALATE`. Missing data is **fail-open for exceptions, fail-closed elsewhere** —
inconsistent.

**Change.**

- Introduce a typed "policy incomplete" signal (raise, or an explicit
  `AmazonDecision(ESCALATE, ...)` with a reason like
  `"policy incomplete: no window clause for category '<x>'"`).
- Never emit an empty string in `cited_clauses`.
- For the exception branch with a missing delivery date, return `ESCALATE` (parity with
  the non-exception path). Only skip the *age* comparison, never the *fact requirement*.

**Acceptance.**

- Unit tests: (a) SoT with the window clauses removed → `ESCALATE`, not `INELIGIBLE`;
  (b) exception reason + `delivered_at=None` → `ESCALATE`; (c) no decision ever contains
  an empty clause id (add an assertion helper and use it across the suite).
- `uv run python evals/engine_agreement.py` still prints **shared-surface agreement = 1.000**.

**Blast radius.** `decide_return`, `PolicyGate`, the decision set in
`evals/post_purchase_cases.jsonl`, `tests/unit/test_amazon_policy.py`. **Do not break
the shared surface** that `evals/engine_agreement.py` pins to 1.000.
**Rollback.** `git revert`.
**Evidence.** Before/after in `specs/RESULTS.md` for decision accuracy; change-log entry.

---

### WP-3 (P1) · Delete the duplicate restocking list

**Problem.** `_RESTOCKING_DEFAULT = ("opened_software", "video_games", "collectible_cards")`
(`app/returns/amazon_policy.py`, module constant) duplicates the YAML list at
`config/policies/amazon.yaml` (`returns#fee-restocking` → `restocking_categories`). The
engine uses the code tuple as a fallback
(`set(fee.rules.get("restocking_categories", _RESTOCKING_DEFAULT))`). This is the "third
copy" that `specs/046-closed-loop/plan.md:51` aims to eliminate.

**Change.**

- Remove `_RESTOCKING_DEFAULT`. Treat a missing `restocking_categories` as *policy
  incomplete* (WP-2), not as a silent default.
- WP-1's schema should mark `restocking_categories` required on that clause.

**Acceptance.** Grep shows the category list exists **once**, in the SoT. Removing it
from the SoT fails schema validation rather than silently changing behavior.
**Blast radius.** Engine only. **Rollback.** `git revert`. **Evidence.** change-log entry.

---

### WP-4 (P1) · Make every decision replayable (provenance)

**Problem.** `AmazonDecision` carries `decision`, `reasons`, `cited_clauses`, `fee_pct`
but **no policy version, no clause `effective_from`, no decision id**. OPA decision logs
record `decision_id` + `bundles[_].revision` precisely so a past decision can be audited
and replayed. Today you cannot prove which policy version produced a recorded proposal.

**Change.**

- Add `policy_version: str` to `AmazonDecision` (the version actually used by
  `decide_return`).
- Attach a `decision_id` at the gate/tool boundary (session id + counter, or a uuid) and
  include `policy_version` + `decision_id` in the `propose_return_decision` record.
- Emit the record to the existing tracer sink (`logs/traces.jsonl`).

**Acceptance.** A recorded proposal carries `policy_version` and `decision_id`; replaying
that version + facts reproduces the same decision.
**Blast radius.** `AmazonDecision` shape → `PolicyGate`, `app/tools/post_purchase.py`
output JSON → frontend (`frontend/src/lib/transport.ts`) and evals that assert the
output shape. Coordinate all three; keep the change additive where possible.
**Rollback.** `git revert`. **Evidence.** change-log entry + a replay test.

---

### WP-5 (P2) · Policy tests: coverage + table-driven + every-clause-exercised

**Problem.** `tests/unit/test_amazon_policy.py` is strong but hand-written per case and
does not prove **every clause is exercised**. OPA's `opa test --coverage` and its
data-driven test format (load cases from YAML) are the reference.

**Change.**

- Move decision cases into a table (YAML/JSON fixtures under `evals/` or `tests/`), and
  run them parameterized.
- Add a check that every clause id in the active version appears in at least one case's
  `expected_policy_refs` (extend the existing
  `tests/unit/test_post_purchase_cases.py::test_policy_refs_resolve_to_real_clauses`
  from "refs resolve" to "refs cover").
- Report clause coverage in CI output.

**Acceptance.** A new clause added to the SoT with no test fails the coverage check.
**Blast radius.** Tests + `scripts/ci.sh`; no runtime change. **Rollback.** `git revert`.

---

### WP-6 (P2) · Enforce the gate on every surface; fix naming drift

**Problem.** `app/mcp/server.py` (the `customer-accounts` server registration) registers
the post-purchase tools **without** a `PolicyGate`, so the runtime "harness disposes"
guarantee (P3) is absent on the MCP surface. Also, the spec calls the policy tool
`search_policies` while the implementation and docs use `search_knowledge`.

**Change.**

- Inject `PolicyGate(load_amazon_policy())` (and `TenancyGate`) wherever
  `register_post_purchase_tools` is called, including the MCP server.
- Pick one tool name and make spec, docs, code, and prompt agree.

**Acceptance.** An MCP `propose_return_decision` that contradicts the engine is rejected
with `validated: false`; `grep -r` finds a single policy-tool name.
**Blast radius.** `app/mcp/server.py`, prompt, docs. **Rollback.** `git revert`.

---

### WP-7 (P2) · Render the new components

**Problem.** The new tools emit `component="return_decision"` and
`component="returnable_items"`, but `frontend/src/lib/transport.ts` maps neither, and
`app/tools/post_purchase.py` sets no `payload`. Results fall through to the generic
tool-step renderer; the mapped `data-order` part would receive an empty payload.

**Change.** Add transport mappings + minimal card components (mirror the existing
`ReturnCard`), or intentionally pass a `payload`. Keep it consistent with
`docs/ui-conventions.md`.

**Acceptance.** A full journey click-through renders the decision as a card with its
cited clauses.
**Blast radius.** frontend only. **Rollback.** `git revert`.

---

### WP-8 (P3, optional) · Align the return domain model with Shopify

**Context.** Shopify's official Returns API models a return as a state machine
(`REQUESTED → OPEN → CLOSED`, plus `DECLINED`, `CANCELED`), with first-class
`declineReason` (e.g. `FINAL_SALE`), `returnReason`, `restockingFee`, and separates
**eligibility** from **financial outcome** (`returnCalculate` /
`suggestedFinancialOutcome`), plus `disposition` (`RESTOCKED` / `MISSING`).

The project already gestures at this ("a fee never makes an item non-returnable" in the
fee clauses) but does not split eligibility from money. Consider aligning the recorded
decision shape with that contract when WP-4 lands. Do not change behavior here — this is
a vocabulary/modeling decision for the owner.

---

### WP-A (P0 conceptually, but **decision-gated**) · Move rule *structure* into the SoT

**Problem.** Today only **values** are data (`window_days`, category lists, fee pct);
the **decision logic is Python control flow**: precedence and overrides live in the
`if`-chain of `decide_return` (`app/returns/amazon_policy.py`). Changing rule semantics
(whether an exception is windowed, which clause wins, first-match order) requires editing
code. DMN decision tables, Rego, and venmo/business-rules all keep the rule *structure*
as data with an explicit **hit policy** (FIRST / PRIORITY / COLLECT).

**Do not start.** This contradicts a recorded decision:
`docs/notes/implemented/architecture/2026-09-13-gates.md` rejects
"A policy engine with configurable rules — over-built for this project," and P6 says no
generic framework. To proceed you must **first**:

1. Write a superseding ADR under `docs/notes/proposed/` that argues why the SoT now
   needs structure-as-data (cite the drift/schema findings from WP-1..WP-3 as evidence).
2. If accepted, open a spec (e.g. `specs/NNN-policy-decision-table/`) with a
   `## Rollback & Versioning` section and a migration path that keeps
   `evals/engine_agreement.py` at 1.000 during the transition.

Only then implement. If the ADR is rejected, WP-A is closed and WP-1..WP-7 stand alone.

---

## 4. Sequencing

```
WP-1 ──► WP-2 ──► WP-3        (same files; do as one focused change)
             └──► WP-4 ──► (WP-8 decision)
WP-5, WP-6, WP-7  (independent, can go in parallel)
WP-A  ── ADR first; block on decision
```

Recommend landing WP-1+WP-2+WP-3 as a single change-log entry (one atomic
"fail-closed + validated SoT" change), then WP-4, then the rest.

## 5. Verification (run before declaring done)

```sh
# from commerce-agent/
uv run pytest tests/unit/test_amazon_policy.py tests/unit/test_post_purchase_cases.py -q
uv run python evals/engine_agreement.py        # MUST print: shared-surface agreement = 1.000
uv run python -m app.returns.render            # regenerate config/knowledge/amazon-returns.md
uv run pytest tests/unit/test_amazon_policy.py::test_rendered_prose_matches_sot -q
./scripts/ci.sh                                 # full gate
```

After any SoT edit you **must** regenerate the rendered corpus (it is a build artifact
and a test asserts byte equality).

## 6. Definition of done

- Every WP landed has a `specs/change-log.json` entry with `blast_radius`, `rollback`,
  and `evidence` (the gate fails entries that omit them).
- Engine/module changes have before/after numbers in `specs/RESULTS.md` / `evals/report.md`.
- `docs/architecture.md` and the relevant spec's tasks are updated (P1).
- No regression to the shared-surface agreement or the rendered-prose test.

## 7. Open questions for the owner

1. **WP-A**: do we revisit the "no configurable policy engine" decision at all? (This is
   the single biggest design fork.)
2. **WP-2**: is `ESCALATE` acceptable where today a missing window clause silently returns
   `INELIGIBLE`? (It changes a small number of case outcomes; confirm against the labeled
   set in `evals/post_purchase_cases.jsonl`.)
3. **WP-4**: `decision_id` source — session-scoped counter, or a uuid? And do we log the
   raw facts (they include order ids) or a redacted form?
4. **WP-6**: canonical tool name — `search_policies` (spec) or `search_knowledge` (code)?

## 8. Sources (the industry patterns this handoff borrows from)

- OPA — policy language, `opa test` (coverage, table-driven tests), bundles (revision +
  signing), decision logs (decision_id, replay, masking):
  https://www.openpolicyagent.org/docs/policy-language/ ,
  https://openpolicyagent.org/docs/policy-testing ,
  https://www.openpolicyagent.org/docs/management-bundles ,
  https://www.openpolicyagent.org/docs/management-decision-logs
- AWS Cedar — schema-at-authoring, analyzable policies, default-deny:
  https://docs.cedarpolicy.com/
- Cerbos — central policy versioning / testing / distribution / audit:
  https://docs.cerbos.dev/cerbos/latest/index.html
- OMG DMN — decision tables + explicit hit policy: https://www.omg.org/dmn/
- venmo/business-rules — rules-as-JSON for Python: https://github.com/venmo/business-rules
- Shopify Returns API — the commerce return domain model (state machine, decline reasons,
  restocking fee, financial outcome):
  https://shopify.dev/docs/apps/build/orders-fulfillment/returns-apps/build-return-management
