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

## Self-review report (SR-1..SR-3)

- [ ] `python scripts/spec_review.py <NNN>-<name>` — no FAIL
- Report: `specs/<NNN>-<name>/review.md`
- Manual clauses confirmed: …

## Decision record

- [ ] Agent Note added/updated under `docs/notes/` (DR-1) — or the change is trivial

## Risks / follow-ups
