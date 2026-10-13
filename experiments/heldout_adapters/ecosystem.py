#!/usr/bin/env python3
# Purpose: Held-out checker adapter — the ecosystem compatibility ruling
#   (Cargo's own semver caret rule).
# Responsibilities: For one case id, decide whether the update target is
#   caret-compatible with the base resolved version per Cargo's documented
#   rule (major>0: same major; 0.x: same minor; 0.0.z: exact patch).
# Rationale: "Ecosystem compatibility tools" arm of the wild-1xk comparison.
#   Cargo's caret semantics are the ecosystem's standard compatibility
#   ruling; applying it to the base/target pair is the offline-deterministic
#   form of that ruling (basis recorded in the report). Uses real context
#   versions derived from committed locks.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _cargo_semver import cargo_caret_compatible  # noqa: E402


def _emit(verdict: str, note: str = "") -> None:
    payload = {"verdict": verdict}
    if note:
        payload["note"] = note
    print(json.dumps(payload))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ecosystem caret-compatibility checker for one case")
    parser.add_argument("case_id")
    parser.add_argument("--context", default="experiments/heldout/case_context.json")
    args = parser.parse_args()

    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    entry = next((c for c in context["cases"] if c["id"] == args.case_id), None)
    if entry is None:
        _emit("error", f"case {args.case_id!r} not in context")
        return 0
    try:
        compatible = cargo_caret_compatible(entry["base"], entry["target"])
    except ValueError as exc:
        _emit("error", str(exc))
        return 0
    _emit("accept" if compatible else "reject")
    return 0


if __name__ == "__main__":
    sys.exit(main())