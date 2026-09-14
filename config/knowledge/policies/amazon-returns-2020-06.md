# Amazon return policy (2020-06)

> Derived from `config/policies/amazon.yaml` (single source of truth).
> Do not edit by hand; regenerate with `python -m app.returns.render`.

Source: [amazon-returns-2020](https://web.archive.org/web/20200624054055/https://www.amazon.com/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7) — retrieved 2020-06-24.

## returns#window-default

Most items could be returned within 30 days of receipt of shipment.

Rules: `window_days=30`

## returns#temporary-covid

Items ordered 2020-03-01..2020-04-30 could be returned until 2020-05-31 (a temporary extension).

Rules: `temporary_extension={'ordered_from': '2020-03-01', 'ordered_to': '2020-04-30', 'return_by': '2020-05-31'}`

## returns#fee-misrepresentation

A 15% fee could apply to computers returned because they 'didn't start' if the condition was misrepresented.

Rules: `misrepresentation_fee_pct=15`, `applies_to_categories=['computer', 'laptop', 'tablet']`

## returns#exception

Damaged, defective, or incorrect items were handled by Customer Service.

Rules: `exception_reasons=['damaged', 'defective', 'wrong_item', 'missing']`
