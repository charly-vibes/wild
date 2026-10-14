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


def write_bundle(
    root: Path, consumer_lib: str = CONSUMER_LIB, provider_lib: str = PROVIDER_LIB
) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "Cargo.toml": WORKSPACE_TOML,
        "Cargo.lock": LOCK,
        "consumer/Cargo.toml": CONSUMER_TOML,
        "consumer/src/lib.rs": consumer_lib,
        "provider/Cargo.toml": PROVIDER_TOML,
        "provider/src/lib.rs": provider_lib,
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

    def test_public_fn_with_non_scalar_return_is_opaque_gap_not_panic(self, tmp_path):
        # beads wild-73j: shape_supported in visit_item_fn did not gate on the
        # return type, so a public fn returning Vec<u32> reached
        # result_ok.expect("unit fallback") and panicked exit 101. The honest
        # behavior mirrors the args_ok else-branch: an unsupported-construct
        # gap plus an opaque slot, never a panic and never an invented
        # function-type slot.
        provider_lib = """pub fn add_one(x: u32) -> u32 { x + 1 }
pub fn make_vec(x: u32) -> Vec<u32> { vec![x] }
"""
        files = write_bundle(tmp_path / "bundle", provider_lib=provider_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, (
            f"non-scalar return must be a refusal, not a panic: "
            f"rc={proc.returncode} stderr={proc.stderr[-500:]}"
        )
        env = envelope(proc)
        assert env["decision"] == "refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "unsupported-construct" in codes
        contract = facts_json(tmp_path / "facts", "contract.json")
        slots = {s["name"]: s for s in contract["slots"]}
        vec_slot = slots.get("provider::make_vec")
        assert vec_slot is not None, "fn must still surface as an opaque slot"
        assert vec_slot["type"]["shape"] == "opaque"
        # the supported fn beside it keeps its genuine function type
        assert slots["provider::add_one"]["type"]["shape"] == "function"

    def test_string_signature_types_become_function_slots(self, tmp_path):
        # beads wild-7e9: &str, String, and &String in public fn signatures
        # are supported scalar text types — String maps to text-owned, while
        # &str and &String normalize to text-borrowed (deref coercion is
        # standard Rust semantics, not a widening) — so text-taking public
        # fns surface genuine function-type slots instead of
        # unsupported-construct opaque gaps. Text is unbounded, so the
        # scalars carry no min/max fields (boolean precedent).
        # todo!() bodies: the whitelisted argument-confined macro (m7f)
        # records no demands, so the fixture isolates the signature subset.
        provider_lib = '''pub fn shout(x: &str) -> String { todo!() }
pub fn owned_len(s: String) -> u32 { todo!() }
pub fn alias_len(s: &String) -> u32 { todo!() }
'''
        consumer_lib = "pub fn plain() -> u32 { 7 }\n"
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=consumer_lib, provider_lib=provider_lib
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, (
            f"text-taking public fns must extract, not refuse: "
            f"rc={proc.returncode} stderr={proc.stderr[-500:]}"
        )
        env = envelope(proc)
        assert env["decision"] == "accept"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        contract = facts_json(tmp_path / "facts", "contract.json")
        slots = {s["name"]: s for s in contract["slots"]}
        shout = slots["provider::shout"]["type"]
        assert shout["shape"] == "function"
        assert shout["arguments"] == [{"shape": "scalar", "name": "text-borrowed"}]
        assert shout["result"] == {"shape": "scalar", "name": "text-owned"}
        owned = slots["provider::owned_len"]["type"]
        assert owned["shape"] == "function"
        assert owned["arguments"] == [{"shape": "scalar", "name": "text-owned"}]
        assert owned["result"]["shape"] == "scalar"
        assert owned["result"]["name"] == "integer"
        assert "min" in owned["result"] and "max" in owned["result"]
        alias = slots["provider::alias_len"]["type"]
        assert alias["shape"] == "function"
        # deref coercion normalizes &String to the borrowed-text scalar
        assert alias["arguments"] == [{"shape": "scalar", "name": "text-borrowed"}]

    def test_mutable_text_borrow_stays_unsupported(self, tmp_path):
        # beads wild-7e9 (D2): mutable text borrows are outside the v1
        # value-transfer model — &mut str keeps the unsupported-construct
        # refusal and an opaque slot, never a text scalar.
        provider_lib = "pub fn mut_len(s: &mut str) -> u32 { todo!() }\n"
        consumer_lib = "pub fn plain() -> u32 { 7 }\n"
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=consumer_lib, provider_lib=provider_lib
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, (
            f"&mut str must stay a refusal, not a panic: "
            f"rc={proc.returncode} stderr={proc.stderr[-500:]}"
        )
        env = envelope(proc)
        assert env["decision"] == "refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "unsupported-construct" in codes
        contract = facts_json(tmp_path / "facts", "contract.json")
        slots = {s["name"]: s for s in contract["slots"]}
        mut_slot = slots.get("provider::mut_len")
        assert mut_slot is not None, "fn must still surface as an opaque slot"
        assert mut_slot["type"]["shape"] == "opaque"

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

    def test_non_inline_module_public_fn_is_inventoried(self, tmp_path):
        # beads wild-cdp.4: the rung-1 adopt audit measured 11/11 testaruda
        # release pairs abstaining because release crates declare their
        # public API via non-inline modules (`pub mod x;` + src/x.rs) and the
        # extractor walked only src/lib.rs. Mod-path resolution must make
        # the verdict computable: the resolved module file's public fns
        # become genuine inventory slots and dep-qualified calls into them
        # resolve as demand — never fabricated, never silently dropped.
        provider_lib = """pub mod inner;

pub fn add_one(x: u32) -> u32 { x + 1 }
pub fn greet(x: u32) -> u32 { x + 2 }
"""
        consumer_lib = CONSUMER_LIB + """
pub fn call_inner() -> u32 { provider::inner::ping(1) }
"""
        files = write_bundle(tmp_path / "bundle", consumer_lib=consumer_lib, provider_lib=provider_lib)
        files["provider/src/inner.rs"] = "pub fn ping(x: u32) -> u32 { x }\n"
        (tmp_path / "bundle/provider/src/inner.rs").write_text(files["provider/src/inner.rs"])
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, proc.stderr
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        contract = facts_json(tmp_path / "facts", "contract.json")
        slots = {s["name"]: s for s in contract["slots"]}
        assert slots["provider::inner::ping"]["type"]["shape"] == "function"
        demand = facts_json(tmp_path / "facts", "demand.json")
        assert "provider::inner::ping" in json.dumps(demand)

    def test_non_inline_module_missing_file_stays_incomplete(self, tmp_path):
        # beads wild-cdp.4: when the module file is absent from the bundle
        # the gap must remain (gaps uncure silently): the inventory stays
        # incomplete and the diagnostic names the unresolved module.
        provider_lib = """pub mod ghost;

pub fn add_one(x: u32) -> u32 { x + 1 }
pub fn greet(x: u32) -> u32 { x + 2 }
"""
        files = write_bundle(tmp_path / "bundle", provider_lib=provider_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, f"gap-bearing extraction must refuse: {proc.stdout}"
        env = envelope(proc)
        assert env["decision"] == "refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "unsupported-construct" in codes
        assert any("ghost" in d.get("reason", "") for d in report["diagnostics"]), (
            "diagnostic must name the unresolved module"
        )

    def test_nested_and_mod_rs_module_files_resolve(self, tmp_path):
        # beads wild-cdp.4: resolution must be recursive and cover both
        # module-file conventions — src/name.rs (with nested
        # src/name/deep.rs inside it) and src/name/mod.rs.
        provider_lib = """pub mod outer;
pub mod widget;

pub fn add_one(x: u32) -> u32 { x + 1 }
pub fn greet(x: u32) -> u32 { x + 2 }
"""
        files = write_bundle(tmp_path / "bundle", provider_lib=provider_lib)
        extra = {
            "provider/src/outer.rs": "pub mod deep;\n\npub fn level() -> u32 { 1 }\n",
            "provider/src/outer/deep.rs": "pub fn deep_fn(x: u32) -> u32 { x }\n",
            "provider/src/widget/mod.rs": "pub fn spin() -> u32 { 2 }\n",
        }
        files.update(extra)
        for rel, text in extra.items():
            (tmp_path / "bundle" / rel).parent.mkdir(parents=True, exist_ok=True)
            (tmp_path / "bundle" / rel).write_text(text)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, proc.stderr
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        contract = facts_json(tmp_path / "facts", "contract.json")
        slot_names = {s["name"] for s in contract["slots"]}
        assert "provider::outer::level" in slot_names
        assert "provider::outer::deep::deep_fn" in slot_names
        assert "provider::widget::spin" in slot_names

    def test_private_non_inline_module_has_no_public_surface(self, tmp_path):
        # beads wild-cdp.4: a private non-inline module carries no public
        # API surface, exactly like a private inline module — resolving or
        # skipping it must emit no slot and no gap.
        provider_lib = """mod secret;

pub fn add_one(x: u32) -> u32 { x + 1 }
pub fn greet(x: u32) -> u32 { x + 2 }
"""
        files = write_bundle(tmp_path / "bundle", provider_lib=provider_lib)
        files["provider/src/secret.rs"] = "pub fn hidden(x: u32) -> u32 { x }\n"
        (tmp_path / "bundle/provider/src/secret.rs").write_text(files["provider/src/secret.rs"])
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, proc.stderr
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        contract = facts_json(tmp_path / "facts", "contract.json")
        assert "hidden" not in json.dumps(contract)

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

    # argument-confined std macro support (add-std-macro-demand-support)
    # test shape defined in the change design.md before implementation.
    # RED-phase position amendment: macro invocations in STATEMENT position
    # (syn Stmt::Macro) are the default under test — the incumbent walker
    # never visits them (silent acceptance, arguments not descended, demands
    # inside not recorded). Expression position keeps today's visit and is
    # covered as a refusal guard. Provider references sit ONLY inside the
    # macro under test so demand assertions cannot be satisfied spuriously
    # by surrounding direct calls. Bundles avoid non-scalar public fn
    # returns (wild-73j panic bug, out of scope here).

    def test_whitelisted_std_macro_does_not_block_complete_claim(self, tmp_path):
        # (a) a statement-position println! alongside a direct provider call
        # yields no incomplete-demand from the std macro; the provider call
        # still resolves and the extraction stays complete
        print_lib = CONSUMER_LIB + 'pub fn with_print() -> u32 { println!("v={}", 1); 7 }\n'
        files = write_bundle(tmp_path / "bundle", consumer_lib=print_lib)
        for i in range(2):
            proc = run_extract(
                request_record(tmp_path / "bundle", files), tmp_path / f"facts{i}"
            )
            assert proc.returncode == 0, f"std macro must not refuse: {proc.stdout}"
            report = facts_json(tmp_path / f"facts{i}", "report.json")
            assert report["complete_inventory"] is True
            assert report["diagnostics"] == []
        # determinism gate unchanged: repeated extraction yields identical
        # contract bytes with the std macro present
        contract = (tmp_path / "facts0" / "contract.json").read_bytes()
        assert (tmp_path / "facts1" / "contract.json").read_bytes() == contract
        demand = facts_json(tmp_path / "facts0", "demand.json")
        assert "provider::add_one" in json.dumps(demand)

    def test_statement_macro_arguments_record_demands_like_direct_calls(self, tmp_path):
        # (b) a statement-position whitelisted macro whose arguments are the
        # ONLY consumer references to provider functions records demands for
        # those functions like direct calls
        assert_lib = (
            "pub fn assert_both() -> u32 {"
            " assert_eq!(provider::add_one(1), provider::greet(2)); 7 }\n"
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=assert_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, f"argument demands must resolve: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        demand = facts_json(tmp_path / "facts", "demand.json")
        demand_blob = json.dumps(demand)
        assert "provider::add_one" in demand_blob
        assert "provider::greet" in demand_blob

    def test_expression_position_whitelisted_macro_descends_arguments(self, tmp_path):
        # (c) an expression-position whitelisted macro whose arguments
        # reference a provider function records that demand like a direct
        # call instead of refusing the whole invocation
        fmt_lib = (
            'pub fn with_format() -> u32 { let msg = format!("{}", provider::add_one(1)); 7 }\n'
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=fmt_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, f"expression descent must support: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        demand = facts_json(tmp_path / "facts", "demand.json")
        assert "provider::add_one" in json.dumps(demand)

    def test_nested_macro_inside_whitelisted_args_retains_gap(self, tmp_path):
        # (d) refusal composes: a nested macro inside a whitelisted macro's
        # arguments keeps the incomplete-demand disclosure
        nested_lib = CONSUMER_LIB + 'pub fn nested() -> u32 { println!("{}", foo!()); 7 }\n'
        files = write_bundle(tmp_path / "bundle", consumer_lib=nested_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "nested unsupported macro must refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_statement_position_non_whitelisted_macro_retains_gap(self, tmp_path):
        # (e) a statement-position macro outside the whitelist must keep the
        # refusal, not be silently skipped as the incumbent does today
        vec_lib = CONSUMER_LIB + "pub fn with_vec() -> u32 { vec![1, 2]; 7 }\n"
        files = write_bundle(tmp_path / "bundle", consumer_lib=vec_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "non-whitelisted statement macro must refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_expression_position_non_whitelisted_macro_retains_gap(self, tmp_path):
        # (f) an expression-position macro outside the whitelist keeps the
        # refusal (regression guard for today's visit_expr_macro behavior)
        vec_lib = CONSUMER_LIB + "pub fn with_vec() -> u32 { let v = vec![1, 2]; 7 }\n"
        files = write_bundle(tmp_path / "bundle", consumer_lib=vec_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "non-whitelisted expression macro must refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_unparseable_whitelisted_head_retains_gap(self, tmp_path):
        # (g) a whitelisted head whose tokens do not parse as a
        # comma-separated expression list keeps the refusal — never guess
        bad_lib = CONSUMER_LIB + "pub fn unparseable() -> u32 { println!(a; b); 7 }\n"
        files = write_bundle(tmp_path / "bundle", consumer_lib=bad_lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "unparseable whitelisted head must refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_relocation_and_formatting_preserve_semantic_identity_with_macro(self, tmp_path):
        # the determinism split must survive macro descent: the demand walk
        # inside whitelisted macro arguments is name-based; locations (which
        # stay location-accurate, including macro-arg call sites) live only
        # in provenance
        lib_a = (
            "pub fn f() -> u32 {"
            " assert_eq!(provider::add_one(1), provider::greet(2)); 7 }\n"
        )
        lib_b = (
            "pub fn f() -> u32 {\n"
            "    // reformatted variant of the same code\n"
            "    assert_eq!(\n"
            "        provider::add_one(1),\n"
            "        provider::greet(2),\n"
            "    );\n"
            "    7\n"
            "}\n"
        )
        files_a = write_bundle(tmp_path / "a", consumer_lib=lib_a)
        files_b = write_bundle(tmp_path / "b-deeper", consumer_lib=lib_b)
        pa, pb = tmp_path / "fa", tmp_path / "fb"
        ra = run_extract(request_record(tmp_path / "a", files_a), pa)
        rb = run_extract(request_record(tmp_path / "b-deeper", files_b), pb)
        assert ra.returncode == 0, ra.stderr
        assert rb.returncode == 0, rb.stderr
        assert (pa / "contract.json").read_bytes() == (pb / "contract.json").read_bytes()
        prov_a = (pa / "provenance.json").read_bytes()
        prov_b = (pb / "provenance.json").read_bytes()
        assert prov_a != prov_b, "raw provenance must stay location-accurate"

    def test_unsupported_source_writes_nothing_and_no_network(self, tmp_path):
        files = write_bundle(tmp_path / "bundle")
        before = {rel: (tmp_path / "bundle" / rel).read_bytes() for rel in files}
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, proc.stderr
        after = {rel: (tmp_path / "bundle" / rel).read_bytes() for rel in files}
        assert before == after, "extraction must not write to the source bundle"

    # format_args! demand support + format-capture disclosure
    # (add-format-args-demand-support, bd wild-1gm). The routed receiver is a
    # free function taking std::fmt::Arguments — every method call is already
    # gapped by the walker, so a method-call route would mask the macro
    # behavior. The provider fixture carries a pub const because provider
    # VALUE items are the capture hole: fn items implement no formatting
    # traits (compiler-refused) and fn-pointer flow via path expressions is
    # already disclosed by visit_expr_path.

    PROVIDER_WITH_CONST = PROVIDER_LIB + "pub const MAX: u32 = 42;\n"

    def test_format_args_does_not_block_complete_claim(self, tmp_path):
        # (a) routed format_args! with positional literal args alongside a
        # direct provider call: no incomplete-demand from the macro, the
        # provider call still resolves, extraction stays complete
        lib = (
            "fn take_args(a: std::fmt::Arguments) -> u32 { 7 }\n"
            + CONSUMER_LIB
            + "pub fn routed() -> u32 { take_args(format_args!(\"hello {}\", \"world\")); provider::add_one(1) }\n"
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=lib)
        for i in range(2):
            proc = run_extract(
                request_record(tmp_path / "bundle", files), tmp_path / f"facts{i}"
            )
            assert proc.returncode == 0, f"format_args must not refuse: {proc.stdout}"
            report = facts_json(tmp_path / f"facts{i}", "report.json")
            assert report["complete_inventory"] is True
            assert report["diagnostics"] == []
        contract = (tmp_path / "facts0" / "contract.json").read_bytes()
        assert (tmp_path / "facts1" / "contract.json").read_bytes() == contract
        demand = facts_json(tmp_path / "facts0", "demand.json")
        assert "provider::add_one" in json.dumps(demand)

    def test_format_args_arguments_record_demands_like_direct_calls(self, tmp_path):
        # (b) a provider call inside format_args! positional arguments is the
        # ONLY reference to that provider fn; the demand is recorded like a
        # direct call
        lib = (
            "fn take_args(a: std::fmt::Arguments) -> u32 { 7 }\n"
            + CONSUMER_LIB
            + "pub fn routed() -> u32 { take_args(format_args!(\"v={} plus {}\", provider::add_one(1), 2)); 7 }\n"
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, f"argument demands must resolve: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        demand = facts_json(tmp_path / "facts", "demand.json")
        assert "provider::add_one" in json.dumps(demand)

    def test_format_args_named_argument_values_record_demands(self, tmp_path):
        # (c) a provider call inside a named-argument value (`x = expr` parses
        # as Expr::Assign, probe-corrected) is descended and recorded like a
        # direct call — refusing it would invent incompleteness
        lib = (
            "fn take_args(a: std::fmt::Arguments) -> u32 { 7 }\n"
            + CONSUMER_LIB
            + "pub fn routed() -> u32 { take_args(format_args!(\"{x} then {x}\", x = provider::add_one(1))); 7 }\n"
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, f"named-argument demands must resolve: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        demand = facts_json(tmp_path / "facts", "demand.json")
        assert "provider::add_one" in json.dumps(demand)

    def test_named_argument_shadowing_provider_name_emits_no_capture_gap(self, tmp_path):
        # (c2) `{MAX}` here references the named argument `MAX = 1`, not a
        # scope variable; the capture check must not misfire on it
        lib = (
            "fn take_args(a: std::fmt::Arguments) -> u32 { 7 }\n"
            + CONSUMER_LIB
            + "pub fn routed() -> u32 { take_args(format_args!(\"{MAX}\", MAX = 1)); 7 }\n"
        )
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=lib, provider_lib=self.PROVIDER_WITH_CONST
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, f"named-arg shadow must not gap: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []

    def test_format_capture_of_provider_value_item_is_disclosed(self, tmp_path):
        # (d) direct capture: the format string captures MAX, which names a
        # provider value item — walker-invisible today (silent acceptance of
        # a provider reference); the capture must be disclosed
        lib = (
            "fn take_args(a: std::fmt::Arguments) -> u32 { 7 }\n"
            "use provider::MAX;\n"
            + CONSUMER_LIB
            + "pub fn captured() -> u32 { println!(\"max={MAX}\"); 7 }\n"
        )
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=lib, provider_lib=self.PROVIDER_WITH_CONST
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "provider-item capture must be disclosed"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_format_capture_via_alias_is_disclosed(self, tmp_path):
        # (d) alias variant: the capture names the consumer-side alias of a
        # provider value item; matching only crate-local provider names would
        # leave the hole open through the alias path the profile supports
        lib = (
            "fn take_args(a: std::fmt::Arguments) -> u32 { 7 }\n"
            "use provider::MAX as LIMIT;\n"
            + CONSUMER_LIB
            + "pub fn captured() -> u32 { take_args(format_args!(\"{LIMIT}\")); 7 }\n"
        )
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=lib, provider_lib=self.PROVIDER_WITH_CONST
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "aliased provider-item capture must be disclosed"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        codes = {d["code"] for d in report["diagnostics"]}
        assert "incomplete-demand" in codes

    def test_format_capture_of_plain_local_stays_demand_inert(self, tmp_path):
        # (e) a capture of a plain local is not provider demand; the provider
        # call in the initializer still resolves and nothing is disclosed
        lib = (
            CONSUMER_LIB
            + "pub fn local_capture() -> u32 { let x = provider::add_one(1); println!(\"{x}\"); x }\n"
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, f"plain-local capture must stay inert: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        demand = facts_json(tmp_path / "facts", "demand.json")
        assert "provider::add_one" in json.dumps(demand)

    def test_escaped_braces_emit_no_capture_and_no_gap(self, tmp_path):
        # (f) escaped braces render literal text, not captures; the scan must
        # not misfire (green-pinned guard)
        lib = (
            CONSUMER_LIB
            + "pub fn braces() -> u32 { println!(\"{{literal}} v={}\", provider::add_one(1)); 7 }\n"
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=lib)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, f"escaped braces must not gap: {proc.stdout}"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []

    # ------------------------------------------------------------------
    # wild-158: widen the rust-cargo-local-1 demand profile — bounded
    # method-call demand (design ruling D1), enum-variant inventory and
    # demand (D2), and per-construct impl-block accounting (D3). Red-first
    # per the brief: every behavior-widening assertion below must fail
    # against the pre-widening extractor.
    # ------------------------------------------------------------------

    METER_LIB = """pub struct Meter { pub v: u32 }
impl Meter {
    pub fn new() -> Meter { Meter { v: 0 } }
    pub fn tick(&mut self) { self.v += 1; }
}
pub fn drive() -> u32 { Meter::new().tick(); 7 }
"""

    def test_widen_same_crate_method_call_demand_resolves(self, tmp_path):
        # D1 bounded resolution: the receiver is a call whose head resolves
        # to an inventoried same-crate constructor with a known return type
        # (`Meter::new() -> Meter`), so `.tick()` creates the demand
        # `consumer::Meter::tick`, which resolves against the inventoried
        # public impl-method slot. Counterexample-capable: renaming/removing
        # the method breaks the demand (absence case pinned separately).
        files = write_bundle(tmp_path / "bundle", consumer_lib=self.METER_LIB)
        for i in range(2):
            proc = run_extract(
                request_record(tmp_path / "bundle", files), tmp_path / f"facts{i}"
            )
            assert proc.returncode == 0, (
                f"bounded method demand must resolve, not refuse: "
                f"rc={proc.returncode} {proc.stdout}"
            )
            report = facts_json(tmp_path / f"facts{i}", "report.json")
            assert report["complete_inventory"] is True
            assert report["diagnostics"] == []
        # determinism gate unchanged: widened extraction stays byte-identical
        contract = (tmp_path / "facts0" / "contract.json").read_bytes()
        assert (tmp_path / "facts1" / "contract.json").read_bytes() == contract
        demand = facts_json(tmp_path / "facts0", "demand.json")
        demand_blob = json.dumps(demand)
        assert "consumer::Meter::tick" in demand_blob
        assert "consumer::Meter::new" in demand_blob
        contract_doc = facts_json(tmp_path / "facts0", "contract.json")
        slots = {s["name"] for s in contract_doc["slots"]}
        assert "consumer::Meter::tick" in slots, "impl method must inventory type-qualified"
        assert "consumer::Meter::new" in slots
        assert "consumer::Meter" in slots, "receiver type itself stays inventoried"

    def test_widen_method_absent_from_inventory_keeps_gap(self, tmp_path):
        # D1: the receiver resolves but the method is absent from the
        # inventory — the demand is recorded and fails resolution with the
        # full `<crate>::<Type>::<method>` path named.
        absent = self.METER_LIB.replace(".tick()", ".tock()")
        files = write_bundle(tmp_path / "bundle", consumer_lib=absent)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "absent method must refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        reasons = [d.get("reason", "") for d in report["diagnostics"]]
        assert any("consumer::Meter::tock" in r for r in reasons), (
            f"gap must name the full method path: {reasons}"
        )

    def test_widen_unbounded_method_receiver_keeps_gap(self, tmp_path):
        # D1/D7: multi-hop chains beyond one resolved hop stay outside the
        # bounded shapes — the honest incomplete-demand gap names the
        # receiver, and the one-hop demand inside the chain is still recorded
        # (never silently dropped).
        chained = self.METER_LIB.replace(
            "Meter::new().tick(); 7", "Meter::new().tick().untick(); 7"
        )
        files = write_bundle(tmp_path / "bundle", consumer_lib=chained)
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "unbounded receiver must refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        reasons = [d.get("reason", "") for d in report["diagnostics"]]
        assert any("receiver" in r for r in reasons), (
            f"gap must name the receiver: {reasons}"
        )
        # the one-hop demand inside the chain is still recorded
        demand = facts_json(tmp_path / "facts", "demand.json")
        assert "consumer::Meter::tick" in json.dumps(demand)

    def test_widen_enum_variant_demand_resolves(self, tmp_path):
        # D2: a public enum inventories its variants as named slots
        # (`<Enum>::<Variant>`) instead of a single opaque enum item, and
        # variant demand paths resolve as supported demand — dep-qualified
        # (`provider::Mode::Slow`) and same-crate (`Flavor::Sour`).
        provider_lib = PROVIDER_LIB + "pub enum Mode { Fast, Slow(u32) }\n"
        consumer_lib = (
            CONSUMER_LIB
            + "pub enum Flavor { Sour, Sweet }\n"
            + "pub fn pick() -> u32 { let m = provider::Mode::Slow(1); 7 }\n"
            + "pub fn taste() -> u32 { let f = Flavor::Sour; 7 }\n"
        )
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=consumer_lib, provider_lib=provider_lib
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, (
            f"variant demand must resolve, not refuse: rc={proc.returncode} {proc.stdout}"
        )
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is True
        assert report["diagnostics"] == []
        contract = facts_json(tmp_path / "facts", "contract.json")
        slots = {s["name"] for s in contract["slots"]}
        assert "provider::Mode::Fast" in slots
        assert "provider::Mode::Slow" in slots
        assert "consumer::Flavor::Sour" in slots
        # variants replace the single opaque enum item (identity law: the
        # qualified path, never line numbers)
        assert "provider::Mode" not in slots
        assert "consumer::Flavor" not in slots
        demand = facts_json(tmp_path / "facts", "demand.json")
        demand_blob = json.dumps(demand)
        assert "provider::Mode::Slow" in demand_blob
        assert "consumer::Flavor::Sour" in demand_blob

    def test_widen_unknown_variant_path_keeps_gap(self, tmp_path):
        # D2: unknown variant paths — dep-qualified or same-crate — keep the
        # honest incomplete-demand gap naming the path (guard: the refusal
        # shape exists pre-widening and must survive it).
        provider_lib = PROVIDER_LIB + "pub enum Mode { Fast, Slow(u32) }\n"
        consumer_lib = (
            CONSUMER_LIB
            + "pub enum Flavor { Sour, Sweet }\n"
            + "pub fn bogus() -> u32 { provider::Mode::Huge(1) }\n"
            + "pub fn salty() -> u32 { let f = Flavor::Salty; 7 }\n"
        )
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=consumer_lib, provider_lib=provider_lib
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "unknown variant must refuse"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        reasons = [d.get("reason", "") for d in report["diagnostics"]]
        assert any("Mode::Huge" in r for r in reasons), f"{reasons}"
        assert any("Flavor::Salty" in r for r in reasons), f"{reasons}"

    def test_widen_impl_accounting_is_per_construct(self, tmp_path):
        # D3: the blanket "method implementations are outside the supported
        # profile" gap is replaced by honest per-construct accounting — pub
        # inherent methods inventory as type-qualified opaque slots, plain
        # private methods carry no public surface, restricted-visibility
        # methods and trait impls keep named gaps, and dep-qualified calls to
        # inventoried methods resolve as supported demand.
        provider_lib = """pub struct Widget;
impl Widget {
    pub fn spin(&self) {}
    fn helper(&self) {}
    pub(crate) fn internal(&self) {}
}
impl Clone for Widget { fn clone(&self) -> Self { Widget } }
impl Default for Widget { fn default() -> Self { Widget } }
"""
        consumer_lib = CONSUMER_LIB + "pub fn use_widget() { provider::Widget::spin(); }\n"
        files = write_bundle(
            tmp_path / "bundle", consumer_lib=consumer_lib, provider_lib=provider_lib
        )
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 1, "trait impls keep the inventory incomplete"
        report = facts_json(tmp_path / "facts", "report.json")
        assert report["complete_inventory"] is False
        reasons = [d.get("reason", "") for d in report["diagnostics"]]
        # the blanket impl-block gap is gone
        assert not any(
            "method implementations are outside the supported profile" in r for r in reasons
        ), f"blanket impl gap must be replaced: {reasons}"
        # trait impls and the restricted-visibility method keep named gaps
        assert any("Clone" in r for r in reasons), f"{reasons}"
        assert any("Default" in r for r in reasons), f"{reasons}"
        assert any("internal" in r for r in reasons), f"{reasons}"
        contract = facts_json(tmp_path / "facts", "contract.json")
        slots = {s["name"] for s in contract["slots"]}
        assert "provider::Widget::spin" in slots, "pub impl method inventories type-qualified"
        assert "provider::Widget::helper" not in slots, "private method: no public surface"
        # the dep-qualified call to the inventoried method resolves cleanly
        assert not any("Widget::spin" in r for r in reasons), (
            f"demand to inventoried method must resolve: {reasons}"
        )
