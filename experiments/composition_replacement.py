#!/usr/bin/env python3
"""Purpose: frozen research experiment for the semantic-composition case
    matrix C01/C02/C08/C14/C16 (beads wild-9co.2): evaluate protected public
    laws against valid and faulty replacements in a finite reservation domain.

Responsibilities: freeze an independently specified public-event oracle
    (safety law L1, bounded progress law L2), a finite scheduler over six
    two-op schedules, and a same-shape structure check; run a baseline atomic
    implementation, a second independently written atomic implementation, and
    the stale-read, deadlock, and beyond-bound controls; check event-complete
    projections and evidence-domain claims; and emit one JSON report with
    finite scope, artifact identities, and unknowns.

Rationale: this is an experiment record, not a runtime claim. Structure
    (same shape) accepts the stale-read replacement; the independent public
    oracle detects it while valid replacements pass. Deadlock fails the
    bounded progress obligation where a safety-only view would pass, and
    timeouts beyond the frozen bound are unknown, not violations. No v1
    runtime, unbounded liveness, or cross-language conformance is claimed.
"""
from __future__ import annotations

import hashlib
import inspect
import itertools
import json
from dataclasses import dataclass

# --- Frozen scope -----------------------------------------------------------

OPS = ("confirmed", "expired")
HOLDING = "held"
COMMIT_STEP_BUDGET = 8          # frozen scheduler bound for commit-phase steps
SCHEDULE_BOUND_EXTRA = 2        # beyond-bound control wants more than frozen

LAWS = (
    {"id": "L1", "kind": "safety",
     "statement": "at most one terminal success event per reservation"},
    {"id": "L2", "kind": "progress",
     "statement": "a terminal outcome occurs within the frozen commit step budget"},
)
ORACLE_ID = "public-oracle-v1"

PUBLIC_SHAPE = {
    op: {"request_in": "unit", "success_out": "unit", "refusal_out": "unit"}
    for op in OPS
}


@dataclass(frozen=True)
class Run:
    schedule: tuple
    internal: tuple            # ((op, kind), ...) kind in {"success", "failure"}
    status: str                # "completed" | "deadline"
    steps: int


def frozen_schedules():
    """The finite domain: every interleaving where each op reads before committing."""
    events = [(op, phase) for op in OPS for phase in ("read", "commit")]
    return [p for p in itertools.permutations(events)
            if all(p.index((op, "read")) < p.index((op, "commit")) for op in OPS)]


def digest(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


# --- Implementations (each returns a Run under a step budget) ---------------

def atomic_compare(schedule, budget):
    """Baseline: storage commit rechecks the current state before taking it."""
    state, reads, internal, steps = HOLDING, {}, [], 0
    for op, phase in schedule:
        if phase == "read":
            reads[op] = state
        elif steps < budget:
            steps += 1
            if reads[op] == state == HOLDING:
                state = op
                internal.append((op, "success"))
            else:
                internal.append((op, "failure"))
        else:
            return Run(schedule, tuple(internal), "deadline", steps)
    return Run(schedule, tuple(internal), "completed", steps)


def stale_read(schedule, budget):
    """Faulty replacement: commit trusts the prior read (same public shape)."""
    state, reads, internal, steps = HOLDING, {}, [], 0
    for op, phase in schedule:
        if phase == "read":
            reads[op] = state
        elif steps < budget:
            steps += 1
            if reads[op] == HOLDING:
                state = op
                internal.append((op, "success"))
            else:
                internal.append((op, "failure"))
        else:
            return Run(schedule, tuple(internal), "deadline", steps)
    return Run(schedule, tuple(internal), "completed", steps)


def atomic_token(schedule, budget):
    """Second implementation, independently written: versioned token CAS.

    Shares nothing with atomic_compare except the public event contract.
    """
    version, reads, internal, steps = 0, {}, [], 0
    state = HOLDING
    for op, phase in schedule:
        if phase == "read":
            reads[op] = (state, version)
        elif steps < budget:
            steps += 1
            seen, token = reads[op]
            if token == version and seen == HOLDING:
                version, state = version + 1, op
                internal.append((op, "success"))
            else:
                internal.append((op, "failure"))
        else:
            return Run(schedule, tuple(internal), "deadline", steps)
    return Run(schedule, tuple(internal), "completed", steps)


def deadlock(schedule, budget):
    """C14 control: commit phase spins until the budget is exhausted."""
    state, reads, internal, steps = HOLDING, {}, [], 0
    for op, phase in schedule:
        if phase == "read":
            reads[op] = state
        elif steps < budget:
            steps += 1  # spin: never terminates the commit
    return Run(schedule, tuple(internal), "deadline", steps)


def beyond_bound(schedule, budget):
    """C14 control: would terminate, but needs more steps than the frozen bound."""
    state, reads, internal, steps = HOLDING, {}, [], 0
    needed = budget + SCHEDULE_BOUND_EXTRA
    for op, phase in schedule:
        if phase == "read":
            reads[op] = state
        elif steps < budget:
            steps += 1
            if steps >= needed and reads[op] == HOLDING:
                state = op
                internal.append((op, "success"))
    return Run(schedule, tuple(internal), "deadline", steps)


@dataclass(frozen=True)
class Impl:
    fn: object
    declared_bound: int | None   # commit budget the implementation itself promises


IMPLS = {
    "impl_atomic_compare": Impl(atomic_compare, None),
    "impl_atomic_token": Impl(atomic_token, None),
    "impl_stale_read": Impl(stale_read, None),
    "impl_deadlock": Impl(deadlock, COMMIT_STEP_BUDGET),
    "impl_beyond_bound": Impl(beyond_bound, COMMIT_STEP_BUDGET + SCHEDULE_BOUND_EXTRA),
}


# --- Independently specified public-event oracle ----------------------------

def safety_only_verdict(runs):
    """L1 alone: a safety-only oracle sees no forbidden public event here."""
    for run in runs:
        public = projection_honest(run)
        successes = [e["op"] for e in public if e["kind"] == "success"]
        if len(set(successes)) != len(successes) or len(successes) > 1:
            return "violated"
    return "allowed"


def oracle_verdict(runs, declared_bound):
    """Full oracle: L1 on the projected public trace, L2 within the frozen bound.

    A run cut off by the frozen bound while its own declared bound exceeds the
    frozen bound is inconclusive (unknown), never a violation.
    """
    if any(run.status == "deadline" for run in runs):
        if declared_bound is not None and declared_bound <= COMMIT_STEP_BUDGET:
            return ("violated", "no_terminal_within_bound")
        return ("unknown", "timeout_within_bound")
    verdict = safety_only_verdict(runs)
    return (verdict, "" if verdict == "allowed" else "both_terminal_successes")


# --- Projections (internal outcomes -> public events) ------------------------

def projection_honest(run):
    return [{"op": op, "kind": "success" if kind == "success" else "refusal"}
            for op, kind in run.internal]


def projection_drop_expiration(run):
    return [e for e in projection_honest(run)
            if not (e["op"] == "expired" and e["kind"] == "success")]


def projection_failure_to_success(run):
    return [{"op": op, "kind": "success"} for op, _ in run.internal]


def completeness_check(run, public_events):
    """Event-completeness fixture: public trace must mirror internal terminals."""
    if not public_events and run.internal:
        return ("rejected", "projection_incomplete")   # no empty-trace pass
    if [e["op"] for e in public_events if e["kind"] == "success"] != \
       [op for op, k in run.internal if k == "success"]:
        return ("rejected", "projection_incomplete")
    if [e["op"] for e in public_events if e["kind"] == "refusal"] != \
       [op for op, k in run.internal if k == "failure"]:
        return ("rejected", "projection_incomplete")
    return ("accepted", "")


# --- Structure check and evidence-domain claims ------------------------------

def structure_check(candidate_shape):
    """Same-shape structural check (the tier that the stale replacement escapes)."""
    if candidate_shape != PUBLIC_SHAPE:
        return "rejected"
    return "accepted"


def frozen_laws_digest():
    return digest(LAWS)


def check_claim(claim):
    """C16: evidence must cover the full frozen domain with the committed oracle."""
    domain = {tuple(s) for s in frozen_schedules()}
    if {tuple(s) for s in claim["domain"]} != domain:
        return ("refused", "domain_mismatch")
    if claim["oracle_id"] != ORACLE_ID:
        return ("refused", "oracle_mismatch")
    if claim["laws_digest"] != frozen_laws_digest():
        return ("refused", "laws_mismatch")
    return ("accepted", "")


# --- Experiment --------------------------------------------------------------

def run_impl(name):
    impl = IMPLS[name]
    return [impl.fn(schedule, COMMIT_STEP_BUDGET) for schedule in frozen_schedules()]


def main():
    schedules = frozen_schedules()
    assert len(schedules) == 6

    stale_runs = run_impl("impl_stale_read")
    stale_verdict, _ = oracle_verdict(stale_runs, IMPLS["impl_stale_read"].declared_bound)
    stale_violations = sum(
        1 for run in stale_runs if safety_only_verdict([run]) == "violated")

    token_runs = run_impl("impl_atomic_token")
    token_verdict, _ = oracle_verdict(token_runs, IMPLS["impl_atomic_token"].declared_bound)
    baseline_runs = run_impl("impl_atomic_compare")
    baseline_verdict, _ = oracle_verdict(baseline_runs, IMPLS["impl_atomic_compare"].declared_bound)

    deadlock_runs = run_impl("impl_deadlock")
    beyond_runs = run_impl("impl_beyond_bound")

    projections = {}
    for name, fn in (("projection_honest", projection_honest),
                     ("projection_drop_expiration", projection_drop_expiration),
                     ("projection_failure_to_success", projection_failure_to_success)):
        checks = [completeness_check(run, fn(run)) for run in baseline_runs]
        verdict = "accepted" if all(c[0] == "accepted" for c in checks) else "rejected"
        reasons = {c[1] for c in checks if c[1]}
        projections[name] = {
            "verdict": verdict,
            "reason": reasons.pop() if reasons else "",
            "empty_trace_pass": any(
                not fn(run) and run.internal for run in baseline_runs),
        }

    claims = {
        "matching": {"domain": [list(s) for s in schedules],
                     "oracle_id": ORACLE_ID,
                     "laws_digest": frozen_laws_digest()},
        "subdomain": {"domain": [list(s) for s in schedules[:4]],
                      "oracle_id": ORACLE_ID,
                      "laws_digest": frozen_laws_digest()},
        "foreign_oracle": {"domain": [list(s) for s in schedules],
                           "oracle_id": ORACLE_ID + "-elsewhere",
                           "laws_digest": frozen_laws_digest()},
        "edited_laws": {"domain": [list(s) for s in schedules],
                        "oracle_id": ORACLE_ID,
                        "laws_digest": digest(LAWS[:1])},
    }

    report = {
        "scope": {
            "ops": list(OPS),
            "schedules": len(schedules),
            "commit_step_budget": COMMIT_STEP_BUDGET,
            "oracle_id": ORACLE_ID,
            "laws": list(LAWS),
            "laws_digest": frozen_laws_digest(),
            "claim": "finite frozen domain only; no v1 runtime, unbounded "
                     "liveness, or cross-language conformance",
        },
        "artifact_ids": {
            "public_oracle": digest([inspect.getsource(oracle_verdict),
                                     inspect.getsource(safety_only_verdict)]),
            "scheduler": digest([inspect.getsource(frozen_schedules),
                                 COMMIT_STEP_BUDGET]),
            **{name: digest(inspect.getsource(impl.fn))
               for name, impl in IMPLS.items()},
            "projection_honest": digest(inspect.getsource(projection_honest)),
            "projection_drop_expiration": digest(
                inspect.getsource(projection_drop_expiration)),
            "projection_failure_to_success": digest(
                inspect.getsource(projection_failure_to_success)),
        },
        "unknowns": [
            "schedules outside the frozen six are unobserved; acceptance is "
            "bounded to the frozen domain, not an equivalence proof",
            "whether the beyond-bound implementation completes past the frozen "
            "bound is outside protocol scope (unknown, not violated)",
            "wall-clock timings are excluded as evidence; repeated timings are "
            "not independent observations",
            "deadlock is modeled as a spinning commit, not real threads",
        ],
        "cases": {
            "C01_same_shape_race": {
                "structure_verdict": structure_check(PUBLIC_SHAPE),
                "oracle_verdict": stale_verdict,
                "violating_schedules": stale_violations,
                "total_schedules": len(schedules),
            },
            "C02_valid_internal_replacement": {
                "structure_verdict": structure_check(PUBLIC_SHAPE),
                "oracle_verdict": token_verdict,
                "schedules_checked": len(token_runs),
                "bounded_to": len(schedules),
                "baseline_oracle_verdict": baseline_verdict,
            },
            "C08_dishonest_projection": projections,
            "C14_trace_hiding_divergence": {
                "deadlock_impl": {
                    "safety_only_verdict": safety_only_verdict(deadlock_runs),
                    "oracle_verdict": oracle_verdict(
                        deadlock_runs, IMPLS["impl_deadlock"].declared_bound)[0],
                    "reason": oracle_verdict(
                        deadlock_runs, IMPLS["impl_deadlock"].declared_bound)[1],
                    "budget": COMMIT_STEP_BUDGET,
                    "declared_bound": IMPLS["impl_deadlock"].declared_bound,
                },
                "beyond_bound_impl": {
                    "oracle_verdict": oracle_verdict(
                        beyond_runs, IMPLS["impl_beyond_bound"].declared_bound)[0],
                    "reason": oracle_verdict(
                        beyond_runs, IMPLS["impl_beyond_bound"].declared_bound)[1],
                    "budget": COMMIT_STEP_BUDGET,
                    "declared_bound": IMPLS["impl_beyond_bound"].declared_bound,
                },
            },
            "C16_evidence_domain_mismatch": {
                name: dict(zip(("verdict", "reason"), check_claim(claim)))
                for name, claim in claims.items()
            },
        },
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()