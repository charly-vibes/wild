# Purpose: Red-first case tests for the semantic-composition composite
#   boundary experiment (beads wild-9co.3): identity and flattening across
#   H0 flat, H1 authored wrapper and H2 first-class composite under
#   protocol revision 2.
# Responsibilities: Run experiments/composite_boundary.py as a subprocess
#   and assert the exact frozen expectations for C03 (demanded export
#   removal refused, unused export removal compatibly scoped), C04 (an
#   unbound hidden dependency is refused in every arm), C05 (shared
#   singleton identity accepted, distinct instances refused even with
#   equal contracts), C06 (a cross-boundary relation with a hidden endpoint
#   is refused), C07 (changed bytes refuse stale evidence, unchanged
#   inputs may reuse), C09a-e (renaming equivalence, empty identity, cyclic
#   closure with once-only traversal, invalid mappings are input errors,
#   grouping associativity), C10 (incomplete bundle refused), C11 (revoked
#   authority refuses old acceptance while structure is preserved), C16
#   (evidence-domain mismatches refused), plus representation equivalence
#   of the three arms under the one shared oracle.
# Rationale: These expectations are the frozen experiment record, not a
#   runtime claim; a mismatch fails the suite so committed scope cannot
#   drift silently. No v1 runtime, unbounded liveness, cross-language
#   conformance, or category-theoretic proof is claimed.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPT = REPO / "experiments" / "composite_boundary.py"
ARMS = ["H0", "H1", "H2"]


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
    assert scope["arms"] == ARMS
    assert scope["protocol_revision"] == 2
    assert scope["oracle_id"] == "closure-oracle-v1"
    assert scope["traversal_bound"] > 0
    assert scope["shared_singleton_key"] == "storage_shared"
    # Artifact identities: every checker and representation encoding
    # carries a recorded digest.
    ids = report["artifact_ids"]
    assert set(ids) == {
        "closure_oracle", "canonicalizer", "evidence_checker",
        "bundle_checker", "h0_flat", "h1_wrapper", "h2_composite",
    }
    assert all(len(d) == 64 for d in ids.values())
    # Unknowns are recorded explicitly, never zero.
    assert report["unknowns"] and all(isinstance(u, str) and u
                                      for u in report["unknowns"])


def test_representation_equivalence_across_arms():
    report = run_experiment()
    eq = report["representation_equivalence"]
    assert eq["equal_across_arms"] is True
    assert len(set(eq["canonical_digests"].values())) == 1
    assert all(v == "accepted" for v in eq["verdicts"].values())


def test_C03_used_vs_unused_output_removal():
    cases = run_experiment()["cases"]["C03_used_vs_unused_output_removal"]
    for arm in ARMS:
        demanded = cases["demanded_removal"][arm]
        assert demanded["verdict"] == "error", (arm, demanded)
        assert any(r.startswith("dangling_endpoint")
                   for r in demanded["reasons"]), (arm, demanded)
        unused = cases["unused_removal"][arm]
        assert unused["verdict"] == "accepted", (arm, unused)
        assert unused["demands_complete"] is True
        assert unused["unused_export_dropped"] is True


def test_C04_hidden_dependency_refused_in_every_arm():
    cases = run_experiment()["cases"]["C04_hidden_dependency"]
    for arm in ARMS:
        rec = cases[arm]
        assert rec["verdict"] == "error", (arm, rec)
        assert any(r.startswith("unbound_input") for r in rec["reasons"])


def test_C05_shared_singleton_identity():
    cases = run_experiment()["cases"]["C05_shared_singleton"]
    for arm in ARMS:
        shared = cases["shared_identity"][arm]
        assert shared["verdict"] == "accepted", (arm, shared)
        assert shared["singleton_instance_count"] == 1
        assert shared["consumers_bound"] == 1
        control = cases["distinct_control"][arm]
        assert control["verdict"] in ("refused", "error"), (arm, control)
        assert any("conflicting_singleton" in r for r in control["reasons"])
    eq = cases["equal_contracts_distinct_instances"]["H1"]
    assert eq["contracts_equal"] is True
    assert eq["verdict"] in ("refused", "error")
    assert any("conflicting_singleton" in r for r in eq["reasons"])


def test_C06_cross_boundary_relation():
    cases = run_experiment()["cases"]["C06_cross_boundary_relation"]
    for arm in ARMS:
        assert cases["honest"][arm]["verdict"] == "accepted", (arm, cases)
    hidden = cases["endpoint_hidden"]["H1"]
    assert hidden["verdict"] == "refused", hidden
    assert any(r.startswith("relation_endpoint_missing")
               for r in hidden["reasons"])
    for arm in ("H0", "H2"):
        assert cases["endpoint_hidden"][arm]["verdict"] == "not_applicable"


def test_C07_same_contract_new_bytes():
    cases = run_experiment()["cases"]["C07_same_contract_new_bytes"]
    assert cases["unchanged_reuse"] == ["accepted", ""]
    assert cases["changed_artifact_stale"] == ["refused", "stale_evidence"]
    assert cases["changed_artifact_fresh_run"] == ["accepted", ""]


def test_C09a_renaming_equivalence():
    cases = run_experiment()["cases"]["C09a_renaming_equivalence"]
    for arm in ARMS:
        rec = cases[arm]
        assert rec["equal"] is True, (arm, rec)
        assert rec["verdict"] == "accepted"
        assert rec["base_digest"] == rec["renamed_digest"]


def test_C09b_empty_identity():
    cases = run_experiment()["cases"]["C09b_empty_identity"]
    for arm in ARMS:
        for side in ("left_identity", "right_identity"):
            rec = cases[side][arm]
            assert rec["verdict"] == "accepted", (arm, side, rec)
            assert rec["identity_preserved"] is True
    empty = cases["empty_alone"]
    assert empty["structure"] == "pass_declared"
    assert empty["coverage_instances"] == 0
    assert empty["coverage_bindings"] == 0
    assert empty["ratio"] is None
    assert empty["verdict"] == "accepted"


def test_C09c_cyclic_closure():
    cases = run_experiment()["cases"]["C09c_cyclic_closure"]
    for arm in ARMS:
        rec = cases[arm]
        assert rec["verdict"] == "accepted", (arm, rec)
        assert rec["visited_once"] is True
        assert rec["traversed"] == 2


def test_C09d_invalid_mapping():
    cases = run_experiment()["cases"]["C09d_invalid_mapping"]
    for arm in ARMS:
        coll = cases["collision"][arm]
        assert coll["verdict"] == "error", (arm, coll)
        assert any(r.startswith("instance_collision")
                   for r in coll["reasons"])
        dang = cases["unresolved_endpoint"][arm]
        assert dang["verdict"] == "error", (arm, dang)
        assert any(r.startswith("dangling_endpoint")
                   for r in dang["reasons"])
        control = cases["valid_control"][arm]
        assert control["verdict"] == "accepted"


def test_C09e_grouping_associativity():
    cases = run_experiment()["cases"]["C09e_grouping_associativity"]
    assert cases["equal_closure"] is True
    assert cases["same_verdict"] is True
    assert cases["grouping_left"]["verdict"] == "accepted"
    assert cases["grouping_right"]["verdict"] == "accepted"
    assert (cases["grouping_left"]["closure_digest"] ==
            cases["grouping_right"]["closure_digest"])


def test_C10_incomplete_bundle():
    cases = run_experiment()["cases"]["C10_incomplete_bundle"]
    assert cases["intact_bundle"] == ["accepted", ""]
    assert cases["missing_impl_blob"] == ["refused",
                                          "missing_artifact_blob:store"]
    assert cases["missing_oracle_fixture"] == ["refused",
                                               "missing_oracle_fixture"]


def test_C11_stale_authority():
    cases = run_experiment()["cases"]["C11_stale_authority"]
    assert cases["structure_verdict_preserved"] == "accepted"
    assert cases["current_authority"] == ["accepted", ""]
    assert cases["old_acceptance_reuse"] == ["refused", "authority_revoked"]


def test_C16_evidence_domain_mismatch():
    cases = run_experiment()["cases"]["C16_evidence_domain_mismatch"]
    assert cases["matching"] == ["accepted", ""]
    assert cases["subdomain"] == ["refused", "domain_mismatch"]
    assert cases["foreign_oracle"] == ["refused", "oracle_mismatch"]
    assert cases["edited_laws"] == ["refused", "laws_mismatch"]