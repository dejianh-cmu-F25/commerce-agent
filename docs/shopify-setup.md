# Shopify dev store setup (free)

This project reads real orders and returnable items from a **Shopify development
store** — a real Admin GraphQL API with real schemas, pagination, rate limits, and
the real returns state machine. It is free and needs no production data.

You do this once; then set three env vars and the adapter uses the real API.

## 1. Create a Partner account and a development store

1. Sign up at <https://partners.shopify.com> (free).
2. Partners dashboard → **Stores** → **Add store** → **Create development store**.
3. Choose **"Create a store to test and build"**.
4. With the Shopify CLI you can pre-populate demo data:
   ```sh
   shopify store create dev --with-demo-data
   ```
   or, in the dashboard, pick a theme/vertical so the store is not empty.
5. Note the store domain, e.g. `my-store.myshopify.com`.

## 2. Create an app and get an Admin API token

1. Partners dashboard → **Apps** → **Create app** → **Create app manually**.
2. Copy the **Admin API access token** (starts with `shpat_`).
3. Under **Configuration → Admin API scopes**, grant at least:
   - `read_orders` (phase 0–1: reads)
   - `read_products` (product/title context)
   - later, for the gated write (phase 3): `write_returns` (or `write_orders`)
4. Install the app on your development store (the dashboard prompts you).

> The token is a secret. Put it in `.env` (never commit it; `.env` is gitignored).

## 3. Configure

```sh
# .env
SHOPIFY_SHOP=my-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2025-07
```

## 4. Smoke test

```sh
uv run python - <<'PY'
import asyncio, os
from app.adapters.shopify_client import ShopifyAdminClient

async def main():
    admin = ShopifyAdminClient(os.environ["SHOPIFY_SHOP"], os.environ["SHOPIFY_ACCESS_TOKEN"])
    data = await admin.query("{ shop { name } }")
    print(data)
    print("cost:", admin.last_cost)

asyncio.run(main())
PY
```

Then list a real order and its returnable items:

```sh
uv run python - <<'PY'
import asyncio, os
from app.adapters.shopify_client import ShopifyAdminClient
from app.adapters.shopify_post_purchase import ShopifyPostPurchase

async def main():
    admin = ShopifyAdminClient(os.environ["SHOPIFY_SHOP"], os.environ["SHOPIFY_ACCESS_TOKEN"])
    backend = ShopifyPostPurchase(admin)
    data = await admin.query("{ orders(first: 1) { edges { node { id name } } } }")
    order_id = data["orders"]["edges"][0]["node"]["id"]
    print("order:", await backend.get_order(order_id))
    print("returnable:", await backend.returnable_items(order_id))

asyncio.run(main())
PY
```

## 5. What is real vs test data (be honest in the README)

- **Real**: the API, the schema, the returns state machine, pagination, rate
  limits, GraphQL query cost, and the app-auth model.
- **Test**: the store's products/orders are generated demo data.
- Do **not** claim the catalog is real; claim the **integration and the domain
  logic** are real. That is the honest and still-strong framing.

## Notes

- Rate limits: the GraphQL Admin API is **cost-based** (leaky bucket). Read
  `extensions.cost.actualQueryCost` (the client records it in `last_cost`) and
  budget accordingly.
- The API version is pinned in config; bump it deliberately and re-run the evals.
