# Purpose: Red-first contract tests for the conveys clause (beads wild-hyk,
#   change add-conveys-clause): a contract may declare a `conveys` clause
#   listing input paths that are forwarded not interpreted, so pass-through
#   components (proxies, pipes, middleware) record a scoped conveyance claim
#   for unknown input slots at declared paths instead of being refused for
#   unextracted demand.
# Responsibilities: Exercise `wild extract` and `wild check` as subprocesses
#   against constructed bundles carrying an unsupplied external-dependency
#   call, and pin the three named scenarios from the spec delta: (a) a
#   conveyed slot at a declared path is claimed, not rejected; (b) an
#   undeclared unknown slot keeps the incumbent refusal; (c) a candidate
#   that introduces a new required input under a conveyed path is still
#   refused and the refusal lists it — scoped_substitution is unchanged.
# Rationale: Assertions mirror observable records (envelopes, extraction
#   report, demand entries, contract slots, check-report diagnostics and
#   claims), never internals. The clause narrows what is interpreted,
#   never what is validated: no test here may weaken the incumbent
#   refusal for uncovered paths or for newly introduced required inputs.

from __future__ import annotations

import json
from pathlib import Path

import pytest

from test_extract import (
    CONSUMER_LIB,
    envelope,
    facts_json,
    request_record,
    run_extract,
    wild_binary,
    write_bundle,
)
from test_scoped_check import check_request_record, run_check

pytestmark = pytest.mark.usefixtures("wild_binary")

# A pass-through consumer: everything the standard fixture does, plus one
# call into an external dependency whose source is absent from the bundle.
FORWARDED_CALL = "extdep::probe"
PASSTHROUGH_LIB = CONSUMER_LIB + "\npub fn forward() -> u32 { extdep::probe(1) }\n"


def passthrough_bundle(root: Path) -> dict[str, str]:
    files = write_bundle(root)
    (root / "consumer/src/lib.rs").write_text(PASSTHROUGH_LIB)
    files["consumer/src/lib.rs"] = PASSTHROUGH_LIB
    toml_text = files["consumer/Cargo.toml"] + 'extdep = "1.0"\n'
    (root / "consumer/Cargo.toml").write_text(toml_text)
    files["consumer/Cargo.toml"] = toml_text
    return files


def test_conveyed_slot_is_claimed_not_rejected(tmp_path: Path) -> None:
    files = passthrough_bundle(tmp_path / "bundle")
    record = request_record(tmp_path / "bundle", files, conveys=["extdep"])
    proc = run_extract(record, tmp_path / "facts")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    env = envelope(proc)
    assert env["decision"] == "accept"
    assert env["assurance"] == "PassDeclared"
    report = facts_json(tmp_path / "facts", "report.json")
    assert report["complete_inventory"] is True
    assert not any(d["code"] == "incomplete-demand" for d in report["diagnostics"])
    # the scoped conveyance claim: the demand entry records the forwarded
    # path and the declared path covering it, not a refusal
    demand = facts_json(tmp_path / "facts", "demand.json")
    entries = [e for e in demand["entries"] if e["called"] == FORWARDED_CALL]
    assert len(entries) == 1
    assert entries[0]["conveyed"] is True
    assert entries[0]["scope"] == "extdep"
    # the forwarded input is still a required (opaque) in-slot: conveyance
    # narrows what is interpreted, never what is validated
    contract = facts_json(tmp_path / "facts", "contract.json")
    in_slots = [s for s in contract["slots"] if s["polarity"] == "in"]
    assert "consumer::demand::extdep::probe" in {s["name"] for s in in_slots}
    assert all(s["required"] is True for s in in_slots)


def test_undeclared_unknown_slot_is_still_refused(tmp_path: Path) -> None:
    files = passthrough_bundle(tmp_path / "bundle")
    # a clause that does not cover the path claims nothing: the incumbent
    # refusal for unextracted demand is preserved unchanged
    record = request_record(tmp_path / "bundle", files, conveys=["unrelated"])
    proc = run_extract(record, tmp_path / "facts")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    env = envelope(proc)
    assert env["decision"] == "refuse"
    report = facts_json(tmp_path / "facts", "report.json")
    assert report["complete_inventory"] is False
    assert any(d["code"] == "incomplete-demand" for d in report["diagnostics"])
    demand = facts_json(tmp_path / "facts", "demand.json")
    assert not any(e.get("conveyed") for e in demand["entries"])


def test_conveyed_path_new_required_input_still_caught(tmp_path: Path) -> None:
    base = write_bundle(tmp_path / "base")
    cand = passthrough_bundle(tmp_path / "cand")
    record = check_request_record(
        tmp_path / "base", base, tmp_path / "cand", cand, conveys=["extdep"]
    )
    proc = run_check(record, tmp_path / "report.json")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    env = envelope(proc)
    # scoped_substitution unchanged: restricting demand never hides the
    # newly introduced required input, so the incumbent verdict class stands
    assert env["decision"] == "refuse"
    assert env["assurance"] == "Unknown"
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["base"]["complete_inventory"] is True
    assert report["candidate"]["complete_inventory"] is True
    # the refusal lists the newly introduced required input
    assert any(
        d["severity"] == "error" and FORWARDED_CALL in d["reason"]
        for d in report["diagnostics"]
    )
    # the candidate-side claim is still recorded, scoped to the declared path
    assert {
        "side": "candidate",
        "called": FORWARDED_CALL,
        "scope": "extdep",
    } in report["conveyance_claims"]
