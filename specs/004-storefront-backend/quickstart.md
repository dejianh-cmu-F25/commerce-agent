# Quickstart: Storefront Backend

## Configure

`config/settings.yaml`:

```yaml
storefront:
  provider: sqlite          # memory | sqlite
  sqlite_path: ./data/db/storefront.sqlite
```

Env overrides: `STOREFRONT_PROVIDER`, `STOREFRONT_SQLITE_PATH`.

## Run

```sh
uv run --env-file .env uvicorn web.main:app --host 127.0.0.1 --port 8000
# or: ./scripts/serve.sh
```

## Verify

1. Open `/`, ask for a tent; the `search_products` step completes and sources list
   the product(s) — now read from the backend.
2. Confirm the SQLite file exists and is seeded:
   ```sh
   sqlite3 data/db/storefront.sqlite "select id,title,price,stock from products;"
   ```
3. Restart the app and re-run the query; the product count is unchanged
   (idempotent seeding).

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

The catalog behavior is user-visible, so a checkpoint is recorded at
`specs/004-storefront-backend/checkpoint.md` (SR-4/SR-5).
