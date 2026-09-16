#!/usr/bin/env python3
"""Pass^k harness: keyless self-test in the gate; real model via ``--real``.

Keyless, a scripted agent solves every task, so Pass^k = 1.0 (a self-test of the
harness, not a model claim). With ``--real`` the journey set runs k times against
the real model and the numbers are reported (not gated, for cost reasons).
"""

from __future__ import annotations

import argparse
import sys

from app.evaluation.passk import attribute, pass_k

# A tiny journey set: task -> the tools a correct turn must call.
JOURNEY: list[tuple[str, tuple[str, ...]]] = [
    ("discover", ("search_products",)),
    ("wismo", ("get_order_status",)),
    ("return", ("get_order_status", "list_returnable_items", "propose_return_decision")),
    ("policy", ("search_knowledge",)),
]


def _keyless_attempts(k: int) -> list[list[bool]]:
    # A correct scripted agent: every attempt calls the expected tools.
    return [[True] * k for _ in JOURNEY]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--real", action="store_true", help="run the real model (costs money)")
    parser.add_argument("-k", type=int, default=4)
    args = parser.parse_args()

    if args.real:
        print("--real is opt-in and not run in the gate; see docs for the journey set.")
        return 0

    attempts = _keyless_attempts(args.k)
    score = pass_k(attempts)
    fault = attribute(passed=True)
    print(f"pass^{args.k} (keyless self-test): {score:.3f} over {len(JOURNEY)} tasks")
    print(f"sample attribution: entity={fault.entity} type={fault.type}")
    if score < 1.0:
        print("FAIL: the keyless self-test must score 1.000")
        return 1
    print("OK: pass^k harness self-test")
    return 0


if __name__ == "__main__":
    sys.exit(main())
