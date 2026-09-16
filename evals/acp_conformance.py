#!/usr/bin/env python3
"""ACP checkout conformance (keyless, feature 046, SC-006).

Asserts the create -> update -> complete lifecycle, that a premature complete
fails, and that **no charge is ever issued**.
"""

from __future__ import annotations

import sys

from app.adapters.acp_checkout import AcpCheckout
from app.ports.checkout import COMPLETED, CREATED, FAILED, READY


def main() -> int:
    checkout = AcpCheckout()
    failures: list[str] = []

    session = checkout.create_session("cart_1", 42.0)
    if session.status != CREATED:
        failures.append(f"create status {session.status!r} != {CREATED!r}")

    ready = checkout.update_session(session.id, "1 Main St")
    if ready.status != READY:
        failures.append(f"update status {ready.status!r} != {READY!r}")

    done = checkout.complete(session.id)
    if done.status != COMPLETED:
        failures.append(f"complete status {done.status!r} != {COMPLETED!r}")
    if done.charge_issued:
        failures.append("a charge was issued (forbidden)")
    if not done.payment_token:
        failures.append("no simulated payment token")

    fresh = checkout.create_session("cart_2", 10.0)
    if checkout.complete(fresh.id).status != FAILED:
        failures.append("completing a non-ready session must fail")

    if failures:
        print("FAIL: " + "; ".join(failures))
        return 1
    print("OK: ACP conformance (create -> ready -> complete; no charge)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
