# Purpose: Red-first command-level runtime tests for the protected-context
#   slice (beads wild-mh5.3): accepted obligations live in a trusted external
#   document, candidate edits cannot weaken them, and an externally authorized
#   transition produces an intentional-change disposition.
# Responsibilities: Exercise `wild check` as a subprocess with a trusted
#   obligations reference {digest, path} and optional trusted transition
#   record; pin the named scenarios from the add-local-contract-checking
#   deltas — regeneration cannot erase intent (deleted law stays evaluated,
#   proposed deletion reported separately), candidate edits its own judge
#   (weaker regenerated contracts, reduced demand, policy/checker changes
#   cannot lift failures), authorized bug-fix transition yields
#   accepted-intentional-change with affected consumers recorded (not
#   backward-compatible success), retained laws without execution evidence
#   stay law-inconclusive unknown, obligations digest mismatch and malformed
#   records are error-class refusals, and the report honestly labels local
#   (non-CI) enforcement with explicit nulls for deferred commitment fields.
# Rationale: Acceptance is an honest protected-context verdict whose
#   unauthorized-weakening refusals survive separate runs; every test asserts
#   observable records and exit codes, never implementation internals.
#   Written red against the mh5.2 binary (which refuses any non-null
#   obligations reference) and must stay green unchanged once this slice
#   lands.

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from test_extract import (
    BIN,
    CONSUMER_LIB,
    PROFILE,
    PROVIDER_LIB,
    REPO,
    sha,
    write_bundle,
)

CHECKER = {"name": "wild", "digest": sha("wild-extractor-v0")}
POLICY = {"structural": "accretion"}
AUTHORITY = {"name": "project-lead", "digest": sha("authority:project-lead")}

U32 = {"shape": "scalar", "name": "integer", "min": 0, "max": 4294967295}
LAW_TEXT = "law: add_one output stays within base bounds for all u32 inputs\n"


def canonical(record: dict) -> str:
    return json.dumps(record, sort_keys=True, separators=(",", ":"))


def fn_type(args: list, result: dict) -> dict:
    return {"shape": "function", "arguments": args, "result": result}


def contract(slots: list[dict]) -> dict:
    return {
        "schema_version": "1",
        "kind": "contract",
        "slots": slots,
        "tombstones": [],
        "laws": [],
        "relations": [],
        "sunsets": [],
    }


def slot(name: str, ty: dict, meaning: str = "public function", polarity: str = "out") -> dict:
    return {
        "name": name,
        "meaning": meaning,
        "polarity": polarity,
        "facet": "api",
        "type": ty,
        "required": True,
        "default": {"present": False},
    }


# The base provider contract the obligations are authored against: add_one
# is the demanded slot this slice's scenarios bind.
BASE_OBLIGATION_CONTRACT = contract(
    [slot("provider::add_one", fn_type([U32], U32), "public function")]
)


def obligation(id: str, predicate: dict | None = None) -> dict:
    """An accepted human-origin obligation on the default consumer scope."""
    if predicate is None:
        predicate = {
            "kind": "structural",
            "digest": sha(canonical(BASE_OBLIGATION_CONTRACT)),
            "contract": BASE_OBLIGATION_CONTRACT,
        }
    return _obligation(id, "human", "accepted", predicate)


def proposed_obligation(id: str, predicate: dict | None = None) -> dict:
    """A proposed (draft) obligation: reported, never enforced."""
    if predicate is None:
        predicate = {
            "kind": "structural",
            "digest": sha(canonical(BASE_OBLIGATION_CONTRACT)),
            "contract": BASE_OBLIGATION_CONTRACT,
        }
    return _obligation(id, "human", "proposed", predicate)


def agent_obligation(id: str, predicate: dict | None = None) -> dict:
    """An accepted agent-origin obligation on the default consumer scope."""
    if predicate is None:
        predicate = {
            "kind": "structural",
            "digest": sha(canonical(BASE_OBLIGATION_CONTRACT)),
            "contract": BASE_OBLIGATION_CONTRACT,
        }
    return _obligation(id, "agent", "accepted", predicate)


def _obligation(id: str, origin: str, state: str, predicate: dict) -> dict:
    return {
        "id": id,
        "scope": "consumer",
        "origin": origin,
        "state": state,
        "authority": dict(AUTHORITY),
        "predicate": predicate,
    }


def obligations_doc(records: list[dict]) -> dict:
    return {"version": "local-1", "kind": "obligations", "obligations": records}


def write_obligations(root: Path, doc: dict, name: str = "obligations.json") -> dict:
    """Write the obligations document; return the trusted reference object."""
    root.mkdir(parents=True, exist_ok=True)
    path = root / name
    path.write_text(json.dumps(doc))
    return {"digest": sha(json.dumps(doc)), "path": str(path)}


def transition_record(old: str, new: str) -> dict:
    return {
        "old_digest": old,
        "new_digest": new,
        "reason": "authorized bug fix changes the old obligation",
        "affected_consumers": ["consumer"],
        "authority": dict(AUTHORITY),
    }


def check_request_record(
    base_root: Path,
    base_files: dict[str, str],
    cand_root: Path,
    cand_files: dict[str, str],
    obligations_ref: dict | None,
    **overrides,
) -> dict:
    record = {
        "version": "local-1",
        "kind": "check-request",
        "profile": PROFILE,
        "consumer": "consumer",
        "base": {
            "bundle_root": str(base_root),
            "files": {rel: sha(text) for rel, text in base_files.items()},
        },
        "candidate": {
            "bundle_root": str(cand_root),
            "files": {rel: sha(text) for rel, text in cand_files.items()},
        },
        "target": "x86_64-unknown-linux-gnu",
        "toolchain": "stable",
        "features": [],
        "policy": POLICY,
        "obligations": obligations_ref,
        "checker": CHECKER,
    }
    record.update(overrides)
    return record


def bundle_with_law(
    root: Path,
    provider_lib: str = PROVIDER_LIB,
    consumer_lib: str = CONSUMER_LIB,
) -> dict[str, str]:
    """A standard bundle plus one committed law-suite artifact."""
    files = write_bundle(root, consumer_lib=consumer_lib)
    if provider_lib != PROVIDER_LIB:
        (root / "provider/src/lib.rs").write_text(provider_lib)
        files["provider/src/lib.rs"] = provider_lib
    law_rel = "provider/tests/law_add_one.wildlaw"
    (root / law_rel).parent.mkdir(parents=True, exist_ok=True)
    (root / law_rel).write_text(LAW_TEXT)
    files[law_rel] = LAW_TEXT
    return files


def run_check(record: dict, report_path: Path) -> subprocess.CompletedProcess[str]:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    request_path = report_path.parent / "check.json"
    request_path.write_text(json.dumps(record))
    try:
        return subprocess.run(
            [str(BIN), "check", "--request", str(request_path), "--format", "json",
             "--report", str(report_path)],
            capture_output=True,
            text=True,
            cwd=REPO,
        )
    except FileNotFoundError:
        pytest.fail(f"wild binary missing at {BIN}; build the extractor first")


def load_report(proc: subprocess.CompletedProcess[str], report_path: Path) -> dict:
    assert proc.returncode in (0, 1, 2), f"unexpected failure: {proc.stderr[-800:]}"
    assert report_path.exists(), "check must write the requested report"
    return json.loads(report_path.read_text())


def diagnostic_codes(report: dict) -> set[str]:
    return {d["code"] for d in report.get("diagnostics", [])}


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


def bundle_pair(tmp_path: Path, name: str, **kwargs) -> tuple[Path, dict]:
    """A bundle root plus its committed files, including the law artifact."""
    root = tmp_path / name
    return root, bundle_with_law(root, **kwargs)


def test_accepted_structural_obligation_accreting_candidate_accepts(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 0, report.get("diagnostics")
    assert report["decision"] == "accept"
    assert report["disposition"] == "compatible"
    verdicts = {o["id"]: o["verdict"] for o in report["obligations"]}
    assert verdicts["add-one-accretes"] == "pass"


def test_deleted_law_is_still_evaluated_and_reported_as_proposed_deletion(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    # candidate regenerates its contracts without carrying the law artifact
    cand_root = tmp_path / "candidate"
    cand_files = write_bundle(cand_root)
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                obligation(
                    "regression-law",
                    predicate={"kind": "law", "suite_digest": sha(LAW_TEXT)},
                )
            ]
        ),
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand_files, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Reject"
    assert "obligation-change" in diagnostic_codes(report)
    verdicts = {o["id"]: o["verdict"] for o in report["obligations"]}
    assert verdicts["regression-law"] == "law-deleted"
    changes = report["obligation_changes"]
    assert any(c["id"] == "regression-law" and c["change"] == "proposed-deletion"
               for c in changes), changes


def test_retained_law_without_execution_evidence_stays_law_inconclusive(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")  # law retained
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                obligation(
                    "regression-law",
                    predicate={"kind": "law", "suite_digest": sha(LAW_TEXT)},
                )
            ]
        ),
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Unknown"
    assert "law-inconclusive" in diagnostic_codes(report)
    verdicts = {o["id"]: o["verdict"] for o in report["obligations"]}
    assert verdicts["regression-law"] == "law-retained-inconclusive"
    # the retained law is never silently skipped and never a fabricated pass
    assert report["decision"] != "accept"


def test_regenerated_weaker_contract_cannot_erase_intent(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    # candidate weakens the bound slot: narrowed parameter domain
    weak_provider = PROVIDER_LIB.replace(
        "pub fn add_one(x: u32) -> u32 { x + 1 }",
        "pub fn add_one(x: u16) -> u32 { x as u32 + 1 }",
    )
    cand_root, cand_files = bundle_pair(tmp_path, "candidate", provider_lib=weak_provider)
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand_files, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Reject"
    assert "obligation-change" in diagnostic_codes(report)
    verdicts = {o["id"]: o["verdict"] for o in report["obligations"]}
    assert verdicts["add-one-accretes"] == "weakened"
    changes = report["obligation_changes"]
    assert any(c["id"] == "add-one-accretes" for c in changes), changes


def test_candidate_demand_reduction_cannot_remove_obligation_coverage(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    # candidate consumer stops calling the bound slot; the accepted
    # obligation keeps the slot covered regardless of candidate demand
    narrowed_consumer = CONSUMER_LIB.replace(
        "pub fn call_direct() -> u32 { provider::add_one(1) }\n", ""
    )
    cand_files = bundle_pair(tmp_path, "candidate", consumer_lib=narrowed_consumer)[1]
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand_files, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 0, report.get("diagnostics")
    assert report["decision"] == "accept"
    # the obligation was still evaluated, not dropped with the demand
    verdicts = {o["id"]: o["verdict"] for o in report["obligations"]}
    assert verdicts["add-one-accretes"] == "pass"


def test_candidate_supplied_context_selects_nothing(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    # the candidate bundle carries its own weaker policy/checker artifacts;
    # the trusted request context must win and those bytes stay inert
    cand_root, cand_files = bundle_pair(tmp_path, "candidate")
    (tmp_path / "candidate" / "wild-policy.json").write_text(
        json.dumps({"structural": "equality"})
    )
    (tmp_path / "candidate" / "wild-checker.json").write_text(
        json.dumps({"name": "candidate-checker", "digest": sha("rogue")})
    )
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand_files, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 0, report.get("diagnostics")
    assert report["decision"] == "accept"
    assert report["invocation_commitment"]["policy"] == POLICY
    assert report["invocation_commitment"]["checker_digest"] == CHECKER["digest"]


def test_authorized_transition_yields_intentional_change_disposition(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    # bug fix changes the bound slot's result type (u32 -> i32: signed
    # error codes); an external authority accepted the old-to-new transition
    # and the obligations doc carries the new state
    I32 = {"shape": "scalar", "name": "integer", "min": -2147483648, "max": 2147483647}
    fixed_provider = PROVIDER_LIB.replace(
        "pub fn add_one(x: u32) -> u32 { x + 1 }",
        "pub fn add_one(x: u32) -> i32 { x as i32 + 1 }",
    )
    cand_root, cand_files = bundle_pair(tmp_path, "candidate", provider_lib=fixed_provider)
    new_contract = contract([slot("provider::add_one", fn_type([U32], I32), "public function")])
    new_predicate_digest = sha(canonical(new_contract))
    old_digest = sha(canonical(BASE_OBLIGATION_CONTRACT))
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                obligation(
                    "add-one-fixed",
                    predicate={
                        "kind": "structural",
                        "digest": new_predicate_digest,
                        "contract": new_contract,
                    },
                )
            ]
        ),
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand_files, ref,
            transition=transition_record(old_digest, new_predicate_digest),
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 0, report.get("diagnostics")
    assert report["decision"] == "accept"
    # intentional change, NOT backward-compatible success
    assert report["disposition"] == "accepted-intentional-change"
    assert report["transition"]["old_digest"] == old_digest
    assert report["transition"]["new_digest"] == new_predicate_digest
    assert report["transition"]["affected_consumers"] == ["consumer"]


def test_unauthorized_type_change_without_transition_refuses(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    fixed_provider = PROVIDER_LIB.replace(
        "pub fn add_one(x: u32) -> u32 { x + 1 }",
        "pub fn add_one(x: u32) -> i32 { x as i32 + 1 }",
    )
    cand_root, cand_files = bundle_pair(tmp_path, "candidate", provider_lib=fixed_provider)
    # no transition record: the same change is an unauthorized weakening
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand_files, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 1
    assert report["decision"] == "refuse"
    assert report["assurance"] == "Reject"
    assert "obligation-change" in diagnostic_codes(report)


def test_proposed_state_obligations_are_not_enforced_but_reported(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    proposed = proposed_obligation("future-law")
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes"), proposed])
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 0, report.get("diagnostics")
    states = {o["id"]: o["state"] for o in report["obligations"]}
    assert states["future-law"] == "proposed"
    assert states["add-one-accretes"] == "accepted"


def test_malformed_obligations_documents_are_error_class(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    # digest mismatch: the document bytes do not hash to the trusted digest
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    (tmp_path / "obligations.json").write_text(
        json.dumps(obligations_doc([]))  # different content, same reference
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    assert proc.returncode == 2
    envelope = json.loads(proc.stdout)
    assert envelope["decision"] == "refuse"


def test_malformed_obligation_record_is_error_class(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    bad = obligation("add-one-accretes")
    bad["origin"] = "compiler"  # unknown origin label
    ref = write_obligations(tmp_path, obligations_doc([bad]))
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    assert proc.returncode == 2


def test_transition_mismatch_is_error_class(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    report_path = tmp_path / "out" / "report.json"
    # the transition names a replacement no accepted obligation carries
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref,
            transition=transition_record(
                sha(canonical(BASE_OBLIGATION_CONTRACT)), sha("no-such-replacement")
            ),
        ),
        report_path,
    )
    assert proc.returncode == 2


def test_report_labels_local_enforcement_with_explicit_nulls(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    ref = write_obligations(
        tmp_path, obligations_doc([obligation("add-one-accretes")])
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    commitment = report["invocation_commitment"]
    assert commitment["enforcement"] == "local"
    assert commitment["obligations_digest"] == ref["digest"]
    assert commitment["harnesses"] is None
    assert commitment["fixtures"] is None
    assert commitment["budgets"] is None
    assert commitment["evaluation_time"] is None
    report_text = report_path.read_text()
    assert "independently enforced" not in report_text
    assert "independent CI enforcement" not in report_text


def test_origin_provenance_is_preserved_in_the_report(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    ref = write_obligations(
        tmp_path,
        obligations_doc(
            [
                obligation("human-law"),
                agent_obligation("agent-law"),
            ]
        ),
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    report = load_report(proc, report_path)
    assert proc.returncode == 0, report.get("diagnostics")
    origins = {o["id"]: o["origin"] for o in report["obligations"]}
    assert origins == {"human-law": "human", "agent-law": "agent"}


def test_duplicate_obligation_ids_are_error_class(
    wild_binary, tmp_path
):
    base_root, base = bundle_pair(tmp_path, "base")
    cand_root, cand = bundle_pair(tmp_path, "candidate")
    ref = write_obligations(
        tmp_path,
        obligations_doc([obligation("dup"), obligation("dup")]),
    )
    report_path = tmp_path / "out" / "report.json"
    proc = run_check(
        check_request_record(
            base_root, base, cand_root, cand, ref
        ),
        report_path,
    )
    assert proc.returncode == 2
