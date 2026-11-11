# Purpose: Red-first contract tests for the on_absent: fallible clause
#   (beads wild-adc, change add-on-absent-fallible): a required input slot
#   may declare `on_absent: fallible`, making absence at the slot a normal
#   value outcome the consumer handles instead of a caller violation —
#   "the outside world lacked the fact" is not "my program is broken".
# Responsibilities: Exercise `wild extract`, `wild check`, and the v1
#   accretion checker as subprocesses against constructed bundles, and pin
#   the named scenarios from the spec deltas: (a) an absent input at a
#   declared slot yields a fallible-absence outcome recording the scoped
#   claim, not a caller-violation refusal; (b) the same slot without the
#   clause keeps the incumbent refusal; (c) gaining the clause on a
#   retained input accretes and revoking it breaks; (d) a NEW fallible
#   required slot is still a non-accretion; (e) a substitution introducing
#   a new required input near a fallible slot is still listed (closure
#   integrity unchanged); (f) the static verdict kind set is unchanged —
#   the clause records a scoped tier-1 claim only, and tier-3 observation
#   stays design-only.
# Rationale: Assertions mirror observable records (envelopes, demand
#   entries, contract slots, check-report claims and verdicts, accretion
#   verdict records), never internals. The clause changes absence HANDLING,
#   never closure membership: the slot stays required in demand and closure
#   validation, no new static verdict kind may appear, and nothing here may
#   weaken accretion_monotone for newly introduced required inputs.

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from test_conveys import FORWARDED_CALL, passthrough_bundle
from test_extract import (
    BIN,
    PROVIDER_LIB,
    envelope,
    facts_json,
    request_record,
    run_extract,
    wild_binary,
    write_bundle,
)
from test_scoped_check import check_request_record, run_check

pytestmark = pytest.mark.usefixtures("wild_binary")

# The incumbent demanded-removal candidate: same consumer, provider drops
# the demanded `add_one` — today a definite structural break (removed).
DEMANDED_REMOVED = PROVIDER_LIB.replace(
    "pub fn add_one(x: u32) -> u32 { x + 1 }\n", ""
)

SCALAR = {"shape": "scalar", "name": "integer", "min": 0, "max": 1}


def contract_slot(name: str, polarity: str, extra: dict | None = None) -> dict:
    slot = {
        "name": name,
        "meaning": "m_" + name.replace("::", "_"),
        "polarity": polarity,
        "facet": "api",
        "type": dict(SCALAR),
        "required": True,
        "default": {"present": False},
    }
    if extra:
        slot.update(extra)
    return slot


def contract_doc(slots: list[dict]) -> dict:
    return {
        "schema_version": "1",
        "kind": "contract",
        "slots": sorted(slots, key=lambda s: s["name"]),
    }


def retained_input_doc(clause: bool) -> dict:
    extra = {"on_absent": "fallible"} if clause else None
    return contract_doc(
        [contract_slot("a::in_req", "in", extra), contract_slot("a::out", "out")]
    )


def run_accretes(
    tmp_path: Path, old: dict, new: dict
) -> tuple[subprocess.CompletedProcess[str], dict]:
    old_path = tmp_path / "old.json"
    new_path = tmp_path / "new.json"
    verdict_path = tmp_path / "verdict.json"
    old_path.write_text(json.dumps(old))
    new_path.write_text(json.dumps(new))
    proc = subprocess.run(
        [
            str(BIN),
            "v1",
            "accretes",
            "--old",
            str(old_path),
            "--new",
            str(new_path),
            "--output",
            str(verdict_path),
        ],
        capture_output=True,
        text=True,
    )
    record = json.loads(verdict_path.read_text()) if verdict_path.exists() else {}
    return proc, record


def test_absent_input_at_fallible_slot_is_handled_outcome(tmp_path: Path) -> None:
    # Extraction leg: the consumer's call into an absent external dependency
    # is declared fallible, so the demand records a scoped fallible-absence
    # outcome instead of the caller-violation refusal.
    files = passthrough_bundle(tmp_path / "bundle")
    record = request_record(tmp_path / "bundle", files, on_absent=["extdep"])
    proc = run_extract(record, tmp_path / "facts")
    assert proc.returncode == 0, proc.stdout + proc.stderr
    env = envelope(proc)
    assert env["decision"] == "accept"
    assert env["assurance"] == "PassDeclared"
    report = facts_json(tmp_path / "facts", "report.json")
    assert report["complete_inventory"] is True
    assert not any(d["code"] == "incomplete-demand" for d in report["diagnostics"])
    # the scoped fallible-absence outcome on the demand entry
    demand = facts_json(tmp_path / "facts", "demand.json")
    entries = [e for e in demand["entries"] if e["called"] == FORWARDED_CALL]
    assert len(entries) == 1
    assert entries[0]["on_absent"] == "fallible"
    assert entries[0]["absent"] is True
    assert entries[0]["scope"] == "extdep"
    # the slot STAYS required and the clause lives on the contract slot
    contract = facts_json(tmp_path / "facts", "contract.json")
    in_slots = [s for s in contract["slots"] if s["polarity"] == "in"]
    slot = next(
        s for s in in_slots if s["name"] == "consumer::demand::extdep::probe"
    )
    assert slot["required"] is True
    assert slot["on_absent"] == "fallible"

    # Check leg: the candidate provider drops the demanded `add_one`; with
    # the clause declared the absence is a handled outcome, not the
    # caller-violation removal break.
    base = write_bundle(tmp_path / "base")
    cand = write_bundle(tmp_path / "cand", provider_lib=DEMANDED_REMOVED)
    proc = run_check(
        check_request_record(
            tmp_path / "base", base, tmp_path / "cand", cand, on_absent=["provider"]
        ),
        tmp_path / "report.json",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    env = envelope(proc)
    assert env["decision"] == "accept"
    assert env["assurance"] == "PassDeclared"
    report = json.loads((tmp_path / "report.json").read_text())
    verdicts = {v["called"]: v["verdict"] for v in report["demanded_slots"]}
    assert "provider::add_one" not in verdicts
    assert verdicts["provider::greet"] == "pass"
    # the scoped absence claim records the handled outcome
    assert {
        "side": "candidate",
        "called": "provider::add_one",
        "scope": "provider",
    } in report["absence_claims"]


def test_absent_input_without_clause_still_refuses(tmp_path: Path) -> None:
    # Extraction leg: without the clause the incumbent incomplete-demand
    # refusal for the absent external dependency is preserved.
    files = passthrough_bundle(tmp_path / "bundle")
    record = request_record(tmp_path / "bundle", files)
    proc = run_extract(record, tmp_path / "facts")
    assert proc.returncode == 1, proc.stdout + proc.stderr
    env = envelope(proc)
    assert env["decision"] == "refuse"
    report = facts_json(tmp_path / "facts", "report.json")
    assert report["complete_inventory"] is False
    assert any(d["code"] == "incomplete-demand" for d in report["diagnostics"])
    demand = facts_json(tmp_path / "facts", "demand.json")
    assert not any(e.get("absent") or e.get("on_absent") for e in demand["entries"])

    # Check leg: without the clause the demanded removal keeps the definite
    # caller-violation verdict.
    base = write_bundle(tmp_path / "base")
    cand = write_bundle(tmp_path / "cand", provider_lib=DEMANDED_REMOVED)
    proc = run_check(
        check_request_record(tmp_path / "base", base, tmp_path / "cand", cand),
        tmp_path / "report.json",
    )
    assert proc.returncode == 1, "a demanded removal is a structural counterexample"
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert env["assurance"] == "Reject"
    report = json.loads((tmp_path / "report.json").read_text())
    verdicts = {v["called"]: v["verdict"] for v in report["demanded_slots"]}
    assert verdicts["provider::add_one"] == "removed"
    assert report["absence_claims"] == []


def test_clause_direction_gaining_accretes_losing_breaks(tmp_path: Path) -> None:
    # Gaining `on_absent: fallible` on a retained input widens demand and
    # accretes.
    proc, record = run_accretes(
        tmp_path, retained_input_doc(clause=False), retained_input_doc(clause=True)
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert envelope(proc)["decision"] == "accept"
    assert record["accretes"] is True
    assert record["verdict"] == "holds"

    # Revoking the clause narrows demand and is a break.
    proc, record = run_accretes(
        tmp_path, retained_input_doc(clause=True), retained_input_doc(clause=False)
    )
    assert proc.returncode == 1, "revoking the absence clause narrows demand"
    assert envelope(proc)["decision"] == "refuse"
    assert record["accretes"] is False
    assert record["verdict"] == "breaks"


def test_new_fallible_required_slot_is_still_non_accretion(tmp_path: Path) -> None:
    # A NEW required input slot is a non-accretion even when it declares
    # the clause: accretion_monotone is unchanged.
    old = retained_input_doc(clause=False)
    new = contract_doc(
        retained_input_doc(clause=False)["slots"]
        + [contract_slot("a::new_req", "in", {"on_absent": "fallible"})]
    )
    proc, record = run_accretes(tmp_path, old, new)
    assert proc.returncode == 1, "a new required input breaks accretion"
    assert envelope(proc)["decision"] == "refuse"
    assert record["accretes"] is False
    assert record["verdict"] == "breaks"


def test_fallible_slot_stays_in_closure_validation(tmp_path: Path) -> None:
    # A candidate whose substitution introduces a new required input near a
    # declared fallible slot is still refused and the new input is still
    # listed: the claim never exempts closure validation.
    base = write_bundle(tmp_path / "base")
    cand = passthrough_bundle(tmp_path / "cand")
    proc = run_check(
        check_request_record(
            tmp_path / "base", base, tmp_path / "cand", cand, on_absent=["extdep"]
        ),
        tmp_path / "report.json",
    )
    assert proc.returncode == 1, "a new required input cannot hide behind the clause"
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert env["assurance"] == "Unknown"
    report = json.loads((tmp_path / "report.json").read_text())
    # the newly introduced required input is still listed
    assert any(
        d["severity"] == "error" and FORWARDED_CALL in d["reason"]
        for d in report["diagnostics"]
    )
    # the candidate-side claim is still recorded, scoped to the declared path
    assert {
        "side": "candidate",
        "called": FORWARDED_CALL,
        "scope": "extdep",
    } in report["absence_claims"]
    # the incumbent verdicts are otherwise unchanged
    verdicts = {v["called"]: v["verdict"] for v in report["demanded_slots"]}
    assert verdicts["provider::add_one"] == "pass"
    assert verdicts["provider::greet"] == "pass"


def test_no_new_static_verdict_kind(tmp_path: Path) -> None:
    # The clause records a scoped tier-1 claim only; the static verdict kind
    # set and the report surface are unchanged (tier-3 observation stays
    # design-only: no observation surface exists in the report).
    base = write_bundle(tmp_path / "base")
    cand = write_bundle(tmp_path / "cand", provider_lib=DEMANDED_REMOVED)
    proc = run_check(
        check_request_record(
            tmp_path / "base", base, tmp_path / "cand", cand, on_absent=["provider"]
        ),
        tmp_path / "report.json",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads((tmp_path / "report.json").read_text())
    incumbent_verdicts = {"pass", "removed", "broken", "unknown"}
    used = {v["verdict"] for v in report["demanded_slots"]}
    assert used <= incumbent_verdicts
    assert report["demanded_slots"], "non-claimed slots are still judged"
    # absence is recorded as a scoped claim, never as a verdict kind
    assert report["absence_claims"]
    assert all("verdict" not in claim for claim in report["absence_claims"])
    # the report surface is the incumbent set plus the claim record only
    expected_keys = {
        "version",
        "kind",
        "conveyance_claims",
        "absence_claims",
        "profile",
        "consumer",
        "policy",
        "law_methods",
        "base",
        "candidate",
        "demanded_slots",
        "obligations",
        "obligation_changes",
        "transition",
        "invocation_commitment",
        "disposition",
        "decision",
        "assurance",
        "diagnostics",
    }
    assert set(report.keys()) == expected_keys
