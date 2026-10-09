# Purpose: Red-first command-level runtime tests for authored law execution
#   (beads wild-mh5.4): the `wild check` runner executes digest-bound law
#   suites against the actual candidate artifact under an enforced sandbox
#   and reports method-labelled v1 law evidence.
# Responsibilities: Exercise `wild check` as a subprocess with executable
#   law obligations and the five law-invocation inputs (harnesses, fixtures,
#   budgets, environment, evaluation_time); pin the slice's named scenarios
#   and decided semantics — human and agent predicates receive equal
#   checking (D6); same-contract changed implementations get fresh evidence
#   (D2/D3); proof/exhaustive methods downgrade to inconclusive (D10);
#   timeout/crash/ambient-access attempts yield inconclusive, never sampled
#   pass (D5); echo-validation rejects stale replayed and mismatched
#   results; duplicate execution catches nondeterminism (D9); unrunnable
#   bound bytes stay law-retained-inconclusive while other obligations still
#   evaluate (unsupported-law isolation); a missing interpreter is an
#   operational error (exit 2); a policy requiring law evidence over only a
#   proposed law yields Unknown, not an error; and the invocation commitment
#   carries the real supplied bindings plus enforced sandbox capabilities
#   (D7/D8).
# Rationale: Acceptance is genuine sandboxed execution of the bound suite
#   bytes with runner echo-validation against runner-derived digests; canned
#   success responses would prove nothing, so every test drives the real CLI
#   and asserts observable records and exit codes. Written red against the
#   mh5.3 binary (which never executes retained suites) and must stay green
#   once this slice lands.

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from test_extract import (
    BIN,
    PROFILE,
    PROVIDER_LIB,
    REPO,
    sha,
    write_bundle,
)
from test_protected_context import (
    AUTHORITY,
    BASE_OBLIGATION_CONTRACT,
    canonical,
    check_request_record,
    diagnostic_codes,
    load_report,
    obligation,
    obligations_doc,
    run_check,
    write_obligations,
)

EVAL_TIME = "2026-10-09T12:00:00Z"

HARNESS_REL = "laws/harness.json"
HARNESS_TEXT = json.dumps(
    {"version": "local-1", "kind": "law-harness", "name": "add-one-law-runner"}
)
FIXTURE_REL = "laws/cases.json"
FIXTURE_TEXT = json.dumps({"cases": ["add_one(1)", "add_one(0)"]})
SUITE_REL = "laws/add_one_law.py"

# The reference executable suite: reads the actual candidate source bytes
# through the invocation's artifact reference, echoes the runner-supplied
# commitments, and reports a sampled pass or a witnessed counterexample.
SUITE_IMPL_CHECK = f"""#!/usr/bin/env python3
import hashlib, json, sys

inv = json.loads(sys.stdin.read())
with open(inv["artifact"]["root"] + "/provider/src/lib.rs", encoding="utf-8") as f:
    src = f.read()
holds = "x + 1" in src
result = {{
    "version": "1",
    "kind": "law_result",
    "law_suite": inv["law"]["suite"],
    "contract": inv["artifact"]["contract"],
    "implementation_artifact": inv["artifact"]["digest"],
    "harness": inv["law"]["harness"],
    "fixtures": [inv["fixtures"]["files"][rel] for rel in sorted(inv["fixtures"]["files"])],
    "seed": inv["seed"],
    "budgets": inv["budgets"],
    "method": "sampled",
    "status": "pass" if holds else "counterexample",
    "witness": None if holds else "sha256:" + hashlib.sha256(b"add_one(1)==3").hexdigest(),
    "reason": None,
}}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
"""

SUITE_PROOF = SUITE_IMPL_CHECK.replace(
    '"method": "sampled"',
    '"method": "proof"',
).replace(
    '"witness": None if holds else "sha256:" + hashlib.sha256(b"add_one(1)==3").hexdigest()',
    '"witness": "sha256:" + hashlib.sha256(b"proof witness").hexdigest()',
)

SUITE_EXHAUSTIVE = SUITE_IMPL_CHECK.replace(
    '"method": "sampled"',
    '"method": "exhaustive"',
).replace(
    '"witness": None if holds else "sha256:" + hashlib.sha256(b"add_one(1)==3").hexdigest()',
    '"witness": "sha256:" + hashlib.sha256(b"exhaustive domain").hexdigest()',
)

SUITE_SLEEP = SUITE_IMPL_CHECK.replace(
    "inv = json.loads(sys.stdin.read())",
    "import time\ninv = json.loads(sys.stdin.read())\ntime.sleep(30)",
)

SUITE_CRASH = SUITE_IMPL_CHECK.replace(
    "inv = json.loads(sys.stdin.read())",
    "import sys\nsys.exit(3)",
)

SUITE_AMBIENT = SUITE_IMPL_CHECK.replace(
    "inv = json.loads(sys.stdin.read())",
    'inv = json.loads(sys.stdin.read())\nopen("/etc/hostname")',
)

SUITE_ECHO_MISMATCH = SUITE_IMPL_CHECK.replace(
    '"implementation_artifact": inv["artifact"]["digest"]',
    '"implementation_artifact": "sha256:" + "0" * 64',
)

# Ignores the invocation entirely and replays a plausible stale result.
SUITE_STALE_REPLAY = """#!/usr/bin/env python3
import json, sys

sys.stdin.read()
result = {
    "version": "1",
    "kind": "law_result",
    "law_suite": "sha256:" + "0" * 64,
    "contract": "sha256:" + "0" * 64,
    "implementation_artifact": "sha256:" + "0" * 64,
    "harness": "sha256:" + "0" * 64,
    "fixtures": [],
    "seed": 7,
    "budgets": {"wall_ms": 2000},
    "method": "sampled",
    "status": "pass",
    "witness": None,
    "reason": None,
}
print(json.dumps(result, sort_keys=True, separators=(",", ":")))
"""

# Each run embeds the wall-clock time into the witness, so the two runs can
# never agree on canonical bytes even though both claim pass.
SUITE_NONDETERMINISTIC = SUITE_IMPL_CHECK.replace(
    "import hashlib, json, sys",
    "import hashlib, json, sys, time",
).replace(
    '"witness": None if holds else "sha256:" + hashlib.sha256(b"add_one(1)==3").hexdigest()',
    '"witness": "sha256:" + hashlib.sha256(str(time.time_ns()).encode()).hexdigest()',
)

SUITE_MISSING_INTERPRETER = SUITE_IMPL_CHECK.replace(
    "#!/usr/bin/env python3",
    "#!/nonexistent-interpreter-9999",
)


def law_bundle(
    root: Path,
    suite_text: str = SUITE_IMPL_CHECK,
    provider_lib: str = PROVIDER_LIB,
) -> dict[str, str]:
    """A standard bundle plus the law suite, harness, and fixture assets."""
    files = write_bundle(root)
    if provider_lib != PROVIDER_LIB:
        (root / "provider/src/lib.rs").write_text(provider_lib)
        files["provider/src/lib.rs"] = provider_lib
    (root / "laws").mkdir(parents=True, exist_ok=True)
    (root / HARNESS_REL).write_text(HARNESS_TEXT)
    files[HARNESS_REL] = HARNESS_TEXT
    (root / FIXTURE_REL).write_text(FIXTURE_TEXT)
    files[FIXTURE_REL] = FIXTURE_TEXT
    (root / SUITE_REL).write_text(suite_text)
    files[SUITE_REL] = suite_text
    (root / SUITE_REL).chmod(0o755)
    return files


def law_pair(tmp_path: Path, name: str, **kwargs) -> tuple[Path, dict, Path, dict]:
    base_root = tmp_path / f"{name}-base"
    base = law_bundle(base_root, **kwargs)
    cand_root = tmp_path / f"{name}-cand"
    cand = law_bundle(cand_root, **kwargs)
    return base_root, base, cand_root, cand


def law_obligation(id: str) -> dict:
    """An accepted human-origin law obligation bound to the reference suite."""
    return {
        "id": id,
        "scope": "consumer",
        "origin": "human",
        "state": "accepted",
        "authority": dict(AUTHORITY),
        "predicate": {"kind": "law", "suite_digest": sha(SUITE_IMPL_CHECK)},
    }


def agent_law_obligation(id: str) -> dict:
    same = law_obligation(id)
    same["origin"] = "agent"
    return same


def proposed_law_obligation(id: str) -> dict:
    same = law_obligation(id)
    same["state"] = "proposed"
    return same


def law_request(
    base_root: Path,
    base: dict,
    cand_root: Path,
    cand: dict,
    obligations_ref: dict,
    wall_ms: int = 2000,
    **overrides,
) -> dict:
    fields = {
        "harnesses": {HARNESS_REL: sha(HARNESS_TEXT)},
        "fixtures": {FIXTURE_REL: sha(FIXTURE_TEXT)},
        "budgets": {"wall_ms": wall_ms},
        "environment": {"seed": 7},
        "evaluation_time": EVAL_TIME,
    }
    fields.update(overrides)
    return check_request_record(
        base_root, base, cand_root, cand, obligations_ref, **fields
    )


def run_law_check(record: dict, tmp_path: Path, name: str):
    report_path = tmp_path / f"{name}-out" / "report.json"
    proc = run_check(record, report_path)
    return load_report(proc, report_path), proc


def obligation_verdicts(report: dict) -> dict:
    return {o["id"]: o["verdict"] for o in report["obligations"]}


@pytest.fixture(scope="session")
def wild_binary() -> Path:
    if not BIN.exists():
        build = subprocess.run(
            ["cargo", "build", "-q"], cwd=REPO, capture_output=True, text=True
        )
        if build.returncode != 0:
            pytest.fail(f"cargo build failed:\n{build.stderr[-2000:]}")
    assert BIN.exists()
    return BIN


def test_human_and_agent_predicates_receive_identical_checking(wild_binary, tmp_path):
    outcomes = []
    for origin_fn, tag in ((law_obligation, "human"), (agent_law_obligation, "agent")):
        base_root, base, cand_root, cand = law_pair(tmp_path, tag)
        ref = write_obligations(
            tmp_path, obligations_doc([origin_fn("add-one-law")]), name=f"{tag}.json"
        )
        report, proc = run_law_check(
            law_request(base_root, base, cand_root, cand, ref),
            tmp_path,
            f"{tag}-run",
        )
        assert proc.returncode == 0, report.get("diagnostics")
        outcomes.append((origin_fn, report))
    (_, human), (_, agent) = outcomes
    for field in ("decision", "assurance", "law_methods"):
        assert human[field] == agent[field]
    assert (
        obligation_verdicts(human)["add-one-law"]
        == obligation_verdicts(agent)["add-one-law"]
        == "law-pass"
    )
    origins = {
        o["origin"]: o["id"] for o in human["obligations"]
    } | {o["origin"]: o["id"] for o in agent["obligations"]}
    assert origins == {"human": "add-one-law", "agent": "add-one-law"}


def test_sampled_law_pass_allows_acceptance(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(tmp_path, "pass")
    ref = write_obligations(
        tmp_path, obligations_doc([law_obligation("add-one-law")])
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "pass-run"
    )
    assert proc.returncode == 0, report.get("diagnostics")
    assert report["decision"] == "accept"
    assert report["disposition"] == "compatible"
    assert obligation_verdicts(report)["add-one-law"] == "law-pass"
    methods = report["law_methods"]
    assert len(methods) == 1
    entry = methods[0]
    assert entry["obligation_id"] == "add-one-law"
    assert entry["method"] == "sampled"
    assert entry["status"] == "pass"
    # sampled evidence discloses tested scope and is never structural proof
    assert entry["runs"] >= 1


def test_counterexample_blocks_despite_passing_structure(wild_binary, tmp_path):
    base_root, base, _, _ = law_pair(tmp_path, "counter")
    # the candidate keeps the same contract but changes the implementation;
    # the structural obligation still passes while the law counterexamples
    changed_lib = PROVIDER_LIB.replace("x + 1", "x + 2")
    _, _, cand_root, cand = law_pair(tmp_path, "counter-changed", provider_lib=changed_lib)
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [law_obligation("add-one-law"), obligation("add-one-accretes")]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "counter-run"
    )
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Reject"
    assert obligation_verdicts(report)["add-one-accretes"] == "pass"
    assert obligation_verdicts(report)["add-one-law"] == "law-counterexample"


def test_same_contract_changed_implementation_receives_fresh_evaluation(
    wild_binary, tmp_path
):
    base_root, base, cand_root, cand = law_pair(tmp_path, "fresh")
    ref = write_obligations(
        tmp_path, obligations_doc([law_obligation("add-one-law")])
    )
    changed_lib = PROVIDER_LIB.replace("x + 1", "x + 2")
    assert changed_lib != PROVIDER_LIB
    _, _, fresh_root, fresh = law_pair(tmp_path, "changed", provider_lib=changed_lib)
    unchanged_report, _ = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "fresh-run"
    )
    changed_report, proc = run_law_check(
        law_request(base_root, base, fresh_root, fresh, ref), tmp_path, "changed-run"
    )
    assert obligation_verdicts(unchanged_report)["add-one-law"] == "law-pass"
    assert proc.returncode == 1
    assert obligation_verdicts(changed_report)["add-one-law"] == "law-counterexample"
    # the fresh run binds the changed candidate artifact, never stale bytes
    unchanged_art = unchanged_report["law_methods"][0]["result_digest"]
    changed_art = changed_report["law_methods"][0]["result_digest"]
    assert unchanged_art != changed_art


def test_changed_harness_cannot_reuse_stale_evidence(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(tmp_path, "harness-a")
    ref = write_obligations(
        tmp_path, obligations_doc([law_obligation("add-one-law")])
    )
    first_report, _ = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "harness-a-run"
    )
    other_harness = json.dumps(
        {"version": "local-1", "kind": "law-harness", "name": "other-runner"}
    )
    (base_root / HARNESS_REL).write_text(other_harness)
    base[HARNESS_REL] = other_harness
    second_report, proc = run_law_check(
        law_request(
            base_root,
            base,
            cand_root,
            cand,
            ref,
            harnesses={HARNESS_REL: sha(other_harness)},
        ),
        tmp_path,
        "harness-b-run",
    )
    assert proc.returncode == 0, second_report.get("diagnostics")
    first_harness = first_report["invocation_commitment"]["harnesses"]
    second_harness = second_report["invocation_commitment"]["harnesses"]
    assert first_harness != second_harness
    assert second_harness == {HARNESS_REL: sha(other_harness)}
    assert second_report["law_methods"][0]["status"] == "pass"


def test_proof_method_is_downgraded_to_inconclusive(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(tmp_path, "proof", suite_text=SUITE_PROOF)
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "proof-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_PROOF)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "proof-run"
    )
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["proof-law"] == "law-executed-inconclusive"
    assert report["law_methods"][0]["status"] == "inconclusive"
    assert "downgraded" in report["law_methods"][0]["reason"]


def test_exhaustive_method_is_downgraded_to_inconclusive(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "exhaustive", suite_text=SUITE_EXHAUSTIVE
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "exhaustive-law",
                    "scope": "consumer",
                    "origin": "agent",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_EXHAUSTIVE)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "exhaustive-run"
    )
    assert proc.returncode == 1
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["exhaustive-law"] == "law-executed-inconclusive"
    assert report["law_methods"][0]["method"] == "exhaustive"
    assert report["law_methods"][0]["status"] == "inconclusive"


def test_timeout_yields_inconclusive_never_sampled_pass(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "timeout", suite_text=SUITE_SLEEP
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "sleeping-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_SLEEP)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref, wall_ms=500),
        tmp_path,
        "timeout-run",
    )
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["sleeping-law"] == "law-executed-inconclusive"
    assert report["law_methods"][0]["status"] == "inconclusive"


def test_crash_yields_inconclusive(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "crash", suite_text=SUITE_CRASH
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "crashing-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_CRASH)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "crash-run"
    )
    assert proc.returncode == 1
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["crashing-law"] == "law-executed-inconclusive"


def test_ambient_access_attempt_yields_inconclusive(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "ambient", suite_text=SUITE_AMBIENT
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "ambient-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_AMBIENT)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "ambient-run"
    )
    assert proc.returncode == 1
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["ambient-law"] == "law-executed-inconclusive"


def test_echo_mismatch_yields_runner_authored_inconclusive(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "echo", suite_text=SUITE_ECHO_MISMATCH
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "echo-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_ECHO_MISMATCH)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "echo-run"
    )
    assert proc.returncode == 1
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["echo-law"] == "law-executed-inconclusive"


def test_stale_replayed_result_is_echo_rejected(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "stale", suite_text=SUITE_STALE_REPLAY
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "stale-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_STALE_REPLAY)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "stale-run"
    )
    assert proc.returncode == 1
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["stale-law"] == "law-executed-inconclusive"


def test_nondeterministic_law_yields_inconclusive(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "nondet", suite_text=SUITE_NONDETERMINISTIC
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "nondet-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(SUITE_NONDETERMINISTIC)},
                }
            ]
        ),
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "nondet-run"
    )
    assert proc.returncode == 1
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["nondet-law"] == "law-executed-inconclusive"


def test_unsupported_law_is_isolated_and_other_obligations_still_evaluate(
    wild_binary, tmp_path
):
    from test_protected_context import LAW_TEXT

    base_root = tmp_path / "iso-base"
    base = write_bundle(base_root)
    law_rel = "provider/tests/law_add_one.wildlaw"
    (base_root / law_rel).parent.mkdir(parents=True, exist_ok=True)
    (base_root / law_rel).write_text(LAW_TEXT)
    base[law_rel] = LAW_TEXT
    cand_root = tmp_path / "iso-cand"
    cand = write_bundle(cand_root)
    (cand_root / law_rel).parent.mkdir(parents=True, exist_ok=True)
    (cand_root / law_rel).write_text(LAW_TEXT)
    cand[law_rel] = LAW_TEXT
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                obligation("add-one-accretes"),
                {
                    "id": "prose-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {"kind": "law", "suite_digest": sha(LAW_TEXT)},
                },
            ]
        ),
    )
    report_path = tmp_path / "iso-out" / "report.json"
    proc = run_check(
        check_request_record(base_root, base, cand_root, cand, ref), report_path
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["add-one-accretes"] == "pass"
    assert obligation_verdicts(report)["prose-law"] == "law-retained-inconclusive"
    assert "law-inconclusive" in diagnostic_codes(report)


def test_missing_interpreter_spawn_failure_is_operational_error(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(
        tmp_path, "interp", suite_text=SUITE_MISSING_INTERPRETER
    )
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                {
                    "id": "broken-law",
                    "scope": "consumer",
                    "origin": "human",
                    "state": "accepted",
                    "authority": dict(AUTHORITY),
                    "predicate": {
                        "kind": "law",
                        "suite_digest": sha(SUITE_MISSING_INTERPRETER),
                    },
                }
            ]
        ),
    )
    report_path = tmp_path / "interp-out" / "report.json"
    proc = run_check(
        law_request(base_root, base, cand_root, cand, ref), report_path
    )
    assert proc.returncode == 2, proc.stdout
    report = json.loads(report_path.read_text())
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Unknown"
    assert "input-mismatch" in diagnostic_codes(report)


def test_missing_law_invocation_inputs_stay_inconclusive(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(tmp_path, "noinv")
    ref = write_obligations(
        tmp_path, obligations_doc([law_obligation("add-one-law")])
    )
    report_path = tmp_path / "noinv-out" / "report.json"
    proc = run_check(
        check_request_record(base_root, base, cand_root, cand, ref), report_path
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 1
    assert report["assurance"] == "Unknown"
    assert obligation_verdicts(report)["add-one-law"] == "law-retained-inconclusive"
    assert "law-inconclusive" in diagnostic_codes(report)


def test_policy_requiring_proposed_law_yields_unknown_not_error(wild_binary, tmp_path):
    base_root, base, cand_root, cand = law_pair(tmp_path, "proposed")
    ref = write_obligations(
        tmp_path, obligations_doc([proposed_law_obligation("draft-law")])
    )
    report_path = tmp_path / "proposed-out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref, policy={"structural": "accretion", "law": "required"}
        ),
        report_path,
    )
    assert proc.returncode == 1, proc.stdout
    report = json.loads(report_path.read_text())
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Unknown"
    assert "law-inconclusive" in diagnostic_codes(report)
    assert report["diagnostics"] == report["diagnostics"]  # stable, no crash


def test_invocation_commitment_carries_real_bindings_and_sandbox_caps(
    wild_binary, tmp_path
):
    base_root, base, cand_root, cand = law_pair(tmp_path, "commit")
    ref = write_obligations(
        tmp_path, obligations_doc([law_obligation("add-one-law")])
    )
    report, proc = run_law_check(
        law_request(base_root, base, cand_root, cand, ref), tmp_path, "commit-run"
    )
    assert proc.returncode == 0, report.get("diagnostics")
    commitment = report["invocation_commitment"]
    assert commitment["enforcement"] == "local"
    assert commitment["evaluation_time"] == EVAL_TIME
    assert commitment["budgets"] == {"wall_ms": 2000}
    assert commitment["harnesses"] == {HARNESS_REL: sha(HARNESS_TEXT)}
    assert commitment["fixtures"] == {FIXTURE_REL: sha(FIXTURE_TEXT)}
    assert commitment["environment"] == {"seed": 7}
    # enforced sandbox capabilities are recorded, never implied
    sandbox = commitment["sandbox"]
    assert sandbox["enforced"] is True
    assert isinstance(sandbox["landlock_abi"], int) and sandbox["landlock_abi"] >= 1
    assert sandbox["network"] == "denied"
    assert sandbox["writes"] == "denied"
    # the law result binds the actual candidate artifact (bundle commitment
    # computed here independently) and the boundary contract digest
    cand_commitment = "sha256:" + hashlib.sha256(
        json.dumps(
            {rel: sha(text) for rel, text in cand.items()},
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    entry = report["law_methods"][0]
    assert entry["implementation_artifact"] == cand_commitment
    assert entry["contract"] == report["invocation_commitment"]["candidate_facts_digest"]
    assert entry["harness"] == sha(HARNESS_TEXT)
    assert entry["result_digest"].startswith("sha256:")
