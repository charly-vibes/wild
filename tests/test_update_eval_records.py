# Purpose: Command-level contract tests for the evaluation record slice
#   (beads wild-aoq.1): record validation, confirmatory gate, and exact
#   denominator summaries for experiments/update_eval.py.
# Responsibilities: Exercise the real CLI as a subprocess against committed
#   metric fixtures (six-candidate confusion table, ineligible/unresolved
#   visibility) and constructed records in tempdirs (zero-delivery null
#   ratio, multi-attempt completion, artifact mismatch, duplicate ids, cost
#   honesty, missing margins). Assert the exact spec numbers, not
#   implementation mirrors.
# Rationale: The harness's first acceptance is a working measurement
#   pipeline whose summaries never inflate successes or hide failed effort.
#   Written red-first per the ticket's TDD mandate; expectations pin the
#   design.md aggregation example and the six wild-evaluate scenarios owned
#   by wild-aoq.1. Changing an expectation appends a fixture version, it
#   does not rewrite committed fixture history.

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "experiments" / "update_eval.py"
FIXTURE_ROOT = REPO / "experiments" / "update_fixtures" / "metric-example"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def digest(seed: str) -> str:
    return "sha256:" + hashlib.sha256(seed.encode()).hexdigest()


def write_json(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


def make_protocol(mode: str = "fixture", n_tasks: int = 1) -> dict:
    return {
        "schema_version": 1,
        "record_type": "protocol",
        "protocol_id": "study-test",
        "mode": mode,
        "split": {"development": ["t1"], "evaluation": []},
        "environment": {"cargo": "1.85.0"},
        "arms": [
            {
                "id": "A",
                "adapter": "existing-tool",
                "outcome_mapping": {"accept": "accept"},
            }
        ],
        "budgets": {"timeout_seconds": 600, "max_attempts": 3},
        "authority": {"manifest_edit": True},
        "cold_warm_policy": "cold",
        "tasks": [make_task(f"t{i + 1}") for i in range(n_tasks)],
    }


def make_task(task_id: str) -> dict:
    return {
        "record_type": "task",
        "task_id": task_id,
        "origin": "synthetic",
        "consumer_digest": digest(f"consumer-{task_id}"),
        "base_digest": digest(f"base-{task_id}"),
        "exact_target": "serde 1.0.200",
        "original_range": ">=1.0.100, <1.1.0",
        "stratum": "direct",
        "feasible_target": {"flag": True, "basis": "registry has release"},
        "non_compatibility_constraints": [],
        "tags": [],
        "oracle_commitment": {
            "domain": "crate:serde",
            "tests_digest": digest(f"oracle-{task_id}"),
        },
    }


def make_attempt(attempt_id: str, *, outcome: str = "accept", minutes: float = 5.0) -> dict:
    cost = {"human_minutes": {"basis": "measured", "value": minutes},
            "compute_cost_usd": {"basis": "unavailable"},
            "wall_time_minutes": {"basis": "measured", "value": minutes}}
    rec = {
        "record_type": "attempt",
        "attempt_id": attempt_id,
        "input_commitments": {"manifest": digest(f"manifest-{attempt_id}")},
        "requested_artifact": {"digest": digest(f"artifact-{attempt_id}")},
        "checker_outcome": outcome,
        "checker_reason": "compatibility" if outcome == "reject" else "none",
        "exit": {"kind": "ok"},
        "costs": cost,
    }
    return rec


def make_oracle(attempt_id: str, verdict: str, *, eligible: bool = True, reasons: list | None = None) -> dict:
    return {
        "record_type": "oracle_result",
        "attempt_id": attempt_id,
        "graded_artifact": {"digest": digest(f"artifact-{attempt_id}")},
        "verdict": verdict,
        "domain": "crate:serde",
        "eligibility": {"eligible": eligible, "reasons": reasons or []},
        "grader": {"id": "grader-1"},
        "adjudication_history": [],
    }


def make_task_result(task_id: str, attempts: list, oracles: list, delivered: dict | None = None) -> dict:
    return {
        "schema_version": 1,
        "record_type": "task_result",
        "task_id": task_id,
        "arm": "A",
        "trial": 1,
        "attempts": attempts,
        "oracle_results": oracles,
        "delivered": delivered,
        "terminal_disposition": "delivered" if delivered else "failed",
    }


def write_run(tmp: Path, name: str, result: dict) -> Path:
    return write_json(tmp / "results" / f"{name}.json", result)


# ---------------------------------------------------------------------------
# Committed metric fixtures (experiments/update_fixtures/metric-example/)
# ---------------------------------------------------------------------------


def summarize_fixture(rel: str) -> tuple[dict, subprocess.CompletedProcess[str]]:
    """Validate + summarize a committed metric fixture via the real CLI."""
    proto = FIXTURE_ROOT / rel / "study.json"
    results = FIXTURE_ROOT / rel / "results"
    ok = run_cli("validate", "--protocol", str(proto))
    assert ok.returncode == 0, ok.stderr
    out = run_cli("summarize", "--protocol", str(proto), "--runs", str(results))
    assert out.returncode == 0, out.stderr
    return json.loads(out.stdout), out


def test_six_candidate_confusion_table():
    """Spec: six-candidate confusion table — exact rates from design.md."""
    summary, _ = summarize_fixture("six-candidate")

    cm = summary["candidate_metrics"]
    assert cm["assigned"] == 6
    conf = cm["confusion"]
    assert conf["unsafe_acceptance"]["num"] == 1 and conf["unsafe_acceptance"]["den"] == 3
    assert conf["detection_recall"]["num"] == 1 and conf["detection_recall"]["den"] == 3
    assert conf["false_negative_rate"]["num"] == 1 and conf["false_negative_rate"]["den"] == 3
    assert conf["false_block_rate"]["num"] == 0 and conf["false_block_rate"]["den"] == 3


def test_six_candidate_unknown_error_and_coverage():
    """Unknown/error stay in assigned counts; coverage covers adjudication."""
    summary, _ = summarize_fixture("six-candidate")

    cm = summary["candidate_metrics"]
    assert cm["unknown_rate"]["num"] == 1 and cm["unknown_rate"]["den"] == 6
    assert cm["error_rate"]["num"] == 1 and cm["error_rate"]["den"] == 6
    assert cm["oracle_coverage"]["num"] == 6 and cm["oracle_coverage"]["den"] == 6


def test_six_candidate_zero_deliveries_yield_null_ratio():
    """No deliveries in the cohort: null ratio with a named reason."""
    summary, _ = summarize_fixture("six-candidate")

    tm = summary["task_metrics"]
    assert tm["completed"] == 0
    ratio = tm["cost_per_valid_update"]
    assert ratio["value"] is None
    assert ratio["reason"] == "zero-deliveries"
    assert ratio["num"] == 0 and ratio["den"] == 0


def test_ineligible_and_unresolved_remain_visible():
    """Spec: ineligible and unresolved cases remain visible — outside binary
    rates, inside assigned counts, never validated completion."""
    proto = FIXTURE_ROOT / "extended" / "study.json"
    results = FIXTURE_ROOT / "extended" / "results"

    out = run_cli("summarize", "--protocol", str(proto), "--runs", str(results))
    assert out.returncode == 0, out.stderr
    summary = json.loads(out.stdout)

    cm = summary["candidate_metrics"]
    # binary table unchanged by the two added cases
    conf = cm["confusion"]
    assert conf["unsafe_acceptance"]["num"] == 1 and conf["unsafe_acceptance"]["den"] == 3
    assert conf["detection_recall"]["num"] == 1 and conf["detection_recall"]["den"] == 3
    assert conf["false_negative_rate"]["num"] == 1 and conf["false_negative_rate"]["den"] == 3
    assert conf["false_block_rate"]["num"] == 0 and conf["false_block_rate"]["den"] == 3
    # but they remain in assigned counts and their own categories
    assert cm["assigned"] == 8
    assert cm["excluded"]["policy_ineligible"]["count"] == 1
    assert cm["excluded"]["oracle_unresolved"]["count"] == 1
    assert cm["accepted_oracle_unresolved"] == 1
    # accepted-but-unresolved never counts as independently validated completion;
    # same for the policy-prohibited delivered candidate.
    tm = summary["task_metrics"]
    assert tm["completed"] == 1
    assert tm["delivered_but_not_validated"] == 2


# ---------------------------------------------------------------------------
# Constructed records in tempdirs
# ---------------------------------------------------------------------------


def test_no_delivered_update(tmp_path: Path):
    """Spec: no delivered update — null ratio, failed effort retained."""
    proto = write_json(tmp_path / "study.json", make_protocol(n_tasks=3))
    for i in (1, 2, 3):
        att = make_attempt(f"t{i}-A-1-a1", outcome="reject", minutes=7.0)
        orc = make_oracle(f"t{i}-A-1-a1", "incompatible")
        write_run(tmp_path, f"t{i}", make_task_result(f"t{i}", [att], [orc]))

    out = run_cli("summarize", "--protocol", str(proto), "--runs", str(tmp_path / "results"))
    assert out.returncode == 0, out.stderr
    tm = json.loads(out.stdout)["task_metrics"]
    assert tm["completed"] == 0
    ratio = tm["cost_per_valid_update"]
    assert ratio["value"] is None and ratio["reason"] == "zero-deliveries"
    # total failed effort stays visible, not folded into a fake zero
    assert tm["effort"]["human_minutes"]["measured"] == 21.0
    assert tm["effort_failed_attempts"]["human_minutes"]["measured"] == 21.0


def test_multiple_attempts_do_not_inflate_completion(tmp_path: Path):
    """Spec: one task, three attempts, one valid delivery — one completion,
    all three attempts charged to effort."""
    proto = write_json(tmp_path / "study.json", make_protocol(n_tasks=1))
    attempts = [
        make_attempt("t1-A-1-a1", outcome="reject", minutes=4.0),
        make_attempt("t1-A-1-a2", outcome="error", minutes=3.0),
        make_attempt("t1-A-1-a3", outcome="accept", minutes=6.0),
    ]
    oracles = [
        make_oracle("t1-A-1-a1", "incompatible"),
        make_oracle("t1-A-1-a2", "compatible"),
        make_oracle("t1-A-1-a3", "compatible"),
    ]
    delivered = {"attempt_id": "t1-A-1-a3", "independently_valid": True}
    write_run(tmp_path, "t1", make_task_result("t1", attempts, oracles, delivered))

    out = run_cli("summarize", "--protocol", str(proto), "--runs", str(tmp_path / "results"))
    assert out.returncode == 0, out.stderr
    tm = json.loads(out.stdout)["task_metrics"]
    assert tm["completed"] == 1
    assert tm["assigned_tasks"] == 1
    assert tm["delivered_attempts"] == 1
    assert tm["attempts_total"] == 3
    assert tm["effort"]["human_minutes"]["measured"] == 13.0
    assert tm["cost_per_valid_update"]["num"] == 13.0 and tm["cost_per_valid_update"]["den"] == 1


def test_requested_and_graded_artifacts_differ(tmp_path: Path):
    """Spec: mismatched commitments invalidate the result — it cannot count
    as a valid update, and summaries refuse invalid records."""
    proto = write_json(tmp_path / "study.json", make_protocol(n_tasks=1))
    att = make_attempt("t1-A-1-a1", outcome="accept", minutes=5.0)
    orc = make_oracle("t1-A-1-a1", "compatible")
    orc["graded_artifact"] = {"digest": digest("a-different-artifact")}
    result = make_task_result("t1", [att], [orc],
                              {"attempt_id": "t1-A-1-a1", "independently_valid": True})
    write_run(tmp_path, "t1", result)

    v = run_cli("validate", "--protocol", str(proto), "--runs", str(tmp_path / "results"))
    assert v.returncode == 1
    assert "artifact" in v.stderr.lower()

    s = run_cli("summarize", "--protocol", str(proto), "--runs", str(tmp_path / "results"))
    assert s.returncode == 1, "summaries must refuse invalid records"


def test_missing_margins_prevent_confirmatory_claims(tmp_path: Path):
    """Spec: confirmatory without preregistration is refused with missing
    fields listed; the fixture-labelled twin stays possible."""
    confirmatory = write_json(tmp_path / "confirmatory.json", make_protocol(mode="confirmatory"))
    v = run_cli("validate", "--protocol", str(confirmatory))
    assert v.returncode == 1
    for field in ("risk_margin", "completion_margin", "stopping_rules"):
        assert field in v.stderr, f"missing field {field} must be listed"

    fixture_twin = write_json(tmp_path / "fixture.json", make_protocol(mode="fixture"))
    ok = run_cli("validate", "--protocol", str(fixture_twin))
    assert ok.returncode == 0, ok.stderr


def test_duplicate_ids_fail_validation(tmp_path: Path):
    """Duplicate task and attempt ids are validation errors, both listed."""
    proto = make_protocol(n_tasks=1)
    proto["tasks"].append(make_task("t1"))
    proto = write_json(tmp_path / "study.json", proto)
    v = run_cli("validate", "--protocol", str(proto))
    assert v.returncode == 1
    assert "duplicate" in v.stderr.lower()

    proto2 = write_json(tmp_path / "study2.json", make_protocol(n_tasks=1))
    att1 = make_attempt("dup-attempt", outcome="accept", minutes=1.0)
    att2 = make_attempt("dup-attempt", outcome="accept", minutes=1.0)
    oracles = [make_oracle("dup-attempt", "compatible"), make_oracle("dup-attempt", "compatible")]
    write_run(tmp_path, "t1", make_task_result("t1", [att1, att2], oracles))
    v2 = run_cli("validate", "--protocol", str(proto2), "--runs", str(tmp_path / "results"))
    assert v2.returncode == 1
    assert "duplicate" in v2.stderr.lower()


def test_missing_cost_is_never_zero(tmp_path: Path):
    """Unavailability must be declared, never recorded as a fabricated zero;
    every standard cost field must declare its basis."""
    proto = write_json(tmp_path / "study.json", make_protocol(n_tasks=1))
    att = make_attempt("t1-A-1-a1", outcome="accept", minutes=5.0)
    base_costs = att["costs"]

    cases = [
        ("zeroed", {"human_minutes": {"basis": "unavailable", "value": 0},
                    "compute_cost_usd": {"basis": "unavailable"},
                    "wall_time_minutes": {"basis": "measured", "value": 5.0}}, False),
        ("absent", {"compute_cost_usd": {"basis": "unavailable"},
                    "wall_time_minutes": {"basis": "measured", "value": 5.0}}, False),
        ("novalue", {"human_minutes": {"basis": "measured"},
                     "compute_cost_usd": {"basis": "unavailable"},
                     "wall_time_minutes": {"basis": "measured", "value": 5.0}}, False),
        ("measured-zero", {"human_minutes": {"basis": "measured", "value": 0},
                           "compute_cost_usd": {"basis": "unavailable"},
                           "wall_time_minutes": {"basis": "measured", "value": 5.0}}, True),
    ]
    for name, costs, expect_ok in cases:
        case = dict(att)
        case["costs"] = costs
        run_dir = tmp_path / "cases" / name
        write_run(run_dir, "t1", make_task_result("t1", [case], [make_oracle("t1-A-1-a1", "compatible")]))
        v = run_cli("validate", "--protocol", str(proto), "--runs", str(run_dir / "results"))
        assert v.returncode == (0 if expect_ok else 1), v.stderr
        if not expect_ok:
            assert "human_minutes" in v.stderr


def test_incomplete_commitments_fail_validation(tmp_path: Path):
    """Missing digests in commitments are validation errors."""
    proto = make_protocol(n_tasks=1)
    task = make_task("t1")
    del task["oracle_commitment"]["tests_digest"]
    proto["tasks"] = [task]
    proto = write_json(tmp_path / "study.json", proto)
    v = run_cli("validate", "--protocol", str(proto))
    assert v.returncode == 1

    proto2 = write_json(tmp_path / "study2.json", make_protocol(n_tasks=1))
    att = make_attempt("t1-A-1-a1", outcome="accept", minutes=1.0)
    att["requested_artifact"] = {"digest": ""}
    write_run(tmp_path, "t1", make_task_result("t1", [att], [make_oracle("t1-A-1-a1", "compatible")]))
    v2 = run_cli("validate", "--protocol", str(proto2), "--runs", str(tmp_path / "results"))
    assert v2.returncode == 1


def test_unknown_schema_version_rejected(tmp_path: Path):
    proto = make_protocol(n_tasks=1)
    proto["schema_version"] = 2
    proto = write_json(tmp_path / "study.json", proto)
    v = run_cli("validate", "--protocol", str(proto))
    assert v.returncode == 1
    assert "schema_version" in v.stderr