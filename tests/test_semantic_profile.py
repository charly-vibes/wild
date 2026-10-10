# Purpose: Red-first case tests for the bounded Specodelic semantic profile
#   experiment (beads wild-9co.4): map a pinned S2 profile to application
#   observations over the shared frozen two-op reservation domain, separating
#   the graph kernel from opaque binding carriers, with a finite event/state
#   interpretation, supported/unsupported predicate outcomes, and a real
#   Python arm compared to the independently specified public-law oracle.
# Responsibilities: Run experiments/semantic_profile.py as a subprocess and
#   assert the exact frozen expectations for the pinned profile (pinned
#   Specodelic revision recorded, no release-v0.7.0 claim without a pinned
#   audit), kernel/carrier separation (distinct digests, oracle reads public
#   observations only), the finite event/state vocabulary and supported
#   predicate set, unsupported outcomes (well-formed unsupported predicate is
#   unknown/unsupported_predicate, malformed input is error), the red cases
#   (changed behavior detected, missing projection refused, circular
#   assumption refused), the green cases (supported domain preserved: atomic
#   token accepted, C14 beyond-bound stays unknown), the real Python arm
#   (separate process) matching the oracle, the Rust arm recorded as
#   not_executed with the pinned-revision reason, and the S2 sufficiency
#   determination for this frozen domain.
# Rationale: These expectations are the frozen experiment record, not a
#   runtime claim; a mismatch fails the suite so committed scope cannot drift
#   silently. No v1 runtime, unbounded liveness, unrestricted equivalence, or
#   release claim is made: the pinned-audit control asserts the v0.7.0 claim
#   is absent, not granted.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "experiments" / "semantic_profile.py"


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


def test_pinned_profile_and_kernel_carrier_separation():
    report = run_experiment()
    profile = report["profile"]
    assert profile["profile_id"] == "semantic-profile-s2-v1"
    assert profile["phase"] == "P2"
    assert profile["domain_schedule_count"] == 6
    # Pinned Specodelic revision with pinned-audit status.
    pin = profile["specodelic_pin"]
    assert pin["revision"] == "0.5.0"
    assert pin["pinned_audit"] is False
    claim = profile["release_claim"]
    assert claim["v0_7_0"] is False
    assert "pinned-audit-required" in claim["reason"]
    # Kernel and opaque binding carriers are distinct recorded identities.
    ids = report["artifact_ids"]
    assert ids["graph_kernel"] != ids["binding_carriers"]
    # The oracle never reads carrier internals: only public observations.
    assert report["oracle"]["reads"] == "public_observations"
    assert report["oracle"]["id"] == "public-oracle-v1"


def test_finite_event_state_interpretation_and_predicate_outcomes():
    report = run_experiment()
    interp = report["interpretation"]
    assert set(interp["events"]) == {"confirmed", "expired"}
    assert set(interp["event_kinds"]) == {"success", "refusal"}
    assert set(interp["states"]) == {"held", "confirmed", "expired"}
    assert set(interp["supported_predicates"]) == {
        "at_most_one_terminal_success",
        "terminal_within_frozen_bound",
        "event_completeness",
    }
    assert set(interp["unsupported_predicates"]) == {
        "cross_run_causality",
        "state_persistence_across_runs",
    }
    assert interp["bound"] == 8
    outcomes = report["predicate_outcomes"]
    # A supported predicate over the green arm computes a real verdict.
    assert outcomes["event_completeness_green"] == "complete"
    # A well-formed unsupported predicate is unknown, with the reason.
    unsup = outcomes["unsupported_request"]
    assert unsup["verdict"] == "unknown"
    assert unsup["reason"] == "unsupported_predicate"
    # Malformed input (an event outside the frozen vocabulary) is error.
    assert outcomes["malformed_request"] == "error"


def test_red_cases_changed_behavior_missing_projection_circular():
    report = run_experiment()
    red = report["red_cases"]
    # Changed behavior: the stale commit is same-shape but the profile's
    # event-completeness observation plus the oracle detects it.
    assert red["changed_behavior"]["shape"] == "unchanged"
    assert red["changed_behavior"]["verdict"] == "violated"
    # Missing projection: a carrier emitting no public events for a non-empty
    # internal trace is refused, not silently accepted.
    assert red["missing_projection"]["verdict"] == "refused"
    assert red["missing_projection"]["reason"] == "missing_projection"
    # Circular assumption: a carrier that computes its own law verdict is
    # refused; the oracle derives the verdict itself.
    assert red["circular_assumption"]["verdict"] == "refused"
    assert red["circular_assumption"]["reason"] == "circular_assumption"


def test_green_cases_and_real_python_arm_match_oracle():
    report = run_experiment()
    green = report["green_cases"]
    assert green["atomic_token"]["verdict"] == "allowed"
    assert green["atomic_token"]["shape"] == "conforms"
    # C14 preserved: beyond-bound cut by the frozen bound is unknown.
    assert green["beyond_bound"]["verdict"] == "unknown"
    assert green["beyond_bound"]["reason"] == "timeout_within_bound"
    arm = report["python_arm"]
    # Real implementation: a separate process, real observations.
    assert arm["executed"] is True
    assert arm["process"] == "subprocess"
    assert arm["impl_atomic_token"]["verdict"] == "allowed"
    assert arm["impl_stale_read"]["verdict"] == "violated"
    assert arm["impl_deadlock"]["verdict"] == "violated"
    assert arm["impl_beyond_bound"]["verdict"] == "unknown"
    assert arm["impl_deadlock"]["reason"] == "no_terminal_within_bound"
    assert arm["impl_beyond_bound"]["reason"] == "timeout_within_bound"


def test_rust_arm_record_and_s2_sufficiency_determination():
    report = run_experiment()
    rust = report["rust_arm"]
    # Pinned-revision honesty: the Rust arm is recorded not_executed with the
    # pinned-revision reason, and a not_executed arm is never a conformance
    # pass.
    assert rust["executed"] is False
    assert rust["conformance"] is False
    assert "pinned-revision" in rust["reason"]
    det = report["s2_sufficiency"]
    # For this frozen domain the red controls are expressible under S2's
    # supported predicate set, so S2 is sufficient before any S3 refinement.
    assert det["sufficient"] is True
    assert det["red_controls_expressible"] == 3
    assert det["red_controls_total"] == 3
