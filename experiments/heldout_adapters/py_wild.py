#!/usr/bin/env python3
# Purpose: Held-out checker adapter — the python contract tool (wild-zfw
#   python arm), the extract/demand/scoped-failure analogue of wild.py.
# Responsibilities: For one python case id, extract the consumer's demand on
#   the provider against the dev provider release, then decide whether the
#   target provider release satisfies that demand (call-site aware, the
#   committed prototype/wild_proto.py semantics — the same engine eval_py.py
#   drove as "tool v2").
# Rationale: "Wild" arm of the python comparison. The engine is frozen
#   committed code; verdicts are computed from the real installed trees
#   (pip --target per python_matrix.json protocol), never guessed. Note: the
#   section-2 tool refinements were tuned on the 28 recorded cells, so this
#   checker's results on those cells are tuning-exposed (disclosed corpus
#   ruling); fresh-matrix cells were never seen by any tuning pass.

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "prototype"))
import wild_proto as P  # noqa: E402

DEFAULT_PYTHON_ROOT = "/tmp/wild-zfw-scratch/pytrees"


def _emit(verdict: str, note: str = "") -> None:
    payload = {"verdict": verdict}
    if note:
        payload["note"] = note
    print(json.dumps(payload))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="python contract-tool checker for one held-out case")
    parser.add_argument("case_id")
    parser.add_argument("--context", default="experiments/heldout/case_context.json")
    parser.add_argument("--python-root", default=DEFAULT_PYTHON_ROOT)
    args = parser.parse_args()

    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    entry = next((c for c in context["cases"] if c["id"] == args.case_id), None)
    if entry is None:
        _emit("error", f"case {args.case_id!r} not in context")
        return 0
    root = Path(args.python_root)
    try:
        consumer_dir = root / f"{entry['consumer']}-{entry['consumer_version']}"
        dev_dir = root / f"{entry['provider']}-{entry['dev']}"
        target_dir = root / f"{entry['provider']}-{entry['target']}"
        prov_dev = P.extract_py(str(dev_dir), entry["provider"])
        calls: dict = {}
        demand, unresolved = P.demand_py(str(consumer_dir), entry["consumer"],
                                         entry["provider"], prov_dev, calls)
        if entry["target"] == entry["dev"]:
            failures: list = []
        else:
            prov_to = P.extract_py(str(target_dir), entry["provider"])
            failures = P.scoped_failures_calls(prov_dev, prov_to, demand, calls)
    except Exception as exc:  # noqa: BLE001 — honest error verdict, never a guess
        _emit("error", f"contract-tool evaluation failed: {exc}")
        return 0
    head = "; ".join(f"{name}: {detail}" for name, detail in failures[:2])
    _emit("reject" if failures else "accept",
          f"demand={len(demand)} unresolved={len(unresolved)} "
          f"failures={len(failures)} {head}"[:200])
    return 0


if __name__ == "__main__":
    sys.exit(main())
