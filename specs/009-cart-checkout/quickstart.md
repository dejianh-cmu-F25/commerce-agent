# Quickstart: Cart and Checkout

## Run

```sh
uv run --env-file .env uvicorn web.main:create_app --factory --host 127.0.0.1 --port 8000
```

## Verify

1. Open `/`, ask "I need a tent under $250", then "add it to my cart": a cart card
   shows the tent and the total.
2. Ask "what's in my cart": the cart card is shown again (quantity preserved).
3. Ask "checkout": a checkout card shows the summary and states nothing is
   charged.
4. Try to add an id the session has not seen (e.g. "add product P-999"): the tool
   returns an error; the cart is unchanged.

## Automated checks

```sh
scripts/ci.sh --fast
```

## Browser checkpoint

Recorded at `specs/009-cart-checkout/checkpoint.md` (SR-4/SR-5).
