## Feature

- Spec: `specs/00X-name/spec.md`
- Feature ID: `00X`

## Tasks completed

- [ ] T001 …
- [ ] T002 …

## Verification

- [ ] Local gate passes: `scripts/ci.sh` (or `make ci`) — ruff + format, pyright,
      pytest unit+integration, spec self-review, agent notes, frontend lint/typecheck/test/build
- [ ] `scripts/ci.sh --with-image` — if the change touches the image, CI, or the build
- [ ] `python evals/run.py` (keyless replay) — if the feature touches model behavior

## Web acceptance (WV-2)

<!-- What a reviewer clicks in the browser to see this feature work. -->

## Human review checklist (GH-3)

- [ ] Spec and implementation are consistent
- [ ] No hardcoded provider, model, or path (PB-1)
- [ ] Prompts live under `config/prompts/` (PB-4)
- [ ] Traces emitted for the new path (SL-2 / OB)
- [ ] Fallback is explicit and config-gated (RD-1)
- [ ] Ingestion/data writes are idempotent (RD-2)
- [ ] Guides and sensors both considered (HR-3)
- [ ] Code is simple and readable; comments explain *why* (CQ)

## Real-world coverage (RW / SC — constitution v1.3.0)

<!-- Fill this in when the change touches inputs, data, the model, or retrieval. -->

- [ ] Input distribution covered, including unseen / adversarial input (RW-1)
- [ ] Dirty / missing / conflicting data has defined behavior and a repair path (RW-2)
- [ ] Edge and failure modes enumerated with a behavior each (RW-3)
- [ ] Fixes are root-caused and ship with a regression (RW-4)
- [ ] External dependencies have an observable, config-gated fallback (RW-5)
- [ ] Scale envelope declared and measured at the stated boundary (SC-1)
- [ ] Failures attributable; metrics segmentable (intent / tool / model / tenant) (SC-2)
- [ ] Latency / cost / error budgets declared and tracked (SC-3)
- [ ] Blast radius and rollback stated (SC-4)

## Change evidence (EV)

- [ ] Model / prompt / retrieval / module change has a before/after on the gold set (EV-1)
- [ ] Paired with multiple seeds; effect size and sample size reported (EV-2)
- [ ] Guardrail metrics (quality, safety, latency, cost) did not regress (EV-3)
- [ ] Model and rendered-prompt hash recorded with the results (EV-4)
- Evidence: `specs/RESULTS.md` / `evals/report.md`

## Self-review report (SR-1..SR-3)

- [ ] `python scripts/spec_review.py <NNN>-<name>` — no FAIL
- Report: `specs/<NNN>-<name>/review.md`
- Manual clauses confirmed: …

## Decision record

- [ ] Agent Note added/updated under `docs/notes/` (DR-1) — or the change is trivial

## Risks / follow-ups
