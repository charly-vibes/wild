#!/usr/bin/env python3
"""Purpose: reproduce bounded evidence for the semantic-composition investigation.

Responsibilities: exercise existing Wild toy checks and enumerate six schedules
of a two-layer reservation example. Rationale: distinguish observed toy results
from proposed v1 conformance or real concurrent-system guarantees.
"""
import itertools
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT / "prototype"))
import wild_cat_sim as cat
import wild_sim as sim


def reservation(atomic, schedule):
    """Coordinator reads, then asks storage to commit a terminal state.

    Atomic storage compares current state; stale storage trusts the prior read.
    Public observations are successful terminal responses, not internal reads.
    """
    state = "held"
    reads = {}
    observations = []
    for operation, phase in schedule:
        if phase == "read":
            reads[operation] = state
        elif (state if atomic else reads[operation]) == "held":
            state = operation
            observations.append(operation)
    return observations


def main():
    events = [(op, phase) for op in ("confirmed", "expired")
              for phase in ("read", "commit")]
    schedules = [p for p in itertools.permutations(events)
                 if all(p.index((op, "read")) < p.index((op, "commit"))
                        for op in ("confirmed", "expired"))]
    rows = []
    for schedule in schedules:
        good = reservation(True, schedule)
        bad = reservation(False, schedule)
        rows.append({"schedule": schedule, "atomic_trace": good,
                     "stale_trace": bad,
                     "atomic_violation": len(set(good)) > 1,
                     "stale_violation": len(set(bad)) > 1})
    shape = sim.Contract({"read": sim.Slot("out", "str"),
                          "commit": sim.Slot("out", "str")})
    certs = cat.cert_study(n=10, seed=9)
    certs.pop("avg_verify_ms", None)  # timings are not comparative evidence here
    print(json.dumps({
        "scope": "toy checks and exhaustive six-schedule illustrative model",
        "category": cat.laws(),
        "substitution": cat.theorem(trials=1000, seed=11),
        "certificates": certs,
        "same_shape_accretion": sim.shape_check(shape, shape)[0],
        "reservation": {"initial_state": "held", "schedules": len(rows),
                        "atomic_violations": sum(r["atomic_violation"] for r in rows),
                        "stale_violations": sum(r["stale_violation"] for r in rows),
                        "rows": rows},
        "existing_behavior_cases": [sim.run_variant(v) for v in sim.V
                                    if v["id"] in ("3b", "3c", "3d", "4c")]
    }, indent=2))


if __name__ == "__main__":
    main()
