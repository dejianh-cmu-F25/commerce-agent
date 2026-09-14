# Amazon return policy (2026-09)

> Derived from `config/policies/amazon.yaml` (single source of truth).
> Do not edit by hand; regenerate with `python -m app.returns.render`.

Source: [amazon-returns-2026](https://www.amazon.com/gp/help/customer/display.html?nodeId=GKM69DUUYKQWKWX7) — retrieved 2026-09-14.

## returns#window-default

Most items can be returned within 30 days of delivery.

Rules: `window_days=30`

## returns#window-category

Some categories have shorter or longer windows (7 / 15 / 90 / 180 / 365 days).

Rules: `window_days_by_category={'digital_book': 7, 'digital_textbook': 7, 'digital_music': 7, 'apple_brand': 15, 'haul_over_3': 15, 'renewed_acceptable': 90, 'renewed_good': 90, 'renewed_excellent': 90, 'baby_nonperishable': 90, 'birthday_gift': 90, 'custom_gift_list': 90, 'mattress': 90, 'wedding_registry_gift': 180, 'renewed_premium': 365, 'baby_registry_gift': 365}`

## returns#non-returnable

Perishables, health/safety-risk, shipping-restricted, customized, redeemable, pharmacy, pet medication, some digital, automobiles, and Final Sale items cannot be returned.

Rules: `non_returnable_categories=['perishable', 'health_safety', 'shipping_restricted', 'customized', 'redeemable', 'pharmacy', 'pet_medication', 'digital_nonreturnable', 'automobile', 'final_sale', 'trading_card_game', 'haul_under_3']`

## returns#condition

Items must be returned in original or unused condition with tags, seals, and original packaging.

Rules: `condition_required=original_unused`

## returns#fee-late

A late fee may apply if the item is not dropped off by the return-by date: 20% of the item price for the first 30 days after, then 100%.

Rules: `late_fee_pct_first_30d=20`, `late_fee_pct_after_30d=100`

## returns#fee-damage

A damage fee of up to 50% of the item price may apply if the item is damaged, missing parts, or not in original condition (100% for Luxury items).

Rules: `damage_fee_pct_max=50`, `damage_fee_pct_luxury=100`

## returns#fee-restocking

A 100% restocking fee applies to opened, activated, or incomplete software, video games, and collectible cards.

Rules: `restocking_fee_pct=100`, `restocking_categories=['opened_software', 'video_games', 'collectible_cards']`

## returns#exception

A non-returnable or Final Sale item that arrives damaged, defective, or materially different is handled by Customer Service.

Rules: `exception_reasons=['damaged', 'defective', 'wrong_item', 'missing']`

## returns#heavy-bulky

Heavy/bulky items (>= 50 lb, longest side > 59 in, or girth > 130 in) may incur a variable return shipping fee.

Rules: `heavy_bulky={'weight_lb': 50, 'longest_side_in': 59, 'girth_in': 130}`

## returns#bundle

All items in a Bundle with Savings must be returned together; partial refunds are not available.

Rules: `bundle_return_all=True`

## returns#discount

Returning an item that was part of a discount qualification reduces the refund accordingly.

Rules: `discount_refund_reduction=True`

## returns#warranty

Manufacturer warranties are handled by the manufacturer, not as a return; a manufacturer warranty may not cover used products.

Rules: `warranty_is_separate=True`
