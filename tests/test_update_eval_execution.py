# Purpose: Command-level contract tests for the four-arm execution slice
#   (beads wild-aoq.3): equal authority across A-D, protected grading outside
#   candidate control, accepted-check deletion protection, and retention of
#   unknown treatment outcomes beside the independently adjudicated oracle.
# Responsibilities: Run the real `execute` CLI against the committed
#   arm-trial fixture (real Cargo, offline local registry) and assert the
#   wild-evaluate scenarios — baseline attempts the same major update, the
#   candidate workspace never contains the hidden oracle, deleting an
#   accepted check yields a policy rejection in every arm, and dynamic-usage
#   abstentions stay unknown through attempt, grade and summary.
# Rationale: The slice's observable workflow is comparative execution with
#   honest outcomes; expectations pin spec scenarios, not implementation
#   mirrors. Written red-first per the ticket's TDD mandate.

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "experiments" / "update_eval.py"
FIXTURE = REPO / "experiments" / "update_fixtures" / "arm-trial"
ALL_ARMS = ["A", "B", "C", "D"]
MAJOR_TASK = "out-of-range-major"
DYNAMIC_TASK = "dynamic-usage"
DELETION_TASK = "accepted-check-deletion"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


@pytest.fixture(scope="module")
def executed(tmp_path_factory: pytest.TempPathFactory) -> dict:
    out = tmp_path_factory.mktemp("arm-run")
    proc = run_cli("execute", "--protocol", str(FIXTURE / "study.json"),
                   "--output", str(out))
    assert proc.returncode == 0, proc.stderr
    records = {}
    for path in sorted(out.glob("*.json")):
        records[path.name] = json.loads(path.read_text())
    return {"dir": out, "records": records, "stderr": proc.stderr}


def record_for(executed: dict, task: str, arm: str) -> dict:
    return executed["records"][f"{task}.{arm}.t1.json"]


def test_all_twelve_arm_trial_records_exist_and_validate(executed: dict) -> None:
    for task in (MAJOR_TASK, DYNAMIC_TASK, DELETION_TASK):
        for arm in ALL_ARMS:
            rec = record_for(executed, task, arm)
            assert rec["record_type"] == "task_result"
            assert rec["task_id"] == task and rec["arm"] == arm and rec["trial"] == 1
    v = run_cli("validate", "--protocol", str(FIXTURE / "study.json"),
                "--runs", str(executed["dir"]))
    assert v.returncode == 0, v.stderr


def test_arms_share_authority_budgets_and_only_feedback_differs(executed: dict) -> None:
    major = {arm: record_for(executed, MAJOR_TASK, arm) for arm in ALL_ARMS}
    for arm, rec in major.items():
        commit = rec["attempts"][0]["input_commitments"]
        # Same frozen target catalog, environment and authority for every arm.
        assert commit["target"] == "dept 2.0.0"
        assert commit["authority"] == {"manifest_edit": True}
        assert commit["budget"] == {"timeout_seconds": 600, "max_attempts": 3}
    feedback = {arm: major[arm]["attempts"][0]["input_commitments"]["feedback"]
                for arm in ALL_ARMS}
    assert feedback == {"A": "none", "B": "mined", "C": "authored", "D": "both"}


def test_realized_order_is_recorded_and_covers_all_assignments(executed: dict) -> None:
    manifest = executed["records"]["run_manifest.json"]
    order = manifest["realized_order"]
    assert len(order) == 12
    keys = {(o.split("/")[0], o.split("/")[1]) for o in order}
    assert keys == {(task, arm) for task in
                    (MAJOR_TASK, DYNAMIC_TASK, DELETION_TASK) for arm in ALL_ARMS}
    # A fixed seed must produce the recorded order deterministically.
    assert manifest["execution_seed"] == 7


def test_baseline_attempts_same_major_update(executed: dict) -> None:
    a = record_for(executed, MAJOR_TASK, "A")
    d = record_for(executed, MAJOR_TASK, "D")
    for rec in (a, d):
        attempt = rec["attempts"][0]
        evidence = attempt["closure"]
        # Real Cargo refused the exact target under the original range, then
        # the same authorized manifest edit overcame it through the shared
        # host path — for the baseline arm exactly as for the full-feedback arm.
        assert evidence["original_range_attempt"] == "resolution-refused-by-range"
        assert evidence["authorized_resolution"] == "resolved"
        assert rec["terminal_disposition"] == "delivered"
        assert rec["delivered"]["independently_valid"] is True
    assert a["delivered"]["attempt_id"] != d["delivered"]["attempt_id"]


def test_candidate_cannot_read_its_oracle(executed: dict) -> None:
    for name, rec in executed["records"].items():
        if name == "run_manifest.json":
            continue
        inventory = rec["attempts"][0]["closure"]["workspace_inventory"]
        # The workspace the candidate acted in never contained the hidden
        # acceptance suite or any oracle artifact.
        assert not any("oracle" in p for p in inventory), (name, inventory)
        assert not any(p.startswith("tests/") and "accepted_check" not in p
                       for p in inventory), (name, inventory)
        oracle = rec["oracle_results"][0]
        # The oracle graded the actual artifact from outside the workspace.
        assert oracle["grader"]["id"] == "independent-oracle"
        assert oracle["graded_artifact"]["digest"] == \
            rec["attempts"][0]["requested_artifact"]["digest"]


def test_deleted_accepted_check_does_not_disappear(executed: dict) -> None:
    for arm in ALL_ARMS:
        rec = record_for(executed, DELETION_TASK, arm)
        attempt = rec["attempts"][0]
        assert attempt["checker_outcome"] == "reject"
        assert attempt["checker_reason"].startswith("policy:")
        assert attempt["closure"]["accepted_check_deleted_from_workspace"] is True
        # The host re-enforced the original check from its protected copy.
        assert attempt["closure"]["protected_accepted_check_enforced"] is True
        assert rec["delivered"] is None
        assert rec["terminal_disposition"] == "failed"
        # The policy refusal stays distinguishable from a compatibility reject.
        assert "compatibility" not in attempt["checker_reason"]


def test_dynamic_usage_unknown_retained_beside_oracle(executed: dict) -> None:
    s = run_cli("summarize", "--protocol", str(FIXTURE / "study.json"),
                "--runs", str(executed["dir"]))
    assert s.returncode == 0, s.stderr
    summary = json.loads(s.stdout)
    for arm in ALL_ARMS:
        rec = record_for(executed, DYNAMIC_TASK, arm)
        attempt = rec["attempts"][0]
        # The treatment abstained on the unresolved dynamic fixture.
        assert attempt["checker_outcome"] == "unknown"
        assert attempt["checker_reason"] == "dynamic-usage"
        # The independent oracle adjudicated the same artifact compatible;
        # both outcomes stay stored side by side without relabelling.
        oracle = rec["oracle_results"][0]
        assert oracle["verdict"] == "compatible"
        assert rec["delivered"]["independently_valid"] is True
        assert attempt["checker_outcome"] == "unknown"
    # The summary retains the unknown outcomes in their own category instead
    # of counting them as detection or unsafe acceptance.
    cm = summary["candidate_metrics"]
    assert cm["unknown_rate"]["num"] == 4
    assert cm["unknown_rate"]["den"] == 12
    assert cm["confusion"]["unsafe_acceptance"]["num"] == 0
    assert cm["confusion"]["unsafe_acceptance"]["den"] == 4
