#!/usr/bin/env python3
# Purpose: Held-out checker adapter — host declared version ranges.
# Responsibilities: For one case id, read the consumer's committed Cargo.toml
#   dept requirement (the pre-update host declaration) and decide whether the
#   declared range allows the update target.
# Rationale: "Host declared ranges" arm of the wild-1xk comparison. The
#   verdict is range-level only: it says whether the host's own declaration
#   permits the target, independent of actual compatibility. Uses real
#   committed manifest bytes and Cargo's documented requirement semantics.

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _cargo_semver import requirement_allows  # noqa: E402

REPO = Path(__file__).resolve().parents[2]


def _emit(verdict: str, note: str = "") -> None:
    payload = {"verdict": verdict}
    if note:
        payload["note"] = note
    print(json.dumps(payload))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="host declared-range checker for one held-out case")
    parser.add_argument("case_id")
    parser.add_argument("--context", default="experiments/heldout/case_context.json")
    args = parser.parse_args()

    context = json.loads((Path(args.context)).read_text(encoding="utf-8"))
    entry = next((c for c in context["cases"] if c["id"] == args.case_id), None)
    if entry is None:
        _emit("error", f"case {args.case_id!r} not in context")
        return 0
    manifest = REPO / entry["consumer"] / "Cargo.toml"
    try:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        requirement = data["dependencies"]["dept"]
        if not isinstance(requirement, str):
            raise ValueError("dept dependency is not a plain requirement")
    except (OSError, tomllib.TOMLDecodeError, KeyError, ValueError) as exc:
        _emit("error", f"unreadable host declaration: {exc}")
        return 0
    try:
        allowed = requirement_allows(requirement, entry["target"])
    except ValueError as exc:
        _emit("error", str(exc))
        return 0
    _emit("accept" if allowed else "reject")
    return 0


if __name__ == "__main__":
    sys.exit(main())