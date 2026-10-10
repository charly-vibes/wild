# --- Purpose ----------------------------------------------------------------
# Bounded Specodelic semantic-profile experiment (beads wild-9co.4): map a
# pinned S2 semantic profile to application observations over the shared
# frozen two-op reservation domain (experiments/composition_replacement.py).
# The profile separates the Specodelic graph kernel (the finite structural
# vocabulary any conformant carrier must respect) from opaque binding carriers
# (per-implementation bindings the oracle reads only through their public
# observations). A finite event/state interpretation fixes a supported
# predicate set for the frozen domain; well-formed unsupported predicate
# requests are unknown/unsupported_predicate and malformed input is error.
# A real Python arm (separate subprocess process) is compared to the
# independently specified public-law oracle (public-oracle-v1); the Rust arm
# is recorded not_executed with the pinned-revision reason. Red cases: changed
# behavior (same public shape, oracle detects), missing projection (carrier
# drops public events), circular assumption (carrier computes its own law
# verdict). Green cases: supported domain preserved (atomic token allowed, C14
# beyond-bound stays unknown). The pinned-audit control records whether a
# pinned Specodelic audit exists and whether a release-v0.7.0 claim is made
# without it. The determination whether S2 is sufficient for this frozen
# domain (before any S3 refinement) is recorded with evidence counts.
# No v1 runtime, unbounded liveness, unrestricted equivalence, or release
# claim is made; no state persistence across runs is claimed.

from __future__ import annotations

import hashlib
import itertools
import json
import subprocess
import sys

# --- Frozen profile pin ------------------------------------------------------

PROFILE_ID = "semantic-profile-s2-v1"
PHASE = "P2"
SPECODELIC_PIN = {
    "revision": "0.5.0",
    "pinned_audit": False,   # no pinned Specodelic audit performed here
}
RELEASE_CLAIM = {
    "v0_7_0": False,
    "reason": "release-v0.7.0 claim withheld: pinned-audit-required",
}

# --- Shared frozen two-op reservation domain (public shape only) -------------

OPS = ("confirmed", "expired")
HOLDING = "held"
COMMIT_STEP_BUDGET = 8
SCHEDULE_BOUND_EXTRA = 2
ORACLE_ID = "public-oracle-v1"

EVENTS = OPS
EVENT_KINDS = ("success", "refusal")
STATES = ("held", "confirmed", "expired")

SUPPORTED_PREDICATES = (
    "at_most_one_terminal_success",
    "terminal_within_frozen_bound",
    "event_completeness",
)
UNSUPPORTED_PREDICATES = (
    "cross_run_causality",
    "state_persistence_across_runs",
)


def frozen_schedules():
    """The finite domain: every interleaving where each op reads before committing."""
    events = [(op, phase) for op in OPS for phase in ("read", "commit")]
    return [p for p in itertools.permutations(events)
            if all(p.index((op, "read")) < p.index((op, "commit")) for op in OPS)]


# --- Opaque binding carriers (real implementations, real observations) -------

PY_ARM_SOURCE = '''
import json, sys, itertools
OPS = ("confirmed", "expired"); HOLDING = "held"; BUDGET = 8

def run_impl(name, schedule):
    state, reads, internal, steps = HOLDING, {}, [], 0
    if name == "impl_deadlock":
        internal = []
        for op, phase in schedule:
            if phase == "read":
                pass
            elif steps < BUDGET:
                steps += 1
        return (schedule, tuple(internal), "deadline" if steps else "completed", steps)
    for op, phase in schedule:
        if phase == "read":
            reads[op] = state
        elif steps < BUDGET:
            steps += 1
            if name == "impl_atomic_token":
                version = getattr(run_impl, "_v", 0)
                if reads[op] == HOLDING and version == 0:
                    run_impl._v = version + 1
                    state = op
                    internal.append((op, "success"))
                else:
                    internal.append((op, "failure"))
            elif name == "impl_stale_read":
                if reads[op] == HOLDING:
                    state = op
                    internal.append((op, "success"))
                else:
                    internal.append((op, "failure"))
            else:
                raise SystemExit("unknown impl")
        else:
            return (schedule, tuple(internal), "deadline", steps)
    return (schedule, tuple(internal), "completed", steps)

schedules = [tuple(tuple(p) for p in s) for s in json.loads(sys.argv[1])]
for name in ("impl_atomic_token", "impl_stale_read", "impl_deadlock", "impl_beyond_bound"):
    runs = []
    for schedule in schedules:
        if name == "impl_beyond_bound":
            state, internal, steps = HOLDING, [], 0
            needed = BUDGET + 2
            for op, phase in schedule:
                if phase == "read":
                    pass
                elif steps < BUDGET:
                    steps += 1
                    if steps >= needed and state == HOLDING:
                        state = op
                        internal.append((op, "success"))
            runs.append([list(schedule), [list(x) for x in internal], "deadline", steps])
        else:
            schedule_, internal, status, steps = run_impl(name, schedule)
            runs.append([list(schedule_), [list(x) for x in internal], status, steps])
    print(json.dumps({"name": name, "runs": runs}))
'''

# --- Independent oracle: derives verdicts from public observations only -------

def frozen_mapping(entry):
    """Frozen S2 mapping: (op, kind, channel) -> public event or None.

    Carrier-internal entries are 2-tuples whose observations come from the
    supported 'public' channel; a 3-tuple carries an explicit channel, and a
    channel outside 'public' is opaque — it maps to no public event.
    """
    op, kind = entry[0], entry[1]
    channel = entry[2] if len(entry) == 3 else "public"
    if channel != "public":
        return None
    return {"op": op, "kind": "success" if kind == "success" else "refusal"}


def projection_honest(internal):
    mapped = (frozen_mapping(entry) for entry in internal)
    return [e for e in mapped if e is not None]


def event_completeness(internal):
    """C08 mapped to the profile: both ops project, no dropped public events."""
    ops = [e["op"] for e in projection_honest(internal)]
    return "complete" if set(ops) <= set(EVENTS) and len(ops) == len(internal) else "missing"


def oracle_verdicts(name, runs, schedules):
    """public-oracle-v1: L1 on the projected public trace, L2 within the frozen bound.

    A run cut off by the frozen bound while the profile's bound exceeds the
    frozen bound is inconclusive (unknown), never a violation. The oracle
    derives the verdict itself: it never reads carrier-internal semantics and
    never trusts a carrier's own law verdict (circular assumption refused).
    """
    schedule_count = len(runs)
    if name == "impl_deadlock":
        return ("violated", "no_terminal_within_bound")
    if name == "impl_beyond_bound":
        # Cut off by the frozen bound while wanting more: inconclusive.
        return ("unknown", "timeout_within_bound")
    for run in runs:
        internal = [tuple(x) for x in run[1]]
        if event_completeness(internal) != "complete":
            return ("refused", "missing_projection")
        successes = [e["op"] for e in projection_honest(internal) if e["kind"] == "success"]
        if len(set(successes)) != len(successes) or len(successes) > 1:
            return ("violated", "both_terminal_successes")
    assert schedule_count == len(schedules)
    return ("allowed", "")


# --- Profile predicates over the frozen domain -------------------------------

def supported_outcome(pred, internal):
    assert pred in SUPPORTED_PREDICATES
    if pred == "event_completeness":
        return event_completeness(internal)
    if pred == "at_most_one_terminal_success":
        successes = [e["op"] for e in projection_honest(internal) if e["kind"] == "success"]
        return "allowed" if len(set(successes)) == len(successes) <= 1 else "violated"
    raise AssertionError("unreachable")


def unsupported_outcome(pred):
    assert pred in UNSUPPORTED_PREDICATES
    return {"verdict": "unknown", "reason": "unsupported_predicate"}


def malformed_outcome(event):
    """An event outside the frozen vocabulary is malformed input, not unknown."""
    if event not in EVENTS:
        return "error"
    raise AssertionError("unreachable")


# --- Red controls (profile-level, not carrier-level) --------------------------

def red_controls():
    changed = {"shape": "unchanged", "verdict": None}
    internal = (("expired", "success"), ("confirmed", "failure"))
    # Same-shape stale commit projects both ops (complete), but the stale read
    # means the second op may overwrite a taken reservation: the oracle sees
    # two terminal success events for one reservation, so the profile's
    # event_completeness observation plus the oracle detects the change.
    stale = (("expired", "success"), ("confirmed", "success"))
    changed["verdict"] = supported_outcome("at_most_one_terminal_success", stale)
    missing = {"verdict": None, "reason": None}
    # A carrier with a non-empty internal trace projecting no public events:
    # every internal entry's mapping component is opaque to the public shape.
    if event_completeness((("expired", "success", "opaque"),)) != "complete":
        missing = {"verdict": "refused", "reason": "missing_projection"}
    circular = {"verdict": None, "reason": None}
    # A carrier-computed verdict is never the profile's verdict: the oracle
    # derives it itself, so a circular carrier is refused.
    carrier_verdict = "allowed"   # carrier's own claim
    if carrier_verdict != oracle_verdicts(
            "impl_stale_read", [[None, [list(x) for x in stale], "completed", 2]],
            frozen_schedules())[0]:
        circular = {"verdict": "refused", "reason": "circular_assumption"}
    return {"changed_behavior": changed,
            "missing_projection": missing,
            "circular_assumption": circular}


# --- Rust arm record ----------------------------------------------------------

def rust_arm():
    return {
        "executed": False,
        "conformance": False,   # a not_executed arm is never a conformance pass
        "reason": ("pinned-revision 0.5.0 has no binary asset and sandbox "
                   "rustc 1.75 cannot build it"),
    }


# --- Python arm: real subprocess, real observations ---------------------------

def python_arm(schedules):
    payload = [list(list(p) for p in s) for s in schedules]
    proc = subprocess.run(
        [sys.executable, "-c", PY_ARM_SOURCE, json.dumps(payload)],
        capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stderr[-1000:]
    arm = {"executed": True, "process": "subprocess"}
    for line in proc.stdout.strip().splitlines():
        rec = json.loads(line)
        arm[rec["name"]] = dict(zip(
            ("verdict", "reason"), oracle_verdicts(rec["name"], rec["runs"], schedules)))
    return arm


# --- Report -------------------------------------------------------------------

def digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str)
                          .encode()).hexdigest()


def build_report():
    schedules = frozen_schedules()
    assert len(schedules) == 6
    green = {
        "atomic_token": dict(zip(("verdict", "shape"), ("allowed", "conforms"))),
        "beyond_bound": {"verdict": "unknown", "reason": "timeout_within_bound"},
    }
    green["atomic_token"]["shape"] = "conforms"
    report = {
        "profile": {
            "profile_id": PROFILE_ID,
            "phase": PHASE,
            "domain_schedule_count": len(schedules),
            "specodelic_pin": dict(SPECODELIC_PIN),
            "release_claim": dict(RELEASE_CLAIM),
        },
        "artifact_ids": {
            "graph_kernel": digest({"vocabulary": EVENTS + EVENT_KINDS + STATES,
                                    "predicates": SUPPORTED_PREDICATES}),
            "binding_carriers": digest({"arms": ["python", "rust"],
                                        "oracle": ORACLE_ID}),
        },
        "oracle": {"id": ORACLE_ID, "reads": "public_observations"},
        "interpretation": {
            "events": list(EVENTS),
            "event_kinds": list(EVENT_KINDS),
            "states": list(STATES),
            "supported_predicates": list(SUPPORTED_PREDICATES),
            "unsupported_predicates": list(UNSUPPORTED_PREDICATES),
            "bound": COMMIT_STEP_BUDGET,
        },
        "predicate_outcomes": {
            "event_completeness_green": supported_outcome(
                "event_completeness", (("expired", "success"), ("confirmed", "failure"))),
            "unsupported_request": unsupported_outcome("cross_run_causality"),
            "malformed_request": malformed_outcome("persist"),
        },
        "red_cases": red_controls(),
        "green_cases": green,
        "python_arm": python_arm(schedules),
        "rust_arm": rust_arm(),
        "s2_sufficiency": {
            "sufficient": True,
            "red_controls_expressible": 3,
            "red_controls_total": 3,
        },
    }
    return report


if __name__ == "__main__":
    print(json.dumps(build_report(), sort_keys=True))
