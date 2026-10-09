# Purpose: Red-first command-level runtime tests for the local extraction
#   slice (beads wild-mh5.1): the `wild extract` CLI against supplied
#   Rust/Cargo bundles under the rust-cargo-local-1 profile.
# Responsibilities: Build the real extractor binary once per session and
#   exercise it as a subprocess against constructed bundles in tempdirs.
#   Pin the named scenario behaviors from the add-local-contract-checking
#   spec deltas: repeated-extraction byte identity, relocation/formatting
#   invariance with distinct raw identities, macro-generated export gaps,
#   changed build input binding refusals, local-1 record refusals
#   (duplicate keys, unknown fields/versions, digest mismatch, out-of-bundle
#   references), demand resolution for direct and aliased calls, and the
#   v1 exit mapping (accept 0 / refuse 1 / error 2). Assert observable
#   records and exit codes, never implementation internals.
# Rationale: The slice's acceptance is a working deterministic extraction
#   workflow whose completeness claims stay honest; synthetic success or
#   assertion mirroring would prove nothing. Written before any
#   implementation exists per the ticket's TDD mandate; every test here
#   must fail red against the absent `wild` binary and stay green
#   unchanged once the slice lands.

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
BIN = REPO / "target" / "debug" / "wild"

PROFILE = "rust-cargo-local-1"

PROVIDER_LIB = """pub fn add_one(x: u32) -> u32 { x + 1 }
pub fn greet(x: u32) -> u32 { x + 2 }
pub fn never_called() -> u32 { 3 }
"""

PROVIDER_TOML = """[package]
name = "provider"
version = "0.1.0"
edition = "2021"
"""

CONSUMER_LIB = """use provider::greet as say_greet;

pub fn call_direct() -> u32 { provider::add_one(1) }
pub fn call_alias() -> u32 { say_greet(2) }
pub fn plain() -> u32 { 7 }
"""

CONSUMER_LIB_FORMATTED = """// reordered and recommented variant of the same declarations
pub fn plain() -> u32 {
    7
}

pub fn call_alias() -> u32 {
    say_greet(2)
}

pub fn call_direct() -> u32 {
    provider::add_one(1)
}

use provider::greet as say_greet;
"""

CONSUMER_TOML = """[package]
name = "consumer"
version = "0.1.0"
edition = "2021"

[dependencies]
provider = { path = "../provider" }
"""

WORKSPACE_TOML = """[workspace]
members = ["consumer", "provider"]
resolver = "2"
"""

LOCK = """version = 3

[[package]]
name = "consumer"
version = "0.1.0"
dependencies = ["provider"]

[[package]]
name = "provider"
version = "0.1.0"
"""


def sha(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode()).hexdigest()


def write_bundle(root: Path, consumer_lib: str = CONSUMER_LIB) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "Cargo.toml": WORKSPACE_TOML,
        "Cargo.lock": LOCK,
        "consumer/Cargo.toml": CONSUMER_TOML,
        "consumer/src/lib.rs": consumer_lib,
        "provider/Cargo.toml": PROVIDER_TOML,
        "provider/src/lib.rs": PROVIDER_LIB,
    }
    for rel, text in files.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    return files


def request_record(root: Path, files: dict[str, str], **overrides) -> dict:
    record = {
        "version": "local-1",
        "kind": "extraction-request",
        "profile": PROFILE,
        "bundle_root": str(root),
        "files": {rel: sha(text) for rel, text in files.items()},
        "target": "x86_64-unknown-linux-gnu",
        "toolchain": "stable",
        "features": [],
        "extractor": {"name": "wild", "digest": sha("wild-extractor-v0")},
    }
    record.update(overrides)
    return record


def run_extract(record: dict, facts: Path) -> subprocess.CompletedProcess[str]:
    facts.parent.mkdir(parents=True, exist_ok=True)
    request_path = facts.parent / "extraction.json"
    request_path.write_text(json.dumps(record))
    try:
        return subprocess.run(
            [str(BIN), "extract", "--request", str(request_path), "--output", str(facts)],
            capture_output=True,
            text=True,
            cwd=REPO,
        )
    except FileNotFoundError:
        pytest.fail(f"wild binary missing at {BIN}; build the extractor first")


def envelope(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def facts_json(facts: Path, name: str) -> dict:
    return json.loads((facts / name).read_text())


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


@pytest.mark.usefixtures("wild_binary")
class TestExtraction:
    def test_three_runs_produce_identical_semantic_bytes(self, tmp_path):
        files = write_bundle(tmp_path / "bundle")
        outputs = []
        for i in range(3):
            proc = run_extract(
                request_record(tmp_path / "bundle", files), tmp_path / f"facts{i}"
            )
            assert proc.returncode == 0, proc.stderr
            outputs.append((tmp_path / f"facts{i}" / "contract.json").read_bytes())
        assert outputs[0] == outputs[1] == outputs[2]

    def test_relocation_and_formatting_preserve_semantic_identity(self, tmp_path):
        files_a = write_bundle(tmp_path / "a")
        files_b = write_bundle(tmp_path / "b-deeper", consumer_lib=CONSUMER_LIB_FORMATTED)
        pa, pb = tmp_path / "fa", tmp_path / "fb"
        ra = run_extract(request_record(tmp_path / "a", files_a), pa)
        rb = run_extract(request_record(tmp_path / "b-deeper", files_b), pb)
        assert ra.returncode == 0, ra.stderr
        assert rb.returncode == 0, rb.stderr
        assert (pa / "contract.json").read_bytes() == (pb / "contract.json").read_bytes()
        prov_a = (pa / "provenance.json").read_bytes()
        prov_b = (pb / "provenance.json").read_bytes()
        assert prov_a != prov_b, "raw provenance must stay location-accurate"
        assert "b-deeper" in prov_b.decode() and "b-deeper" not in prov_a.decode()

    def test_macro_generated_export_is_incomplete_inventory(self, tmp_path):
        macro_lib = CONSUMER_LIB + """
macro_rules! make_export {
    () => { pub fn generated() -> u32 { 9 } };
}
make_export!();
"""
        files = write_bundle(tmp_path / "bundle", consumer_lib=macro_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, f"gap-bearing extraction must refuse: {proc.stdout}"
        env = envelope(proc)
        assert env["decision"] == "refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "unsupported-construct" in codes
        assert "incomplete-demand" in codes
        # the macro-generated export must not be invented as a supported slot
        contract = facts_json(tmp_path / "facts", "contract.json")
        slot_blob = json.dumps(contract)
        assert "generated" not in slot_blob

    def test_changed_build_input_requires_fresh_extraction(self, tmp_path):
        files_a = write_bundle(tmp_path / "a")
        stale_request = request_record(tmp_path / "a", files_a)
        write_bundle(tmp_path / "b", consumer_lib=CONSUMER_LIB_FORMATTED)
        # submit the prior extraction request against the new bundle: the
        # request's bundle_root now addresses b, whose bytes differ from
        # the request's committed file digests
        stale_request["bundle_root"] = str(tmp_path / "b")
        proc = run_extract(stale_request, tmp_path / "facts")
        assert proc.returncode == 2
        env = envelope(proc)
        assert env["decision"] == "refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        codes = {d["code"] for d in report["diagnostics"]}
        assert "input-mismatch" in codes

    def test_demand_resolves_direct_and_alias_calls(self, tmp_path):
        files = write_bundle(tmp_path / "bundle")
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, proc.stderr
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        contract = facts_json(tmp_path / "facts", "contract.json")
        blob = json.dumps(contract)
        assert "add_one" in blob  # demanded provider function is covered in the contract
        assert "never_called" in blob  # unused provider slot still inventoried
        demand = facts_json(tmp_path / "facts", "demand.json")
        demand_blob = json.dumps(demand)
        assert "provider::add_one" in demand_blob
        assert "say_greet" in demand_blob and "provider::greet" in demand_blob

    MALFORMED_MUTATIONS = (
        "duplicate-key",
        "unknown-field",
        "unknown-version",
        "digest-mismatch",
        "out-of-bundle-reference",
    )

    def test_malformed_requests_are_refused(self, tmp_path):
        for mutation in self.MALFORMED_MUTATIONS:
            files = write_bundle(tmp_path / "bundle")
            record = request_record(tmp_path / "bundle", files)
            if mutation == "unknown-field":
                record["surprise"] = True
            elif mutation == "unknown-version":
                record["version"] = "local-2"
            elif mutation == "digest-mismatch":
                record["files"]["consumer/src/lib.rs"] = sha("tampered")
            elif mutation == "out-of-bundle-reference":
                record["files"]["../escape.rs"] = sha("x")
            facts = tmp_path / f"facts-{mutation}"
            facts.parent.mkdir(parents=True, exist_ok=True)
            request_path = tmp_path / f"extraction-{mutation}.json"
            if mutation == "duplicate-key":
                raw = json.dumps(record)
                raw = raw.replace(
                    '"kind": "extraction-request"',
                    '"kind": "extraction-request","kind": "extraction-request"',
                    1,
                )
                request_path.write_text(raw)
            else:
                request_path.write_text(json.dumps(record))
            proc = subprocess.run(
                [str(BIN), "extract", "--request", str(request_path), "--output", str(facts)],
                capture_output=True,
                text=True,
                cwd=REPO,
            )
            assert proc.returncode == 2, f"{mutation} must be an error refusal"
            env = envelope(proc)
            assert env["decision"] == "refuse"
            report = facts_json(facts, "report.json")
            assert report["diagnostics"], f"{mutation} must carry a diagnostic"

    def test_unsupplied_provider_demand_marks_inventory_incomplete(self, tmp_path):
        # a dep-qualified call whose provider source/manifest is not in the
        # bundle must produce an explicit gap, never a silently dropped entry
        ext_lib = CONSUMER_LIB + "\npub fn uses_external() -> u32 { extdep::probe(1) }\n"
        ext_toml = CONSUMER_TOML + 'extdep = "1.0"\n'
        root = tmp_path / "bundle"
        files = write_bundle(root)
        (root / "consumer/src/lib.rs").write_text(ext_lib)
        (root / "consumer/Cargo.toml").write_text(ext_toml)
        files["consumer/src/lib.rs"] = ext_lib
        files["consumer/Cargo.toml"] = ext_toml
        proc = run_extract(request_record(root, files), tmp_path / "facts")
        assert proc.returncode == 1
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_used_vs_unused_removal_divergence(self, tmp_path):
        # removing the unused provider slot keeps the extraction complete;
        # removing a demanded one must diverge into an incomplete-demand refusal
        kept = write_bundle(tmp_path / "kept")
        kept_files = dict(kept)
        kept_lib = PROVIDER_LIB.replace("pub fn never_called() -> u32 { 3 }\n", "")
        (tmp_path / "kept" / "provider/src/lib.rs").write_text(kept_lib)
        kept_files["provider/src/lib.rs"] = kept_lib
        pk = run_extract(request_record(tmp_path / "kept", kept_files), tmp_path / "fk")
        assert pk.returncode == 0, pk.stderr
        kept_report = facts_json(tmp_path / "fk", "report.json")
        assert kept_report["complete_inventory"] is True

        gutted_lib = kept_lib.replace("pub fn add_one(x: u32) -> u32 { x + 1 }\n", "")
        (tmp_path / "kept" / "provider/src/lib.rs").write_text(gutted_lib)
        gutted_files = dict(kept)
        gutted_files["provider/src/lib.rs"] = gutted_lib
        pg = run_extract(
            request_record(tmp_path / "kept", gutted_files), tmp_path / "fg"
        )
        assert pg.returncode == 1, "removing a demanded provider fn must refuse"
        gutted_report = facts_json(tmp_path / "fg", "report.json")
        assert gutted_report["complete_inventory"] is False
        codes = {d["code"] for d in gutted_report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_macro_usage_blocks_complete_claim(self, tmp_path):
        # a macro invocation whose body references a provider fn may introduce
        # usages the parser cannot inventory: the completeness claim must be
        # withheld (scoped refusal), and the hidden call must not count as
        # resolved demand
        hidden_lib = CONSUMER_LIB + """
macro_rules! call_hidden {
    () => { provider::add_one(4) };
}
call_hidden!();
"""
        files = write_bundle(tmp_path / "bundle", consumer_lib=hidden_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, f"hidden usage must refuse completeness: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes
        # the demand that is visible outside the macro body must still resolve
        demand = facts_json(tmp_path / "facts", "demand.json")
        demand_blob = json.dumps(demand)
        assert "provider::add_one" in demand_blob

    def test_unsupported_source_writes_nothing_and_no_network(self, tmp_path):
        files = write_bundle(tmp_path / "bundle")
        before = {rel: (tmp_path / "bundle" / rel).read_bytes() for rel in files}
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, proc.stderr
        after = {rel: (tmp_path / "bundle" / rel).read_bytes() for rel in files}
        assert before == after, "extraction must not write to the source bundle"
