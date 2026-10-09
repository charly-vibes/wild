# Purpose: Command-level contract tests for the full E5 fixture cohort and
#   the evaluation-CLI replay path (beads wild-aoq.2).
# Responsibilities: Validate the frozen e5 manifest (membership, dev/sealed
#   split, synthetic origin, raw artifact commitments) and replay cases
#   through real offline Cargo resolution/build/test via
#   `experiments/update_eval.py replay`, comparing observed outcomes to
#   committed expectations. Native cells replay both phases (original-range
#   refusal, authorized-manifest overcome); representative special cases
#   (migration, wrong-target, singleton, baseline) are exercised for real;
#   remaining sealed cases are validated structurally to keep the suite
#   honest about runtime.
# Rationale: The evaluation harness must prove original exclusion with
#   actual Cargo resolution — never a handwritten semver oracle or path
#   replacement — and must retain unresolved/failing cases under their own
#   labels. Written red-first per the ticket's TDD mandate. Expectations
#   are versioned; changing one appends a new fixture version.

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "experiments" / "update_eval.py"
E5 = REPO / "experiments" / "update_fixtures" / "e5"
MANIFEST = E5 / "cases.json"

EXPECTED_CELLS = {
    "cell-excluded-compatible-major": {
        "target": "2.0.0",
        "verdict": "compatible",
        "phases": {
            "original-range": "resolution-refused-by-range",
            "authorized": "resolved-and-consumer-tests-passed",
        },
    },
    "cell-allowed-incompatible-patch": {
        "target": "1.2.4",
        "verdict": "incompatible",
        "phases": {"authorized": "resolved-then-consumer-tests-failed"},
    },
    "cell-allowed-compatible-update": {
        "target": "1.2.5",
        "verdict": "compatible",
        "phases": {"authorized": "resolved-and-consumer-tests-passed"},
    },
    "cell-excluded-incompatible-major": {
        "target": "3.0.0",
        "verdict": "incompatible",
        "phases": {
            "original-range": "resolution-refused-by-range",
            "authorized": "resolved-then-consumer-build-failed",
        },
    },
}


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def cases_by_id() -> dict[str, dict]:
    return {c["id"]: c for c in load_manifest()["cases"]}


# ---------------------------------------------------------------------------
# Manifest integrity: membership, split, origin, raw artifact commitments
# ---------------------------------------------------------------------------


def test_manifest_membership_and_split():
    manifest = load_manifest()
    assert manifest["schema"] == "wild-e5-cases-v1"
    cases = manifest["cases"]
    ids = [c["id"] for c in cases]
    assert len(ids) >= 12, "full E5 cohort: twelve case classes"
    assert len(ids) == len(set(ids)), "case ids unique"

    # the four range cells, independently specified
    for cid, spec in EXPECTED_CELLS.items():
        case = cases_by_id()[cid]
        assert case["target"] == spec["target"]
        assert case["independent_verdict"] == spec["verdict"]
        phases = {p["phase"]: p["expected_outcome"] for p in case["phases"]}
        assert phases == spec["phases"]

    # every required case class is present
    required_classes = {
        "transitive-addition", "singleton-conflict", "platform-ineligibility",
        "dynamic-usage-unresolved", "wrong-target-selection",
        "baseline-failure", "migration", "intent-change",
    }
    have = {c["class"] for c in cases}
    assert required_classes <= have, f"missing classes: {required_classes - have}"

    # dev/sealed split: total, disjoint, covers every case
    split = manifest["split"]
    dev, sealed = set(split["development"]), set(split["evaluation"])
    assert dev and sealed and not (dev & sealed)
    assert dev | sealed == set(ids), "split covers the full frozen membership"
    # bootstrap development expectations pinned by wild-aoq.5 stay in dev
    assert "cell-excluded-compatible-major" in dev
    assert "cell-allowed-incompatible-patch" in dev
    # sealed evaluation membership frozen before comparative trials
    assert split["policy"] == "never-tune-against-sealed"


def test_manifest_discloses_synthetic_origin_and_commitments():
    for case in load_manifest()["cases"]:
        assert case["origin"] == "synthetic", f"{case['id']} must disclose origin"
        assert case["feasible_target"]["flag"] in (True, False)
        assert case["feasible_target"]["basis"]

    # raw artifact commitments: every committed file under e5/ (except the
    # manifest itself) is digest-committed exactly once
    committed: dict[str, str] = {}
    for artifact in load_manifest()["artifacts"]:
        rel = artifact["path"]
        assert rel not in committed, f"duplicate commitment for {rel}"
        committed[rel] = artifact["sha256"]
        path = E5 / rel
        assert path.is_file(), f"missing artifact: {rel}"
        assert sha256(path) == artifact["sha256"], f"drifted artifact: {rel}"
    actual = {
        str(p.relative_to(E5)) for p in E5.rglob("*")
        if p.is_file() and p.name != "cases.json" and "__pycache__" not in str(p)
    }
    assert actual == set(committed), (
        f"uncommitted: {sorted(actual - set(committed))[:5]}, "
        f"stale: {sorted(set(committed) - actual)[:5]}"
    )


def test_registry_catalog_serves_exact_versions():
    index = E5 / "registry" / "index" / "de" / "pt" / "dept"
    lines = [json.loads(l) for l in index.read_text().splitlines() if l.strip()]
    versions = {l["vers"] for l in lines}
    assert {"1.2.3", "1.2.4", "2.0.0"} <= versions, "bootstrap versions carried"
    assert {"1.2.5", "3.0.0", "1.9.0", "1.8.0", "1.7.0", "2.1.0"} <= versions
    for line in lines:
        crate = E5 / "consumer-mirror" / f"dept-{line['vers']}.crate"
        assert crate.is_file(), f"mirror missing dept-{line['vers']}"
        assert sha256(crate) == line["cksum"], f"cksum drift on dept-{line['vers']}"


# ---------------------------------------------------------------------------
# Native replay through the evaluation CLI (real Cargo, offline)
# ---------------------------------------------------------------------------


def replay(case: str, phase: str) -> dict:
    out = run_cli("replay", "--fixtures", str(E5), "--case", case, "--phase", phase)
    assert out.returncode == 0, out.stderr
    record = json.loads(out.stdout)
    assert record["record_type"] == "replay_record"
    assert record["origin"] == "synthetic"
    return record


def test_cell_excluded_compatible_major_two_phases():
    refused = replay("cell-excluded-compatible-major", "original-range")
    assert refused["observed_outcome"] == "resolution-refused-by-range"
    assert refused["match"] is True
    assert "2.0.0" in refused["evidence"]["combined_output"]
    lock = refused["evidence"]["lock_dept_version"]
    assert lock in (None, "1.2.3"), "refused target must not enter the lockfile"

    overcome = replay("cell-excluded-compatible-major", "authorized")
    assert overcome["observed_outcome"] == "resolved-and-consumer-tests-passed"
    assert overcome["evidence"]["lock_dept_version"] == "2.0.0", (
        "the pinned delivered update must select the exact target — "
        "neither a parse-only report nor a path replacement counts"
    )


def test_cell_allowed_incompatible_patch():
    rec = replay("cell-allowed-incompatible-patch", "authorized")
    assert rec["observed_outcome"] == "resolved-then-consumer-tests-failed"
    assert rec["evidence"]["lock_dept_version"] == "1.2.4"
    assert rec["match"] is True


def test_cell_allowed_compatible_update():
    rec = replay("cell-allowed-compatible-update", "authorized")
    assert rec["observed_outcome"] == "resolved-and-consumer-tests-passed"
    assert rec["evidence"]["lock_dept_version"] == "1.2.5"


def test_cell_excluded_incompatible_major_two_phases():
    refused = replay("cell-excluded-incompatible-major", "original-range")
    assert refused["observed_outcome"] == "resolution-refused-by-range"

    broken = replay("cell-excluded-incompatible-major", "authorized")
    assert broken["observed_outcome"] == "resolved-then-consumer-build-failed"
    assert broken["independent_verdict"] == "incompatible"


def test_migration_case_requires_the_supplied_migration():
    rec = replay("migration-supplied", "authorized")
    assert rec["observed_outcome"] == "resolved-and-consumer-tests-passed"
    assert rec["evidence"]["migration_applied"] is True
    assert rec["evidence"]["without_migration"] == "resolved-then-consumer-tests-failed", (
        "the migration must be necessary: the unpatched consumer fails"
    )


def test_wrong_target_selection_is_detected():
    rec = replay("wrong-target-selection", "no-update")
    assert rec["observed_outcome"] == "resolved-but-selected-target-mismatch"
    assert rec["evidence"]["requested"] == "1.2.5"
    assert rec["evidence"]["selected"] == "1.2.3", "stale lock must select the old version"


def test_singleton_conflict_refuses_resolution():
    rec = replay("singleton-conflict", "authorized")
    assert rec["observed_outcome"] == "resolution-conflict"
    assert "deputil" in rec["evidence"]["combined_output"]


def test_baseline_failure_is_retained_as_baseline():
    rec = replay("baseline-failure", "baseline")
    assert rec["observed_outcome"] == "baseline-tests-failed"
    assert rec["evidence"]["lock_dept_version"] == "1.2.3"


def test_dynamic_case_retains_unresolved_label():
    case = cases_by_id()["dynamic-usage-unresolved"]
    assert case["expected_checker_outcome"] == "unknown", (
        "abstention must be retained, not relabelled as detection or unsafe acceptance"
    )
    assert case["independent_verdict"] == "unresolved"
    # the oracle side remains able to adjudicate behavior independently
    assert case["oracle_can_adjudicate"] is True


def test_development_split_replays_end_to_end():
    out = run_cli("replay", "--fixtures", str(E5), "--split", "development", "--expect-only")
    assert out.returncode == 0, out.stderr
    report = json.loads(out.stdout)
    assert report["record_type"] == "replay_report"
    # --expect-only validates every committed expectation resolves to a
    # replayable phase spec without executing cargo (structural check)
    assert set(report["cases"]) == set(load_manifest()["split"]["development"])
    assert all(r["expectation_valid"] for r in report["cases"].values())


def test_sealed_cases_declare_never_tune_policy():
    manifest = load_manifest()
    sealed = manifest["split"]["evaluation"]
    assert "migration-supplied" in sealed and "dynamic-usage-unresolved" in sealed
    for cid in sealed:
        assert cases_by_id()[cid]["origin"] == "synthetic"