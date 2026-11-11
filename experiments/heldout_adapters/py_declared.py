#!/usr/bin/env python3
# Purpose: Held-out checker adapter — the declared-range ruling for python
#   cells (wild-zfw python arm), the PEP 440 analogue of host_ranges.py.
# Responsibilities: For one python case id, read the consumer's installed
#   METADATA Requires-Dist entry for the provider and decide whether the
#   declared specifier set admits the update target version.
# Rationale: "Declared ranges" arm of the python comparison. The declared
#   range is read from real installed metadata bytes (pip --target trees
#   installed per python_matrix.json protocol); PEP 440 semantics come from
#   the vendored packaging library (experiments/heldout_adapters/_vendor),
#   never ad-hoc version math. Ephemeral trees are reinstallable from the
#   committed matrix spec; the checker measures the host's own declaration.

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "_vendor"))
try:  # repo-local vendor first, then pip's own vendored packaging
    from packaging.specifiers import SpecifierSet  # noqa: E402
    from packaging.version import Version  # noqa: E402
except ImportError:  # pragma: no cover — dev sandboxes without repo _vendor
    from pip._vendor.packaging.specifiers import SpecifierSet  # noqa: E402
    from pip._vendor.packaging.version import Version  # noqa: E402

DEFAULT_PYTHON_ROOT = "/tmp/wild-zfw-scratch/pytrees"


def _emit(verdict: str, note: str = "") -> None:
    payload = {"verdict": verdict}
    if note:
        payload["note"] = note
    print(json.dumps(payload))


def _declared(metadata_path: Path, provider: str) -> str:
    for line in metadata_path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(rf"Requires-Dist:\s*{re.escape(provider)}\s*(.*)", line, re.I)
        if m:
            return re.sub(r"[()\s]", "", m.group(1).split(";")[0]) or ""
    raise ValueError(f"no Requires-Dist entry for {provider!r} in {metadata_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="python declared-range (PEP 440) checker for one held-out case")
    parser.add_argument("case_id")
    parser.add_argument("--context", default="experiments/heldout/case_context.json")
    parser.add_argument("--python-root", default=DEFAULT_PYTHON_ROOT)
    args = parser.parse_args()

    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    entry = next((c for c in context["cases"] if c["id"] == args.case_id), None)
    if entry is None:
        _emit("error", f"case {args.case_id!r} not in context")
        return 0
    try:
        consumer_dir = Path(args.python_root) / f"{entry['consumer']}-{entry['consumer_version']}"
        metas = sorted(glob.glob(str(consumer_dir / "*.dist-info" / "METADATA")))
        if not metas:
            raise ValueError(f"no dist-info METADATA under {consumer_dir}")
        spec = SpecifierSet(_declared(Path(metas[0]), entry["provider"]))
        allowed = Version(entry["target"]) in spec
    except Exception as exc:  # noqa: BLE001 — honest error verdict, never a guess
        _emit("error", f"declared-range evaluation failed: {exc}")
        return 0
    _emit("accept" if allowed else "reject",
          f"declared='{spec}' target={entry['target']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
