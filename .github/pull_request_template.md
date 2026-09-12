## Feature

- Spec: `specs/00X-name/spec.md`
- Feature ID: `00X`

## Tasks completed

- [ ] T001 …
- [ ] T002 …

## Verification

- [ ] `ruff check . && ruff format --check .`
- [ ] `pyright`
- [ ] `pytest tests/unit tests/integration`
- [ ] `python evals/run.py` (keyless replay) — if the feature touches model behavior
- [ ] Image builds: `docker build .`

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

## Decision record

- [ ] Agent Note added/updated under `docs/notes/` (DR-1) — or the change is trivial

## Risks / follow-ups
