# Shopify dev store + Admin API token (free)

Goal: a real Shopify development store and an **Admin API access token**
(`shpat_...`) so the agent reads real orders and returnable items. Free, ~10
minutes. No production data.

You only do this once. Then set three env vars and the adapter uses the real API.

---

## Step 1 — Create a development store

**Option A (Dev Dashboard, recommended):**

1. Go to <https://dev.shopify.com/dashboard/> and sign in (create a free account
   if needed).
2. Left sidebar → **Stores** → **Create store**.
3. Store type → **Dev**.
4. Enter a name (e.g. `post-purchase-agent`). This becomes the
   `<name>.myshopify.com` domain.
5. Pick a plan (**Basic** is fine) → **Create store**.
6. Open the store admin and log in.

**Option B (Shopify CLI):**

```sh
shopify store create dev --name "post-purchase-agent" --plan basic --demo-data
```

`--demo-data` (or `--with-demo-data` on older CLI versions) pre-populates
products, customers, and orders — so you are not testing against an empty store.

> Note the store domain, e.g. `post-purchase-agent.myshopify.com`.

---

## Step 2 — Get an Admin API access token

### Path 1 — Custom app in the store admin (fewest steps; try this first)

1. In the **store admin**, go to **Settings** → **Apps and sales channels**.
2. Click **Develop apps** (if prompted, click **Allow custom app development**).
3. **Create an app** → name it `post-purchase-agent`.
4. Open **Configuration** → **Admin API integration** → **Configure**.
5. Enable these scopes:
   - `read_orders` (orders, fulfillments, transactions)
   - `read_products` (product/title context)
   - `read_returns` (**required** for `returnableFulfillments`)
   - `write_returns` (the gated write in phase 3; add it now to avoid a second
     install)
6. **Save**.
7. Open the **API credentials** tab → **Install app**.
8. Copy the **Admin API access token** (starts with `shpat_`). It is shown once —
   copy it now.

### Path 2 — App in the Dev Dashboard (if Path 1 is unavailable)

1. Dev Dashboard → **Apps** → **Create app** → **Create app manually**.
2. Copy the **Client ID** and **Client secret**.
3. Under **Configuration → Admin API scopes**, add `read_orders`, `read_products`,
   `read_returns`, and `write_returns`.
4. **Install** the app on your dev store (the dashboard offers a
   "Test on development store" / install link).
5. Server-side, exchange the credentials for a token with the **client
   credentials grant** (no redirect needed):
   ```sh
   curl -s -X POST "https://<store>.myshopify.com/admin/oauth/access_token" \
     -H "Content-Type: application/json" \
     -d '{"client_id":"<id>","client_secret":"<secret>","grant_type":"client_credentials"}'
   ```
   The response contains `access_token` (starts with `shpat_`). It expires in
   ~24h; re-run the request to refresh.

> **Token prefixes:** `shpat_` = Admin API access token; `shppa_` = delegate
> access token. We use an Admin API token.

---

## Step 3 — Configure the project

Create/update `.env` in the repo root (`.env` is gitignored — never commit it):

```sh
SHOPIFY_SHOP=post-purchase-agent.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2025-07
```

---

## Step 4 — Verify

**4a. The token works (shop name):**

```sh
curl -s "https://$SHOPIFY_SHOP/admin/api/$SHOPIFY_API_VERSION/graphql.json" \
  -H "X-Shopify-Access-Token: $SHOPIFY_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"{ shop { name myshopifyDomain } }"}'
```

Expected: `{"data":{"shop":{"name":"...","myshopifyDomain":"..."}}}`.

**4b. The project reads a real order and its returnable items:**

```sh
uv run python - <<'PY'
import asyncio, os
from app.adapters.shopify_client import ShopifyAdminClient
from app.adapters.shopify_post_purchase import ShopifyPostPurchase

async def main():
    admin = ShopifyAdminClient(os.environ["SHOPIFY_SHOP"], os.environ["SHOPIFY_ACCESS_TOKEN"])
    backend = ShopifyPostPurchase(admin)
    data = await admin.query("{ orders(first: 1) { edges { node { id name } } } }")
    edges = data["orders"]["edges"]
    if not edges:
        print("No orders yet — create a test order (see below).")
        return
    order_id = edges[0]["node"]["id"]
    print("order:", await backend.get_order(order_id))
    print("returnable:", await backend.returnable_items(order_id))
    print("cost:", admin.last_cost)

asyncio.run(main())
PY
```

---

## Step 5 — Create a test order (so there is something to return)

1. In the store admin, **Orders** → **Create order** → add a product → **Mark as
   paid** → **Fulfill** the item.
2. Or in the storefront, use the **Bogus payment gateway** (enabled on dev
   stores) to place a test checkout.
3. If your store was created with demo data, orders may exist as **draft
   orders** — mark one as paid to convert it.

A returnable item requires the order to be **fulfilled**. If
`returnable_items` is empty, fulfill the order first.

---

## Troubleshooting

| Symptom | Cause / fix |
| --- | --- |
| `401 Unauthorized` | Wrong/expired token, or the app is not installed on this store. |
| `403 Forbidden` | The token is valid but lacks the scope — add the missing scope and re-install. |
| `Access denied for returnableFulfillments field` | Missing `read_returns`; add it and re-install the app. |
| `Field 'returnableFulfillments' doesn't exist` | API version too old; set `SHOPIFY_API_VERSION` to a recent version (e.g. `2025-07`). |
| `returnable_items` is empty | The order is not fulfilled, or everything is already refunded. |
| `429` / throttled | Cost-based rate limit; watch `extensions.cost` (the client records `last_cost`). |

## What is real vs test data (say this honestly)

- **Real:** the API, the schema, the returns state machine, pagination, rate
  limits, GraphQL cost, and the app-auth model.
- **Test:** the store's products and orders are generated demo data.
- Do **not** claim the catalog is real. Claim the **integration and domain logic**
  are real — that is honest and still strong.
