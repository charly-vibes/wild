# Purpose: Red-first case tests for the semantic-composition replacement
#   experiment (beads wild-9co.2): protected public laws evaluated against
#   valid and faulty replacements in the frozen two-op reservation domain.
# Responsibilities: Run experiments/composition_replacement.py as a
#   subprocess and assert the exact frozen expectations for C01 (same-shape
#   stale commit escapes structure, public oracle detects it), C02 (a second,
#   independently written atomic implementation passes the public oracle
#   across the whole frozen schedule domain), C08 (dishonest projections are
#   rejected by the event-completeness fixture, honest projection accepted),
#   C14 (deadlock fails the bounded progress obligation while safety-only
#   observation would pass; beyond-bound is unknown, not violated), and C16
#   (evidence-domain mismatches are refused; the matching claim is accepted).
# Rationale: These expectations are the frozen experiment record, not a
#   runtime claim; a mismatch fails the suite so committed scope cannot
#   drift silently. No v1 runtime, unbounded liveness, or cross-language
#   conformance is claimed.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "experiments" / "composition_replacement.py"


def run_experiment() -> dict:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        text=True,
        timeout=120,
        cwd=REPO,
    )
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads(proc.stdout)


def test_frozen_scope_and_artifact_identities_are_recorded():
    report = run_experiment()
    scope = report["scope"]
    assert scope["schedules"] == 6          # frozen finite domain
    assert scope["ops"] == ["confirmed", "expired"]
    assert scope["commit_step_budget"] > 0
    assert scope["commit_step_budget"] > 0
    # Artifact identities: every implementation, projection and the oracle
    # carries a recorded digest; the oracle is independently specified.
    ids = report["artifact_ids"]
    assert set(ids) == {
        "public_oracle", "scheduler",
        "impl_atomic_compare", "impl_atomic_token", "impl_stale_read",
        "impl_deadlock", "impl_beyond_bound",
        "projection_honest", "projection_drop_expiration",
        "projection_failure_to_success",
    }
    assert all(len(d) == 64 for d in ids.values())
    assert ids["impl_atomic_compare"] != ids["impl_atomic_token"]
    # Unknowns are recorded explicitly, never zero.
    assert report["unknowns"]


def test_c01_same_shape_race_escapes_structure_and_public_oracle_detects_it():
    report = run_experiment()
    case = report["cases"]["C01_same_shape_race"]
    # Red: the stale-read replacement has the same public shape and passes
    # the structural (same-shape) check.
    assert case["structure_verdict"] == "accepted"
    # The independently specified public oracle flags it: some frozen
    # schedule yields both terminal successes on one reservation.
    assert case["oracle_verdict"] == "violated"
    assert case["violating_schedules"] >= 1
    assert case["total_schedules"] == 6
    # The baseline atomic implementation is not flagged on any schedule.
    assert report["cases"]["C02_valid_internal_replacement"]["baseline_oracle_verdict"] == "allowed"


def test_c02_second_conforming_implementation_passes_public_oracle():
    report = run_experiment()
    case = report["cases"]["C02_valid_internal_replacement"]
    # Independently written token-CAS implementation: same public shape,
    # accepted structurally, allowed by the public oracle on all 6 schedules.
    assert case["structure_verdict"] == "accepted"
    assert case["oracle_verdict"] == "allowed"
    assert case["schedules_checked"] == 6
    # Bound declarations preserved: acceptance is only within the frozen domain.
    assert case["bounded_to"] == scope_schedules(report)


def scope_schedules(report: dict) -> int:
    return report["scope"]["schedules"]


def test_c08_dishonest_projection_rejected_by_event_completeness():
    report = run_experiment()
    case = report["cases"]["C08_dishonest_projection"]
    # Honest projection is event-complete and accepted.
    assert case["projection_honest"]["verdict"] == "accepted"
    assert case["projection_honest"]["empty_trace_pass"] is False
    # Dropping expiration successes is rejected: internal terminal outcomes
    # are missing from the public trace.
    assert case["projection_drop_expiration"]["verdict"] == "rejected"
    assert case["projection_drop_expiration"]["reason"] == "projection_incomplete"
    # Mapping failures into success is rejected too.
    assert case["projection_failure_to_success"]["verdict"] == "rejected"
    assert case["projection_failure_to_success"]["reason"] == "projection_incomplete"


def test_c14_deadlock_fails_bounded_progress_not_safety_only():
    report = run_experiment()
    case = report["cases"]["C14_trace_hiding_divergence"]
    impl = case["deadlock_impl"]
    # Safety-only view: no forbidden public event is emitted, so a
    # safety-only oracle would accept — recorded, not hidden.
    assert impl["safety_only_verdict"] == "allowed"
    # Bounded progress obligation fails within the committed step bound.
    assert impl["oracle_verdict"] == "violated"
    assert impl["reason"] == "no_terminal_within_bound"
    assert impl["budget"] == report["scope"]["commit_step_budget"]
    # An implementation that would terminate after the bound is inconclusive,
    # not a violation: beyond-bound liveness is unknown.
    assert case["beyond_bound_impl"]["oracle_verdict"] == "unknown"
    assert case["beyond_bound_impl"]["reason"] == "timeout_within_bound"


def test_c16_evidence_domain_mismatch_refused():
    report = run_experiment()
    case = report["cases"]["C16_evidence_domain_mismatch"]
    # A matching claim over the full frozen domain with the committed oracle
    # and laws is accepted.
    assert case["matching"]["verdict"] == "accepted"
    # Fewer schedules than the frozen domain: refused, not silently scaled.
    assert case["subdomain"]["verdict"] == "refused"
    assert case["subdomain"]["reason"] == "domain_mismatch"
    # A different oracle identity: refused.
    assert case["foreign_oracle"]["verdict"] == "refused"
    assert case["foreign_oracle"]["reason"] == "oracle_mismatch"
    # Edited obligations (a weakened law set): refused.
    assert case["edited_laws"]["verdict"] == "refused"
    assert case["edited_laws"]["reason"] == "laws_mismatch"