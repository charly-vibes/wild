#!/usr/bin/env python3
# Purpose: Held-out checker adapter — the existing CI tool (consumer test
#   suite under real Cargo).
# Responsibilities: For one case id, replay the case's authorized phase
#   through real Cargo against the frozen registry (via the committed
#   update_eval.py replay machinery) and map the observed outcome to a
#   verdict.
# Rationale: "CI" arm of the wild-1xk comparison — the strong baseline is
#   the consumer's own test suite executed by the host. Grading comes from
#   real process exit codes and lockfile content (replay classifies, never
#   canned responses); the mapping below is the only adapter logic.

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
# Stays under heldout_eval.CHECKER_TIMEOUT_SECONDS=60 so a hung replay is
# attributed to this adapter, not to the harness kill.
ADAPTER_TIMEOUT_SECONDS = 55

REJECT_OUTCOMES = {
    "resolved-then-consumer-tests-failed",
    "resolved-then-consumer-build-failed",
    "resolution-conflict",
}
ACCEPT_OUTCOMES = {"resolved-and-consumer-tests-passed"}
UNKNOWN_OUTCOMES = {
    "resolution-refused-by-range",
    "resolved-but-selected-target-mismatch",
    "resolved-and-selected-target-matches",
    "resolved",
    "baseline-tests-passed",
    "baseline-tests-failed",
}


def map_replay_outcome(outcome: str) -> str:
    if outcome in ACCEPT_OUTCOMES:
        return "accept"
    if outcome in REJECT_OUTCOMES:
        return "reject"
    if outcome in UNKNOWN_OUTCOMES:
        return "unknown"
    return "error"


def _emit(verdict: str, note: str = "") -> None:
    payload = {"verdict": verdict}
    if note:
        payload["note"] = note
    print(json.dumps(payload))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="CI (consumer test suite) checker for one case")
    parser.add_argument("case_id")
    parser.add_argument("--fixtures", default="experiments/update_fixtures/e5")
    parser.add_argument("--phase", default="authorized")
    args = parser.parse_args()

    try:
        proc = subprocess.run(
            [sys.executable, str(REPO / "experiments" / "update_eval.py"),
             "replay", "--fixtures", str(Path(args.fixtures)),
             "--case", args.case_id, "--phase", args.phase],
            cwd=REPO, capture_output=True, text=True,
            timeout=ADAPTER_TIMEOUT_SECONDS)
        # replay exits 0 on expected-match, 1 on observed!=expected (a graded
        # outcome, not a checker failure), 2 on refusal.
        if proc.returncode not in (0, 1):
            _emit("error",
                  f"replay exited {proc.returncode}; "
                  f"stderr tail: {proc.stderr[-200:]!r}")
            return 0
        record = json.loads(proc.stdout)
        observed = record.get("observed_outcome", "")
        verdict = map_replay_outcome(observed)
        note = "" if verdict != "error" else f"unmapped replay outcome: {observed!r}"
        _emit(verdict, note)
        return 0
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
        _emit("error", f"replay invocation failed: {exc}")
        return 0


if __name__ == "__main__":
    sys.exit(main())