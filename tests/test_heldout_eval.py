# Purpose: Red-first command-level tests for the held-out validation harness
#   (beads wild-1xk). Covers tooling freeze verification, sealed held-out/dev
#   split discipline, four-checker comparison classification, and the
#   separate-metrics report with explicit denominators.
# Responsibilities: Prove that evaluation tooling drift refuses runs, held-out
#   data cannot leak into development commands, sealed oracle outcomes gate any
#   held-out comparison, checker verdicts classify into exactly one outcome
#   class, and the report renders missed breakages, false blocks, Unknown rate,
#   coverage, execution cost, and human contract-maintenance time separately —
#   never merged into aggregate accuracy.
# Rationale: wild-1xk is the value-proposition validation ticket. The viability
#   evaluation showed aggregate accuracy conceals the safety tradeoff (missed
#   breakages vs false blocks), so every metric here has its own denominator.
#   The harness is a stub-checker-driven, offline, deterministic fixture run —
#   NOT evidence about future v1 runtime failure rates.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "experiments" / "heldout_eval.py"

DISCLAIMER = (
    "This is validation of the value proposition, not evidence that the "
    "future v1 runtime has the prototype failure rates."
)


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _case_entry(case_id: str, family: str, pool: str, minutes: int | None) -> dict:
    entry = {"id": case_id, "family": family, "pool": pool}
    if minutes is None:
        entry["human_minutes"] = {"value": None, "basis": "unavailable"}
    else:
        entry["human_minutes"] = {"value": minutes, "basis": "measured"}
    return entry


def _default_oracle() -> dict:
    return {
        "oracle": "independent-prepared",
        "outcomes": [
            {"case_id": "alpha-1", "outcome": "break"},
            {"case_id": "alpha-2", "outcome": "ok"},
        ],
    }


def _stage(tmp: Path, oracle: dict | None = None) -> dict:
    """Build the full fixture environment: tool, freeze, cases, split, oracle, seal."""
    tool = tmp / "tools" / "probe.sh"
    tool.parent.mkdir(parents=True, exist_ok=True)
    tool.write_text("#!/bin/sh\necho probe\n", encoding="utf-8")
    env = {"tmp": tmp}

    cases = {
        "version": 1,
        "cases": [
            _case_entry("alpha-1", "alpha", "held_out", 30),
            _case_entry("alpha-2", "alpha", "held_out", None),
            _case_entry("beta-1", "beta", "development", 15),
            _case_entry("beta-2", "beta", "development", None),
        ],
    }
    env["cases"] = tmp / "cases.json"
    _write_json(env["cases"], cases)

    env["oracle"] = tmp / "oracle.json"
    _write_json(env["oracle"], oracle if oracle is not None else _default_oracle())

    env["freeze"] = tmp / "freeze"
    proc = _run(["freeze", "--tool", str(tool), "--out", str(env["freeze"])])
    assert proc.returncode == 0, proc.stderr

    env["split"] = tmp / "split"
    proc = _run(["split", "--cases", str(env["cases"]), "--out", str(env["split"])])
    assert proc.returncode == 0, proc.stderr

    env["seal"] = tmp / "seal"
    proc = _run(["seal", "--oracle", str(env["oracle"]), "--out", str(env["seal"])])
    assert proc.returncode == 0, proc.stderr
    return env


def _checkers_file(tmp: Path, verdict_by_case: dict[str, dict[str, str]]) -> Path:
    """Each checker command is a self-contained python -c verdict stub."""
    entries = []
    for name, table in verdict_by_case.items():
        body = (
            "import json,sys;aid=sys.argv[1];"
            f"print(json.dumps({{'verdict': {table!r}.get(aid, 'unknown')}}))"
        )
        entries.append({"name": name, "cmd": [sys.executable, "-c", body]})
    path = tmp / "checkers.json"
    _write_json(path, {"version": 1, "checkers": entries})
    return path


def _run_compare(env: dict, checkers: Path) -> subprocess.CompletedProcess:
    return _run([
        "compare",
        "--freeze", str(env["freeze"]),
        "--split", str(env["split"]),
        "--cases", str(env["cases"]),
        "--oracle", str(env["oracle"]),
        "--seal", str(env["seal"]),
        "--checkers", str(checkers),
        "--pool", "held_out",
        "--out", str(env["tmp"] / "compare.json"),
    ])


def _report_text(env: dict, checkers: Path) -> tuple[str, dict]:
    proc = _run_compare(env, checkers)
    compare_path = env["tmp"] / "compare.json"
    assert compare_path.exists(), proc.stderr
    out = env["tmp"] / "report.md"
    proc = _run(["report", "--compare", str(compare_path),
                 "--cases", str(env["cases"]), "--oracle", str(env["oracle"]),
                 "--out", str(out)])
    assert proc.returncode == 0, proc.stderr
    return out.read_text(encoding="utf-8"), json.loads(compare_path.read_text(encoding="utf-8"))


# --- freeze -----------------------------------------------------------------


def test_freeze_build_then_verify_passes(tmp_path):
    env = _stage(tmp_path)
    proc = _run(["verify", "--freeze", str(env["freeze"])])
    assert proc.returncode == 0, proc.stderr


def test_freeze_verify_names_drifted_tool(tmp_path):
    env = _stage(tmp_path)
    (tmp_path / "tools" / "probe.sh").write_text("#!/bin/sh\necho tampered\n", encoding="utf-8")
    proc = _run(["verify", "--freeze", str(env["freeze"])])
    assert proc.returncode == 2
    assert "probe.sh" in proc.stderr


def test_compare_refuses_when_frozen_tool_drifted(tmp_path):
    env = _stage(tmp_path)
    (tmp_path / "tools" / "probe.sh").write_text("drift\n", encoding="utf-8")
    proc = _run_compare(env, _checkers_file(tmp_path, {"wild": {}}))
    assert proc.returncode == 2
    assert "freeze" in proc.stderr.lower()


# --- split discipline -------------------------------------------------------


def test_split_is_deterministic_and_byte_identical(tmp_path):
    env = _stage(tmp_path)
    out2 = tmp_path / "split-again"
    proc = _run(["split", "--cases", str(env["cases"]), "--out", str(out2)])
    assert proc.returncode == 0, proc.stderr
    assert (env["split"] / "split.json").read_bytes() == (out2 / "split.json").read_bytes()


def test_split_refuses_family_spanning_both_pools(tmp_path):
    cases = {
        "version": 1,
        "cases": [
            {"id": "a-1", "family": "fam", "pool": "development",
             "human_minutes": {"value": None, "basis": "unavailable"}},
            {"id": "a-2", "family": "fam", "pool": "held_out",
             "human_minutes": {"value": None, "basis": "unavailable"}},
        ],
    }
    path = tmp_path / "cases.json"
    _write_json(path, cases)
    proc = _run(["split", "--cases", str(path), "--out", str(tmp_path / "split")])
    assert proc.returncode == 2
    assert "fam" in proc.stderr


def test_dev_select_refuses_held_out_id(tmp_path):
    env = _stage(tmp_path)
    proc = _run(["dev-select", "--split", str(env["split"]), "--ids", "alpha-1,beta-1"])
    assert proc.returncode == 2
    assert "alpha-1" in proc.stderr
    assert "held_out" in proc.stderr


# --- sealed-oracle discipline ----------------------------------------------


def test_compare_before_seal_refuses(tmp_path):
    env = _stage(tmp_path)
    env["seal"] = tmp_path / "no-seal"
    proc = _run_compare(env, _checkers_file(tmp_path, {"wild": {}}))
    assert proc.returncode == 2
    assert "seal" in proc.stderr.lower()


def test_compare_refuses_oracle_modified_after_seal(tmp_path):
    env = _stage(tmp_path)
    _write_json(env["oracle"], {
        "oracle": "independent-prepared",
        "outcomes": [
            {"case_id": "alpha-1", "outcome": "ok"},
            {"case_id": "alpha-2", "outcome": "ok"},
        ],
    })
    proc = _run_compare(env, _checkers_file(tmp_path, {"wild": {}}))
    assert proc.returncode == 2
    assert "digest" in proc.stderr.lower()


def test_compare_refuses_held_out_case_missing_from_oracle(tmp_path):
    env = _stage(tmp_path, oracle={
        "oracle": "independent-prepared",
        "outcomes": [{"case_id": "alpha-1", "outcome": "break"}],
    })
    proc = _run_compare(env, _checkers_file(tmp_path, {"wild": {}}))
    assert proc.returncode == 2
    assert "alpha-2" in proc.stderr


# --- classification ---------------------------------------------------------


def test_classification_maps_verdicts_to_single_classes(tmp_path):
    env = _stage(tmp_path)
    checkers = _checkers_file(tmp_path, {
        "wild": {"alpha-1": "reject", "alpha-2": "reject"},
        "host-ranges": {"alpha-1": "accept", "alpha-2": "accept"},
    })
    proc = _run_compare(env, checkers)
    assert proc.returncode == 1, proc.stderr
    report = json.loads((tmp_path / "compare.json").read_text(encoding="utf-8"))
    by_checker: dict[str, dict[str, str]] = {}
    for run in report["runs"]:
        by_checker.setdefault(run["checker"], {})[run["case_id"]] = run["outcome_class"]
    assert by_checker["wild"]["alpha-1"] == "correct-reject"
    assert by_checker["wild"]["alpha-2"] == "false-block"
    assert by_checker["host-ranges"]["alpha-1"] == "missed-breakage"
    assert by_checker["host-ranges"]["alpha-2"] == "correct-accept"


def test_unknown_verdict_is_not_merged_into_definite_classes(tmp_path):
    env = _stage(tmp_path)
    checkers = _checkers_file(tmp_path, {"wild": {"alpha-1": "unknown"}})
    proc = _run_compare(env, checkers)
    report = json.loads((tmp_path / "compare.json").read_text(encoding="utf-8"))
    wild = {r["case_id"]: r["outcome_class"] for r in report["runs"]
            if r["checker"] == "wild"}
    assert wild["alpha-1"] == "unknown"
    assert wild["alpha-2"] == "unknown"


def test_all_correct_comparison_exits_zero(tmp_path):
    env = _stage(tmp_path)
    checkers = _checkers_file(tmp_path, {
        "wild": {"alpha-1": "reject", "alpha-2": "accept"},
    })
    proc = _run_compare(env, checkers)
    assert proc.returncode == 0, proc.stderr


# --- review-fix regression tests --------------------------------------------


def test_report_refuses_oracle_mismatch_against_compare_artifact(tmp_path):
    env = _stage(tmp_path)
    proc = _run_compare(env, _checkers_file(tmp_path, {"wild": {}}))
    assert proc.returncode in (0, 1), proc.stderr
    swapped = tmp_path / "swapped-oracle.json"
    _write_json(swapped, {
        "oracle": "independent-prepared",
        "outcomes": [
            {"case_id": "alpha-1", "outcome": "ok"},
            {"case_id": "alpha-2", "outcome": "ok"},
        ],
    })
    out = tmp_path / "report.md"
    proc = _run(["report", "--compare", str(tmp_path / "compare.json"),
                 "--cases", str(env["cases"]), "--oracle", str(swapped),
                 "--out", str(out)])
    assert proc.returncode == 2
    assert "mismatch" in proc.stderr.lower()


def test_compare_records_freeze_and_oracle_provenance(tmp_path):
    env = _stage(tmp_path)
    proc = _run_compare(env, _checkers_file(tmp_path, {"wild": {}}))
    assert proc.returncode in (0, 1), proc.stderr
    compare = json.loads((tmp_path / "compare.json").read_text(encoding="utf-8"))
    assert compare["oracle_sha256"]
    assert compare["freeze_sha256"]


def test_crashed_checker_is_classified_error_not_graded(tmp_path):
    env = _stage(tmp_path)
    path = tmp_path / "checkers.json"
    _write_json(path, {"version": 1, "checkers": [{
        "name": "crasher",
        "cmd": [sys.executable, "-c",
                "import json,sys;print(json.dumps({'verdict': 'accept'}));"
                "import os;os._exit(3)"],
    }]})
    proc = _run_compare(env, path)
    assert proc.returncode == 0, proc.stderr
    compare = json.loads((tmp_path / "compare.json").read_text(encoding="utf-8"))
    run = compare["runs"][0]
    assert run["verdict"] == "error"
    assert run["outcome_class"] == "unknown"
    assert "exited 3" in run["note"]


def test_dev_pool_coverage_refusal_wording_is_pool_neutral(tmp_path):
    env = _stage(tmp_path)
    _write_json(env["oracle"], {
        "oracle": "independent-prepared",
        "outcomes": [{"case_id": "alpha-1", "outcome": "break"},
                     {"case_id": "alpha-2", "outcome": "ok"}],
    })
    proc = _run([
        "compare",
        "--freeze", str(env["freeze"]),
        "--split", str(env["split"]),
        "--cases", str(env["cases"]),
        "--oracle", str(env["oracle"]),
        "--seal", str(env["seal"]),
        "--checkers", str(_checkers_file(tmp_path, {"wild": {}})),
        "--pool", "development",
        "--out", str(tmp_path / "compare-dev.json"),
    ])
    assert proc.returncode == 2
    assert "beta-1" in proc.stderr
    assert "held-out case(s)" not in proc.stderr


# --- report -----------------------------------------------------------------


def test_report_metrics_are_separate_per_checker_with_denominators(tmp_path):
    env = _stage(tmp_path)
    checkers = _checkers_file(tmp_path, {
        "wild": {"alpha-1": "reject", "alpha-2": "reject"},
        "host-ranges": {"alpha-1": "accept", "alpha-2": "accept"},
    })
    text, _ = _report_text(env, checkers)
    assert "missed-breakage" in text
    assert "false-block" in text
    assert "denominator" in text
    for checker in ("wild", "host-ranges"):
        assert checker in text


def test_report_has_no_aggregate_accuracy_substitute(tmp_path):
    env = _stage(tmp_path)
    text, _ = _report_text(env, _checkers_file(tmp_path, {"wild": {}}))
    assert "aggregate-accuracy" not in text
    assert DISCLAIMER in text


def test_report_zero_denominator_null_ratio_named_reason(tmp_path):
    # Both held-out cases break: the false-block denominator is zero.
    env = _stage(tmp_path, oracle={
        "oracle": "independent-prepared",
        "outcomes": [
            {"case_id": "alpha-1", "outcome": "break"},
            {"case_id": "alpha-2", "outcome": "break"},
        ],
    })
    text, _ = _report_text(env, _checkers_file(tmp_path, {"wild": {"alpha-1": "reject"}}))
    assert "null" in text.lower()
    assert "zero-denominator" in text


def test_report_covers_cost_and_maintenance_separately(tmp_path):
    env = _stage(tmp_path)
    text, compare = _report_text(env, _checkers_file(tmp_path, {"wild": {"alpha-1": "reject"}}))
    assert "execution-cost" in text
    assert "human-contract-maintenance-time" in text
    assert "unavailable" in text
    for run in compare["runs"]:
        assert "elapsed_seconds" in run