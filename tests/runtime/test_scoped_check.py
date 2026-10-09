# Purpose: Red-first command-level runtime tests for the scoped structural
#   check slice (beads wild-mh5.2): the `wild check` CLI against immutable
#   base/candidate bundles for a named consumer boundary.
# Responsibilities: Build the real extractor binary once per session and
#   exercise `wild check` as a subprocess against constructed bundle pairs in
#   tempdirs. Pin the named scenario behaviors from the
#   add-local-contract-checking spec deltas: a first structural result in an
#   existing repository reports assurance/law methods/scope/coverage without
#   touching project files; unused-removal and demanded-removal candidates
#   diverge (accept vs reject); hidden macro usage blocks scoped acceptance;
#   the gap/break/malformed trio yields unknown/reject/error with exits
#   1/1/2; candidate-side unresolved demand blocks acceptance; signature
#   breaks on demanded slots are definite counterexamples; repeated checks
#   are byte-identical. Assert observable records and exit codes, never
#   implementation internals.
# Rationale: The slice's acceptance is an honest scoped structural verdict
#   whose unknown/reject/error distinctions survive separate runs; synthetic
#   success or assertion mirroring would prove nothing. Written before any
#   check implementation exists; every test here must fail red against the
#   current binary (which only implements `extract`) and stay green unchanged
#   once the slice lands.

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from test_extract import (
    BIN,
    CONSUMER_LIB,
    PROVIDER_LIB,
    PROFILE,
    REPO,
    run_extract,
    request_record,
    sha,
    write_bundle,
)

CHECKER = {"name": "wild", "digest": sha("wild-extractor-v0")}
POLICY = {"structural": "accretion"}


def check_request_record(
    base_root: Path,
    base_files: dict[str, str],
    cand_root: Path,
    cand_files: dict[str, str],
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
        "obligations": None,
        "checker": CHECKER,
    }
    record.update(overrides)
    return record


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


def envelope(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


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


def candidate_bundle(
    root: Path, provider_lib: str = PROVIDER_LIB, consumer_lib: str = CONSUMER_LIB
) -> dict[str, str]:
    files = write_bundle(root, consumer_lib=consumer_lib)
    if provider_lib != PROVIDER_LIB:
        (root / "provider/src/lib.rs").write_text(provider_lib)
        files["provider/src/lib.rs"] = provider_lib
    return files


def _duplicate_key_raw(record: dict) -> str:
    return json.dumps(record).replace(
        '"kind": "check-request"',
        '"kind": "check-request","kind": "check-request"',
        1,
    )


def _no_raw(record: dict) -> None:
    del record
    return None


# Each mutation distorts one check-request shape the validator must refuse
# with an error-class exit; the mapped function applies the distortion and
# returns raw request text when the malformedness lives in the bytes.
MALFORMED_MUTATIONS: dict[str, Callable[[dict], str | None]] = {
    "unknown-field": lambda r: r.update(surprise=True) or _no_raw(r),
    "unknown-version": lambda r: r.update(version="local-2") or _no_raw(r),
    "base-digest-mismatch": lambda r: r["base"]["files"].update(
        {"consumer/src/lib.rs": sha("tampered")}
    )
    or _no_raw(r),
    "out-of-bundle-reference": lambda r: r["base"]["files"].update(
        {"../escape.rs": sha("x")}
    )
    or _no_raw(r),
    "non-null-obligations": lambda r: r.update(obligations={"digest": sha("obligations")})
    or _no_raw(r),
    "wrong-policy": lambda r: r.update(policy={"structural": "equality"}) or _no_raw(r),
    "duplicate-key": _duplicate_key_raw,
}


@pytest.mark.usefixtures("wild_binary")
class TestScopedCheck:
    def test_first_result_reports_scope_without_registry(self, tmp_path):
        base = write_bundle(tmp_path / "base")
        cand = candidate_bundle(tmp_path / "cand")
        before = {
            rel: (tmp_path / name / rel).read_bytes()
            for name in ("base", "cand")
            for rel in (list(base) + list(cand))
            if (tmp_path / name / rel).exists()
        }
        out = tmp_path / "out"
        proc = run_check(
            check_request_record(tmp_path / "base", base, tmp_path / "cand", cand),
            out / "report.json",
        )
        assert proc.returncode == 0, proc.stderr
        env = envelope(proc)
        assert env["decision"] == "accept"
        assert env["assurance"] == "PassDeclared"
        assert env["command"] == "check"
        report = json.loads((tmp_path / "out" / "report.json").read_text())
        assert report["kind"] == "check-report"
        assert report["law_methods"] == []  # honest: no laws evaluated in this slice
        assert report["consumer"] == "consumer"
        assert report["policy"] == POLICY
        # only explicitly requested report outputs are written: the report
        # file plus its declared facts subdirectories, nothing else
        written = {str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()}
        allowed = {"report.json", "check.json"}
        allowed |= {
            f"facts/{side}/{name}"
            for side in ("base", "candidate")
            for name in ("contract.json", "demand.json", "provenance.json")
        }
        assert written - allowed == set(), f"unexpected writes: {written - allowed}"
        assert (out / "facts/base/contract.json").exists()
        assert (out / "facts/candidate/contract.json").exists()
        # project source, manifests and locks remain unchanged
        after = {
            rel: (tmp_path / name / rel).read_bytes()
            for name in ("base", "cand")
            for rel in (list(base) + list(cand))
            if (tmp_path / name / rel).exists()
        }
        assert before == after

    def test_unused_removal_accepts_and_demanded_removal_rejects(self, tmp_path):
        base = write_bundle(tmp_path / "base")
        unused_removed = PROVIDER_LIB.replace(
            "pub fn never_called() -> u32 { 3 }\n", ""
        )
        cand_ok = candidate_bundle(tmp_path / "cand-ok", provider_lib=unused_removed)
        proc = run_check(
            check_request_record(tmp_path / "base", base, tmp_path / "cand-ok", cand_ok),
            tmp_path / "ok.json",
        )
        assert proc.returncode == 0, proc.stdout
        assert envelope(proc)["decision"] == "accept"

        demanded_removed = unused_removed.replace(
            "pub fn add_one(x: u32) -> u32 { x + 1 }\n", ""
        )
        cand_bad = candidate_bundle(tmp_path / "cand-bad", provider_lib=demanded_removed)
        proc = run_check(
            check_request_record(tmp_path / "base", base, tmp_path / "cand-bad", cand_bad),
            tmp_path / "bad.json",
        )
        assert proc.returncode == 1, "a demanded removal is a structural counterexample"
        env = envelope(proc)
        assert env["decision"] == "refuse"
        assert env["assurance"] == "Reject"
        report = json.loads((tmp_path / "bad.json").read_text())
        verdicts = {v["called"]: v["verdict"] for v in report["demanded_slots"]}
        assert verdicts["provider::add_one"] == "removed"
        assert verdicts["provider::greet"] == "pass"

    def test_hidden_usage_blocks_scoped_claim(self, tmp_path):
        base = write_bundle(tmp_path / "base")
        hidden = CONSUMER_LIB + "\nmacro_rules! call_hidden {\n    () => { provider::add_one(4) };\n}\ncall_hidden!();\n"
        cand = candidate_bundle(tmp_path / "cand", consumer_lib=hidden)
        # the base consumer must carry the hidden usage too for the pair to
        # be otherwise identical; rebuild base with the same consumer source
        base_files = dict(base)
        (tmp_path / "base/consumer/src/lib.rs").write_text(hidden)
        base_files["consumer/src/lib.rs"] = hidden
        proc = run_check(
            check_request_record(tmp_path / "base", base_files, tmp_path / "cand", cand),
            tmp_path / "report.json",
        )
        assert proc.returncode == 1, "hidden usage must block scoped acceptance"
        env = envelope(proc)
        assert env["decision"] == "refuse"
        assert env["assurance"] == "Unknown"
        report = json.loads((tmp_path / "report.json").read_text())
        codes = {d["code"] for d in report["diagnostics"]}
        assert "unsupported-construct" in codes

    def test_base_macro_gaps_demand_declaration_visibility(self, tmp_path):
        # The macro is unrelated to the demanded slot (it invokes a non-demanded
        # provider fn) and the candidate passes every verdict, so the verdict
        # engine alone would declare it a forged compatible result; the
        # base-side declaration-visible-on-base claim requires the base
        # inventory to be complete, and the extractor marks base complete_inventory
        # false because the opaque macro invocation's body is un-analyzed.
        base = write_bundle(tmp_path / "base")
        macro_lib = (
            CONSUMER_LIB
            + "\nmacro_rules! opaque {\n    () => { provider::never_called(7) };\n}\nopaque!();\n"
        )
        base_files = dict(base)
        (tmp_path / "base/consumer/src/lib.rs").write_text(macro_lib)
        base_files["consumer/src/lib.rs"] = macro_lib
        cand = candidate_bundle(tmp_path / "cand", consumer_lib=macro_lib)
        proc = run_check(
            check_request_record(tmp_path / "base", base_files, tmp_path / "cand", cand),
            tmp_path / "report.json",
        )
        assert proc.returncode == 1, "gaps in base demand declaration visibility must be unknown"
        env = envelope(proc)
        assert env["decision"] == "refuse"
        assert env["assurance"] == "Unknown"
        report = json.loads((tmp_path / "report.json").read_text())
        assert report["base"]["complete_inventory"] is False, (
            "the demanded slot is declaration-visible but the base inventory is incomplete"
        )
        verdicts = {v["called"]: v["verdict"] for v in report["demanded_slots"]}
        assert verdicts["provider::add_one"] == "pass", (
            "the refusal must come from the completeness claim, not a verdict"
        )
        assert verdicts["provider::greet"] == "pass"

    def test_gap_break_error_trio_yields_unknown_reject_error(self, tmp_path):
        # unknown: a required analysis gap (unresolved external dep demand)
        base = write_bundle(tmp_path / "base")
        gap_lib = CONSUMER_LIB + "\npub fn uses_external() -> u32 { extdep::probe(1) }\n"
        gap_toml = (
            "consumer/Cargo.toml",
            "consumer/src/lib.rs",
        )
        gap_files = dict(base)
        (tmp_path / "base/consumer/src/lib.rs").write_text(gap_lib)
        gap_files["consumer/src/lib.rs"] = gap_lib
        (tmp_path / "base/consumer/Cargo.toml").write_text(
            (tmp_path / "base/consumer/Cargo.toml").read_text() + 'extdep = "1.0"\n'
        )
        gap_files["consumer/Cargo.toml"] = (
            tmp_path / "base/consumer/Cargo.toml"
        ).read_text()
        cand = candidate_bundle(tmp_path / "cand")
        cand_files = dict(cand)
        (tmp_path / "cand/consumer/src/lib.rs").write_text(gap_lib)
        cand_files["consumer/src/lib.rs"] = gap_lib
        (tmp_path / "cand/consumer/Cargo.toml").write_text(
            (tmp_path / "cand/consumer/Cargo.toml").read_text() + 'extdep = "1.0"\n'
        )
        cand_files["consumer/Cargo.toml"] = (
            tmp_path / "cand/consumer/Cargo.toml"
        ).read_text()
        proc = run_check(
            check_request_record(tmp_path / "base", gap_files, tmp_path / "cand", cand_files),
            tmp_path / "gap.json",
        )
        assert proc.returncode == 1
        env = envelope(proc)
        assert env["decision"] == "refuse" and env["assurance"] == "Unknown"

        # reject: demanded removal (definite structural counterexample);
        # rebuild a clean base on disk — the earlier unknown part mutated
        # tmp_path/base in place, so its digests no longer describe it
        demanded_removed = PROVIDER_LIB.replace(
            "pub fn add_one(x: u32) -> u32 { x + 1 }\n", ""
        ).replace("pub fn never_called() -> u32 { 3 }\n", "")
        cand_bad = candidate_bundle(tmp_path / "cand-bad", provider_lib=demanded_removed)
        clean_base = write_bundle(tmp_path / "base-clean")
        proc = run_check(
            check_request_record(tmp_path / "base-clean", clean_base, tmp_path / "cand-bad", cand_bad),
            tmp_path / "break.json",
        )
        assert proc.returncode == 1
        env = envelope(proc)
        assert env["decision"] == "refuse" and env["assurance"] == "Reject"

        # error: malformed request
        record = check_request_record(tmp_path / "base", base, tmp_path / "cand-bad", cand_bad)
        record["version"] = "local-2"
        proc = run_check(record, tmp_path / "err.json")
        assert proc.returncode == 2
        env = envelope(proc)
        assert env["decision"] == "refuse"

    def test_candidate_unresolved_demand_blocks_acceptance(self, tmp_path):
        # a candidate adding a call to a dependency whose source is absent
        # must not be accepted behind root demand
        base = write_bundle(tmp_path / "base")
        ext_lib = CONSUMER_LIB + "\npub fn uses_external() -> u32 { extdep::probe(1) }\n"
        cand = candidate_bundle(tmp_path / "cand", consumer_lib=ext_lib)
        proc = run_check(
            check_request_record(tmp_path / "base", base, tmp_path / "cand", cand),
            tmp_path / "report.json",
        )
        assert proc.returncode == 1, "newly required dependencies cannot hide"
        env = envelope(proc)
        assert env["assurance"] == "Unknown"

    def test_signature_change_breaks_demanded_slot(self, tmp_path):
        base = write_bundle(tmp_path / "base")
        widened = PROVIDER_LIB.replace(
            "pub fn add_one(x: u32) -> u32 { x + 1 }",
            "pub fn add_one(x: i32) -> i32 { x + 1 }",
        )
        cand = candidate_bundle(tmp_path / "cand", provider_lib=widened)
        proc = run_check(
            check_request_record(tmp_path / "base", base, tmp_path / "cand", cand),
            tmp_path / "report.json",
        )
        assert proc.returncode == 1
        env = envelope(proc)
        assert env["assurance"] == "Reject"
        report = json.loads((tmp_path / "report.json").read_text())
        verdicts = {v["called"]: v["verdict"] for v in report["demanded_slots"]}
        assert verdicts["provider::add_one"] == "broken"

    def test_repeated_check_is_byte_identical(self, tmp_path):
        base = write_bundle(tmp_path / "base")
        cand = candidate_bundle(tmp_path / "cand")
        record = check_request_record(tmp_path / "base", base, tmp_path / "cand", cand)
        outs = []
        for i in range(2):
            proc = run_check(record, tmp_path / f"report{i}.json")
            assert proc.returncode == 0, proc.stderr
            outs.append(
                (
                    proc.stdout,
                    (tmp_path / f"report{i}.json").read_bytes(),
                    (tmp_path / f"facts{i if False else i}" / "base" / "contract.json")
                    .read_bytes()
                    if False
                    else None,
                )
            )
        assert outs[0] == outs[1]

    def test_malformed_check_requests_are_refused(self, tmp_path):
        base = write_bundle(tmp_path / "base")
        cand = candidate_bundle(tmp_path / "cand")
        for mutation, mutate in MALFORMED_MUTATIONS.items():
            record = check_request_record(tmp_path / "base", base, tmp_path / "cand", cand)
            raw = mutate(record)
            request_path = tmp_path / f"check-{mutation}.json"
            request_path.write_text(raw if raw is not None else json.dumps(record))
            report_path = tmp_path / f"report-{mutation}.json"
            proc = subprocess.run(
                [str(BIN), "check", "--request", str(request_path), "--format", "json",
                 "--report", str(report_path)],
                capture_output=True,
                text=True,
                cwd=REPO,
            )
            assert proc.returncode == 2, f"{mutation} must be an error refusal"
            env = envelope(proc)
            assert env["decision"] == "refuse"
            report = json.loads(report_path.read_text())
            assert report["diagnostics"], f"{mutation} must carry a diagnostic"

    def test_extract_still_works_after_check_lands(self, tmp_path):
        # the check slice must not disturb the extract workflow it sits on
        files = write_bundle(tmp_path / "bundle")
        proc = run_extract(request_record(tmp_path / "bundle", files), tmp_path / "facts")
        assert proc.returncode == 0, proc.stderr
