# Purpose: Red-first tests for the wild-1xk held-out corpus execution slice.
#   Covers corpus derivation from the committed e5 cohort under seal discipline,
#   real adapter registration (host declared ranges, CI, ecosystem, Wild), and
#   the end-to-end held-out comparison through the landed harness.
# Responsibilities: Prove the corpus build excludes oracle-unresolvable cases
#   with recorded reasons, maps the e5 independent verdicts to break/ok
#   outcomes without touching the committed cohort, registers the four real
#   adapters as harness command templates, and that adapter verdict mappings
#   are honest (caret semantics, replay outcomes, wild envelope decisions).
# Rationale: wild-1xk remaining scope. The harness (heldout_eval.py) is
#   landed; this slice authors the sealed corpus and the real adapters that
#   feed it. Every adapter verdict mapping is unit-pinned here before any
#   real comparison run, so the committed results report can be audited.

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "experiments" / "heldout_corpus.py"
COHORT = REPO / "experiments" / "update_fixtures" / "e5" / "cases.json"
HELDOUT_EVAL = REPO / "experiments" / "heldout_eval.py"

ADAPTERS = ("host_ranges", "ci", "ecosystem", "wild")

# Committed e5 cohort ground truth (independent verdicts fixed by real Cargo
# replay before any miner tuning; see cases.json note).
DEVELOPMENT_CASES = {
    "cell-excluded-compatible-major",
    "cell-allowed-incompatible-patch",
    "cell-allowed-compatible-update",
    "cell-excluded-incompatible-major",
}
EVALUATION_CASES = {
    "transitive-addition",
    "singleton-conflict",
    "platform-ineligibility",
    "dynamic-usage-unresolved",
    "wrong-target-selection",
    "baseline-failure",
    "migration-supplied",
    "intent-change",
}
UNRESOLVED_CASES = {
    "singleton-conflict",
    "dynamic-usage-unresolved",
    "wrong-target-selection",
    "baseline-failure",
}
# Adjudicable held-out cases after exclusion (4 of 8; the 4 unresolved are
# resolution-level refusals, not upgrade-compatibility outcomes).
ADJUDICABLE_HELD_OUT = {
    "transitive-addition": "ok",
    "platform-ineligibility": "break",
    "migration-supplied": "ok",
    "intent-change": "ok",
}


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _run_eval(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(HELDOUT_EVAL), *args],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=120,
    )


def _load_module(name: str):
    spec = importlib.util.spec_from_file_location(
        name, REPO / "experiments" / "heldout_adapters" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _build_corpus(tmp: Path, cohort: Path | None = None) -> Path:
    out = tmp / "heldout"
    result = _run(["build", "--cohort", str(cohort or COHORT), "--out", str(out)])
    assert result.returncode == 0, result.stderr
    return out


# --- corpus build ------------------------------------------------------------


def test_corpus_build_derives_pools_and_oracle_from_committed_cohort(tmp_path):
    out = _build_corpus(tmp_path)
    cases = json.loads((out / "cases.json").read_text())["cases"]
    pool_by_case = {c["id"]: c["pool"] for c in cases}

    # Only adjudicable cases enter the comparison corpus; pool mapping follows
    # the committed e5 split.
    assert set(pool_by_case) == set(ADJUDICABLE_HELD_OUT) | {
        c for c in DEVELOPMENT_CASES}
    for case_id, pool in pool_by_case.items():
        if case_id in ADJUDICABLE_HELD_OUT:
            assert pool == "held_out"
        else:
            assert pool == "development"

    # Every case carries family integrity inputs and unavailable human time.
    for case in cases:
        assert case["family"] == case["id"]
        assert case["human_minutes"] == {"value": None, "basis": "unavailable"}

    # Oracle outcomes cover exactly the corpus cases with the mapped verdict.
    oracle = json.loads((out / "oracle.json").read_text())
    outcomes = {o["case_id"]: o["outcome"] for o in oracle["outcomes"]}
    assert outcomes == {**ADJUDICABLE_HELD_OUT,
                        "cell-excluded-compatible-major": "ok",
                        "cell-allowed-incompatible-patch": "break",
                        "cell-allowed-compatible-update": "ok",
                        "cell-excluded-incompatible-major": "break"}

    # Unresolved cases are excluded with a recorded reason, never silently.
    excluded = json.loads((out / "excluded.json").read_text())
    assert {e["id"] for e in excluded["excluded"]} == UNRESOLVED_CASES
    for entry in excluded["excluded"]:
        assert "unresolved" in entry["reason"]


def test_corpus_build_records_case_context_with_real_base_version(tmp_path):
    out = _build_corpus(tmp_path)
    context = json.loads((out / "case_context.json").read_text())["cases"]
    by_id = {c["id"]: c for c in context}
    # consumer-base cases sit on the committed dept 1.2.3 lock.
    assert by_id["transitive-addition"]["consumer"].endswith("consumer-base")
    assert by_id["transitive-addition"]["base"] == "1.2.3"
    assert by_id["transitive-addition"]["target"] == "1.9.0"
    # Case-scoped consumers keep their own trees (the one adjudicable case
    # that does not sit on the shared consumer-base tree).
    assert by_id["cell-excluded-compatible-major"]["consumer"].endswith(
        "cases/cell-excluded-compatible-major/consumer")
    # Excluded cases are absent from the adapter context by construction.
    assert "singleton-conflict" not in by_id
    # Every corpus case has full adapter context.
    for case_id in set(ADJUDICABLE_HELD_OUT) | DEVELOPMENT_CASES:
        entry = by_id[case_id]
        assert entry["consumer"] and entry["target"] and entry["base"]


def test_corpus_build_refuses_unexpected_cohort_schema(tmp_path):
    bad = tmp_path / "bad-cohort.json"
    _write_json(bad, {"version": 99, "cases": []})
    result = _run(["build", "--cohort", str(bad), "--out", str(tmp_path / "o")])
    assert result.returncode == 2
    assert "cohort" in result.stderr.lower()


def test_corpus_build_refuses_unknown_independent_verdict(tmp_path):
    cohort = json.loads(COHORT.read_text())
    cohort["cases"][0]["independent_verdict"] = "maybe"
    bad = tmp_path / "cohort.json"
    _write_json(bad, cohort)
    result = _run(["build", "--cohort", str(bad), "--out", str(tmp_path / "o")])
    assert result.returncode == 2
    assert "maybe" in result.stderr


def test_corpus_build_refuses_duplicate_case_ids(tmp_path):
    cohort = json.loads(COHORT.read_text())
    cohort["cases"].append(dict(cohort["cases"][0]))
    bad = tmp_path / "cohort.json"
    _write_json(bad, cohort)
    result = _run(["build", "--cohort", str(bad), "--out", str(tmp_path / "o")])
    assert result.returncode == 2
    assert "duplicate" in result.stderr


def test_corpus_build_refuses_cohort_without_adjudicable_held_out(tmp_path):
    cohort = json.loads(COHORT.read_text())
    for case in cohort["cases"]:
        if case.get("split") == "evaluation":
            case["independent_verdict"] = "unresolved"
    bad = tmp_path / "cohort.json"
    _write_json(bad, cohort)
    # Consumer paths resolve relative to the cohort file's parent: stage
    # minimal trees so lock parsing cannot mask the intended refusal.
    lock = "[[package]]\nname = \"dept\"\nversion = \"1.2.3\"\n"
    (tmp_path / "consumer-base").mkdir()
    (tmp_path / "consumer-base" / "Cargo.lock").write_text(lock)
    scoped = (tmp_path / "cases" / "cell-excluded-compatible-major" / "consumer")
    scoped.mkdir(parents=True)
    (scoped / "Cargo.lock").write_text(lock)
    result = _run(["build", "--cohort", str(bad), "--out", str(tmp_path / "o")])
    assert result.returncode == 2
    assert "held_out" in result.stderr


def test_corpus_cases_pass_harness_split_family_guard(tmp_path):
    out = _build_corpus(tmp_path)
    result = _run_eval(["split", "--cases", str(out / "cases.json"),
                        "--out", str(tmp_path / "split")])
    assert result.returncode == 0, result.stderr
    split = json.loads((tmp_path / "split" / "split.json").read_text())
    assert sum(1 for p in split["pool_by_case"].values()
               if p == "held_out") == 4


def test_corpus_build_registers_four_real_adapters(tmp_path):
    out = _build_corpus(tmp_path)
    checkers = json.loads((out / "checkers.json").read_text())["checkers"]
    names = {c["name"] for c in checkers}
    assert names == set(ADAPTERS)
    for checker in checkers:
        script = REPO / checker["cmd"][1]
        assert script.exists(), f"adapter script missing: {script}"
        # The harness appends the case id; templates must not bake one in.
        assert checker["cmd"][-1] != "transitive-addition"


# --- sealed end-to-end comparison through the landed harness -----------------


def test_seal_and_compare_held_out_end_to_end_with_stub_checker(tmp_path):
    out = _build_corpus(tmp_path)

    split_rc = _run_eval(["split", "--cases", str(out / "cases.json"),
                          "--out", str(tmp_path / "split")])
    assert split_rc.returncode == 0
    seal_rc = _run_eval(["seal", "--oracle", str(out / "oracle.json"),
                         "--out", str(tmp_path / "seal")])
    assert seal_rc.returncode == 0

    stub = tmp_path / "stub_checker.py"
    stub.write_text('print(\'{"verdict": "accept"}\')\n', encoding="utf-8")
    _write_json(tmp_path / "checkers.json", {
        "checkers": [{"name": "stub",
                      "cmd": [sys.executable, str(stub)]}]})

    tool = tmp_path / "tools" / "probe.sh"
    tool.parent.mkdir(parents=True, exist_ok=True)
    tool.write_text("#!/bin/sh\necho probe\n", encoding="utf-8")
    freeze_rc = _run_eval(["freeze", "--tool", str(tool),
                           "--out", str(tmp_path / "freeze")])
    assert freeze_rc.returncode == 0

    compare_rc = _run_eval([
        "compare", "--freeze", str(tmp_path / "freeze"),
        "--split", str(tmp_path / "split"),
        "--cases", str(out / "cases.json"),
        "--oracle", str(out / "oracle.json"),
        "--seal", str(tmp_path / "seal"),
        "--checkers", str(tmp_path / "checkers.json"),
        "--pool", "held_out",
        "--out", str(tmp_path / "compare.json"),
    ])
    # The always-accept stub misses the one definite-break held-out case.
    assert compare_rc.returncode == 1
    compare = json.loads((tmp_path / "compare.json").read_text())
    runs = {(r["case_id"], r["outcome_class"]) for r in compare["runs"]}
    assert runs == {
        ("transitive-addition", "correct-accept"),
        ("migration-supplied", "correct-accept"),
        ("intent-change", "correct-accept"),
        ("platform-ineligibility", "missed-breakage"),
    }


def test_host_ranges_adapter_matches_caret_semantics_on_held_out(tmp_path):
    out = _build_corpus(tmp_path)
    expected = {
        # consumer-base declares dept = "~1.2" (cargo tilde: >=1.2.0, <1.3.0)
        "transitive-addition": "reject",     # 1.9.0 outside the tilde range
        "intent-change": "accept",           # 1.2.4 within the tilde range
        "platform-ineligibility": "reject",  # 1.8.0 outside the tilde range
        "migration-supplied": "reject",      # 2.1.0 outside the tilde range
    }
    for case_id, verdict in expected.items():
        result = subprocess.run(
            [sys.executable,
             str(REPO / "experiments" / "heldout_adapters" / "host_ranges.py"),
             case_id, "--context", str(out / "case_context.json")],
            cwd=REPO, capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stderr
        emitted = json.loads(result.stdout.strip().splitlines()[-1])
        assert emitted["verdict"] == verdict, f"{case_id}: {emitted}"


# --- adapter verdict mappings (unit-pinned) ----------------------------------


def test_ci_adapter_inner_timeout_stays_under_harness_cap():
    # A hung replay must be attributed to this adapter (its own timeout),
    # not to the harness's CHECKER_TIMEOUT_SECONDS=60 kill.
    ci = _load_module("ci")
    assert ci.ADAPTER_TIMEOUT_SECONDS < 60


def test_ci_adapter_maps_replay_outcomes_honestly():
    ci = _load_module("ci")
    mapping = {
        "resolved-and-consumer-tests-passed": "accept",
        "resolved-then-consumer-tests-failed": "reject",
        "resolution-conflict": "reject",
        "resolution-refused-by-range": "unknown",
        "resolved-but-selected-target-mismatch": "unknown",
        "something-unforeseen": "error",
    }
    for outcome, verdict in mapping.items():
        assert ci.map_replay_outcome(outcome) == verdict, outcome


def test_ecosystem_adapter_applies_cargo_caret_ruling():
    ecosystem = _load_module("ecosystem")
    compatible = [("1.2.3", "1.2.5"), ("1.2.3", "1.9.0"), ("0.1.0", "0.1.5")]
    incompatible = [("1.2.3", "2.0.0"), ("0.1.0", "0.2.0"), ("0.8.3", "0.9.0")]
    for base, target in compatible:
        assert ecosystem.cargo_caret_compatible(base, target) is True, (base, target)
    for base, target in incompatible:
        assert ecosystem.cargo_caret_compatible(base, target) is False, (base, target)


def test_wild_adapter_maps_envelope_decisions_honestly():
    wild = _load_module("wild")
    accept_envelope = {"decision": "accept", "assurance": "Accept"}
    reject_envelope = {"decision": "refuse", "assurance": "Reject"}
    unknown_envelope = {"decision": "refuse", "assurance": "Unknown"}
    error_envelope = {"decision": "refuse", "assurance": "whatever"}
    assert wild.map_envelope(accept_envelope) == "accept"
    assert wild.map_envelope(reject_envelope) == "reject"
    assert wild.map_envelope(unknown_envelope) == "unknown"
    assert wild.map_envelope(error_envelope) == "error"