# Quickstart: Merchant Agent

## Run

```sh
uv run --env-file .env uvicorn web.main:create_app --factory --host 127.0.0.1 --port 8000
```

## Verify

1. Open `/`, switch to **Merchant**: the inventory lists products with price/stock.
2. In **Chat**, ask "set the tent price to $199" (the agent proposes; nothing
   changes yet).
3. Back in **Merchant**: the pending change appears; click **Approve**.
4. The inventory now shows the new price and the change leaves the pending list.

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

Recorded at `specs/010-merchant-agent/checkpoint.md` (SR-4/SR-5).
