# Quickstart: Web Experience

## Run

```sh
# real DeepSeek (needs LLM_API_KEY in .env)
uv run --env-file .env uvicorn web.main:app --host 127.0.0.1 --port 8000

# or, with the helper (opens the browser)
./scripts/serve.sh
```

Open http://127.0.0.1:8000.

## Manual check (the Web Acceptance path)

1. On load: suggestion chips are visible; the input is focused; the budget meter
   reads `—`.
2. Click a chip (fills the input), then Send.
3. Expect: status shows "Thinking…" then "Responding…"; a `search_products` step
   appears and turns `ok`; the reply renders formatted markdown; a sources card
   lists the product(s); the budget meter updates.
4. Press **Stop** during a turn: the request cancels, the partial reply stays.
5. Force an error (stop the server mid-stream): an inline error with **Retry**
   appears.
6. Keyboard: Tab to the input, type, press Enter; focus is always visible.
7. Resize to 375px: no horizontal scroll. Toggle the OS theme: colors switch.

## Automated checks

```sh
uv run ruff check . && uv run ruff format --check .
uv run pyright
uv run pytest -q
uv run python scripts/spec_review.py 002-web-experience
uv run python scripts/verify_notes.py
```

## Browser checkpoint

Driven with Playwright (agent-side). Scenario: the Web Acceptance path above;
capture `specs/002-web-experience/checkpoint.png` and record the result in
`specs/002-web-experience/checkpoint.md` (SR-4/SR-5).

## Vendored assets

`web/static/vendor/marked.min.js` and `web/static/vendor/purify.min.js` are
pinned, committed copies. To update, replace the file and record the new version
in `docs/ui-conventions.md` (or a follow-up Agent Note). No CDN at runtime.
