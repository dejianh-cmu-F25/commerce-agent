# What cross-customer isolation needs (INV-7)

`app/gates/tenancy.py` refuses to read an order that declares an owner other than the
authenticated customer, and refuses when an order declares an owner and there is no
authenticated customer. The invariant cases and `tests/unit/test_tenancy_scoping.py`
prove that behaviour against fixtures.

**It is enforced only where ownership data exists, and this deployment does not have
it.** The distinction is worth stating plainly rather than leaving implied:

| | Ownership available? | Gate outcome |
| --- | --- | --- |
| In-memory fixtures (`evals/order_fixtures.py`, the eval backends, the unit tests) | yes, `OrderView.customer_id` is set | enforced, tested |
| Live Shopify orders | **no** | the order declares no owner, so the read is allowed |

## Why the live path has none

The Shopify Admin app backing this store is **not approved for the Customer object**.
Two queries make that concrete: selecting `customer { id }` on an order fails with
`Access denied for customer field. Required access: read_customers`, and selecting the
order's `email` fails with *"This app is not approved to access the Customer object.
Access to personally identifiable information… requires approval."*

Reading either one is therefore not a code decision - the platform refuses it. An
earlier version of this change added `customer { id }` to the order queries and, as a
result, **every live order read failed** while every keyless eval kept passing, because
those run on fixtures. That is the reason this file exists.

## What a deployment must supply

Pick one, then the gate starts enforcing on the live path with no code change:

1. **Customer access on the Shopify app** (the `read_customers` scope, plus Shopify's
   PII approval for `email`). Then the order carries its owner and the mapping in
   `ShopifyPostPurchase._to_order` fills `customer_id`.
2. **A local ownership mapping** - your own `orders → customer` table, or the
   storefront-customer session - supplied to the order view. This is the route a
   non-Shopify or multi-tenant deployment would take, and it keeps the gate
   independent of platform permissions.

Until one of them exists, the honest statement is: **the isolation rule is implemented
and verified against fixtures, and its live enforcement is a deployment prerequisite**,
not "cross-customer access is prevented in production".

The same shape applies to `list_orders`: it is scoped by the authenticated principal
and refuses without one, so it cannot be used to enumerate the shop - but on this
deployment the principal has no orders to match, because the orders carry no owner.
