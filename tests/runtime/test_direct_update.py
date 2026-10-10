# Purpose: Red-first command-level runtime tests for the integrated direct
#   update slice (beads wild-nic.3, change add-consumer-update-workflow): the
#   `wild update evaluate` pipeline that connects baseline validation, real
#   offline Cargo resolution, fixed-lock build/test, full closure coverage,
#   and a durable pinned diff into one delivered/refused decision. The
#   request builder also carries the optional supplied-migration fields
#   (wild-nic.4): a caller-committed `migration_patch` map bound by
#   `migration_digest` (sha256 of the canonical target -> source-digest map).
# Responsibilities: Assemble the e5 fixture consumers with their frozen
#   local-registry mirrors, plan the exact candidate, pin an external
#   authority, and run evaluation as a subprocess against real Cargo.
#   Pin the scenarios owned by this slice from the spec delta: (a) a
#   compatible release outside the old range is delivered with a
#   manifest/lock-only diff, evidence for the actual artifacts, and no
#   registry-certificate or newest-tip claim; (b) a permitted patch that
#   breaks the consumer is refused with no delivered-update claim; (c) a new
#   provider dependency is not hidden by demand restriction — it stays in
#   closure and coverage as Unknown and refuses delivery; (d) failed output
#   persistence cannot deliver; (e) a failed baseline is recorded, never
#   attributed to the candidate; (f) the original worktree stays unchanged.
# Rationale: The slice's acceptance requires actual Cargo builds/tests and
#   durable output, not canned success responses. Every scenario runs the
#   real binary offline against the committed mirror so verdicts survive
#   separate runs; assertions mirror observable records, never internals.

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from test_extract import BIN, REPO, sha

FIXTURES = REPO / "experiments" / "update_fixtures" / "e5"


def sha_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(value: dict) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value: dict) -> str:
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def bundle_files(root: Path) -> dict[str, str]:
    return {
        str(p.relative_to(root)).replace("\\", "/"): sha_bytes(p.read_bytes())
        for p in sorted(root.rglob("*"))
        if p.is_file()
    }


def snapshot(root: Path) -> dict[str, str]:
    return {rel: sha_bytes((root / rel).read_bytes()) for rel in bundle_files(root)}


def assemble_consumer(case: str, root: Path) -> Path:
    """Copy one e5 case consumer and attach the frozen mirror + config.

    The committed e5 case lockfiles are bootstrap clones whose checksums do
    not match the e5 mirror's index cksums, so a consistent baseline lock is
    synthesized here with real Cargo against the frozen mirror, pinning the
    case's baseline release (dept 1.2.3 for every scenario this slice owns).
    """
    consumer_dir = FIXTURES / "cases" / case / "consumer"
    if not consumer_dir.is_dir():
        consumer_dir = FIXTURES / "consumer-base"
    shutil.copytree(consumer_dir, root)
    mirror = root / "registry-mirror"
    shutil.copytree(FIXTURES / "registry" / "index", mirror / "index")
    shutil.copy2(FIXTURES / "registry" / "index" / "config.json", mirror / "config.json")
    for crate in sorted((FIXTURES / "consumer-mirror").glob("*.crate")):
        shutil.copy2(crate, mirror / crate.name)
    (root / ".cargo").mkdir(exist_ok=True)
    (root / ".cargo" / "config.toml").write_text(
        '[source.crates-io]\nreplace-with = "wild-lr"\n\n'
        '[source.wild-lr]\nlocal-registry = "registry-mirror"\n',
        encoding="utf-8",
    )
    (root / "Cargo.lock").unlink(missing_ok=True)
    home = tmp_cargo_home(root)
    proc = subprocess.run(
        ["cargo", "update", "--offline", "-p", "dept", "--precise", "1.2.3"],
        cwd=root, capture_output=True, text=True,
        env={"CARGO_HOME": str(home), "PATH": os.environ["PATH"]},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    shutil.rmtree(home)
    return root


def tmp_cargo_home(root: Path) -> Path:
    home = root / ".wild-scratch-home"
    home.mkdir(exist_ok=True)
    return home.resolve()


def migration_digest(patch: dict[str, str | None], root: Path) -> str:
    """sha256 of the canonical {target: source-digest | None} binding map."""
    bound = {
        target: (sha_bytes((root / source).read_bytes()) if source else None)
        for target, source in sorted(patch.items())
    }
    return digest(bound)


def run_plan(root: Path, tmp_path: Path, release: str, contracts: dict, migration: dict[str, str | None] | None = None) -> dict:
    request = {
        "version": "local-1",
        "kind": "update-request",
        "bundle_root": str(root),
        "files": bundle_files(root),
        "manifest": "Cargo.toml",
        "package": "dept",
        "release": release,
        "source_digest": sha_bytes((root / "registry-mirror" / f"dept-{release}.crate").read_bytes()),
        "target": "x86_64-unknown-linux-gnu",
        "toolchain": "1.98.1",
        "features": [],
        "consumer": "consumer",
        "policy": {"structural": "complete-structure"},
        "catalog": {"kind": "local-fixture", "digest": sha_bytes(b"catalog-snapshot-v0")},
        "planner": {"name": "wild", "digest": sha_bytes(b"wild-planner-v0")},
        "contracts": contracts,
    }
    if migration is not None:
        request["migration_patch"] = migration
        request["migration_digest"] = migration_digest(migration, root)
    request_path = tmp_path / "update-request.json"
    request_path.write_text(canonical(request))
    output = tmp_path / "plan.json"
    proc = subprocess.run(
        [str(BIN), "update", "plan", "--request", str(request_path), "--output", str(output)],
        capture_output=True, text=True, cwd=REPO,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(output.read_text())


def trusted_pin(plan: dict, authority: dict) -> dict:
    return {
        "version": "local-1",
        "kind": "update-authority-pin",
        "invocation": {"name": "trusted-ci", "digest": sha_bytes(b"trusted-ci-v0")},
        "plan_digest": digest(plan),
        "authority_digest": digest(authority),
    }


def make_authority(tmp_path: Path, plan: dict) -> dict:
    return {
        "version": "local-1",
        "kind": "update-authority",
        "plan_digest": digest(plan),
        "bundle_root": str(tmp_path / "consumer"),
        "invocation": {"name": "trusted-ci", "digest": sha_bytes(b"trusted-ci-v0")},
        "allowed_actions": ["evaluate"],
        "environment": {"toolchain": "1.98.1", "target": "x86_64-unknown-linux-gnu"},
        "policy": {"structural": "complete-structure"},
    }


def run_evaluate(plan: dict, authority: dict, pin: dict, tmp_path: Path) -> tuple[subprocess.CompletedProcess[str], Path]:
    plan_path = tmp_path / "evaluate-plan.json"
    authority_path = tmp_path / "authority.json"
    pin_path = tmp_path / "authority-pin.json"
    plan_path.write_text(canonical(plan))
    authority_path.write_text(canonical(authority))
    pin_path.write_text(canonical(pin))
    result_dir = tmp_path / "result"
    proc = subprocess.run(
        [
            str(BIN), "update", "evaluate",
            "--plan", str(plan_path),
            "--authority", str(authority_path),
            "--pin", str(pin_path),
            "--output", str(result_dir),
        ],
        capture_output=True, text=True, cwd=REPO,
    )
    return proc, result_dir


def evaluate_case(tmp_path: Path, case: str, release: str, contracts: dict):
    root = assemble_consumer(case, tmp_path / "consumer")
    before = snapshot(root)
    plan = run_plan(root, tmp_path, release, contracts)
    proc, result_dir = run_evaluate(plan, make_authority(tmp_path, plan), trusted_pin(plan, make_authority(tmp_path, plan)), tmp_path)
    report_path = result_dir / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    after = snapshot(root)
    return proc, report, result_dir, before, after


DEPT = "dept"


def contract_for(version: str) -> dict:
    crate = FIXTURES / "consumer-mirror" / f"dept-{version}.crate"
    return {DEPT: sha_bytes(crate.read_bytes())}


def test_compatible_release_outside_the_old_range_is_delivered(tmp_path: Path) -> None:
    proc, report, result_dir, before, after = evaluate_case(
        tmp_path, "cell-excluded-compatible-major", "2.0.0", contract_for("2.0.0")
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "delivered"
    assert report["update_class"] == "direct"
    assert report["actual"]["version"] == "2.0.0"
    # The pinned diff changes only manifest/lock.
    assert [d["path"] for d in report["diff"]] == ["Cargo.toml", "Cargo.lock"]
    # Durable pinned output exists and reads back with the reported digests.
    for entry in report["diff"]:
        name = "Cargo.toml" if entry["path"] == "Cargo.toml" else "Cargo.lock"
        pinned = (result_dir / "pinned" / name).read_bytes()
        assert sha_bytes(pinned) == entry["after_digest"]
    # Evidence for the actual commands: baseline and fixed-lock build/test ran.
    roles = {e["role"]: e["exit_code"] for e in report["evidence"]}
    assert roles["baseline-test"] == 0
    assert roles["fixed-lock-build"] == 0
    assert roles["fixed-lock-test"] == 0
    # Local report: no registry certificate or newest-tip claim.
    text = canonical(report)
    assert report["scope"] == "local"
    assert report["resolution"] == "host-selected"
    assert "certificate" not in text and "newest" not in text and "lineage" not in text
    # The original worktree remains unchanged.
    assert before == after


def test_permitted_patch_breaking_the_consumer_is_refused(tmp_path: Path) -> None:
    proc, report, result_dir, before, after = evaluate_case(
        tmp_path, "cell-allowed-incompatible-patch", "1.2.4", contract_for("1.2.4")
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "refused"
    assert report["actual"]["version"] == "1.2.4"
    assert any(d["code"] == "consumer-break" for d in report["diagnostics"])
    assert not (result_dir / "pinned").exists()
    assert before == after


def test_new_provider_dependency_is_not_hidden_by_demand_restriction(tmp_path: Path) -> None:
    proc, report, result_dir, before, after = evaluate_case(
        tmp_path, "transitive-addition", "1.9.0", contract_for("1.9.0")
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "refused"
    # deputil enters the closure even though the root's demanded output
    # signature is unchanged; it refuses delivery.
    names = {(e["package"], e["assurance"]) for e in report["closure"]}
    assert ("deputil", "Unknown") in names
    assert any(d["code"] == "unknown-dependency" for d in report["diagnostics"])
    assert before == after


def test_unknown_dependency_remains_visible_in_closure_and_coverage(tmp_path: Path) -> None:
    proc, report, result_dir, before, after = evaluate_case(
        tmp_path, "transitive-addition", "1.9.0", {}
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "refused"
    entries = {(e["package"], e["status"], e["assurance"]) for e in report["closure"]}
    # The uncontracted dependency stays in the closure and coverage.
    assert ("deputil", "new", "Unknown") in entries
    assert before == after


def test_failed_output_persistence_cannot_deliver(tmp_path: Path) -> None:
    root = assemble_consumer("cell-excluded-compatible-major", tmp_path / "consumer")
    before = snapshot(root)
    plan = run_plan(root, tmp_path, "2.0.0", contract_for("2.0.0"))
    result_dir = tmp_path / "result"
    (result_dir / "pinned").mkdir(parents=True)
    # Make the pinned directory unwritable so the durable write must fail.
    (result_dir / "pinned").chmod(0o500)
    proc, result_dir2 = run_evaluate(plan, make_authority(tmp_path, plan), trusted_pin(plan, make_authority(tmp_path, plan)), tmp_path)
    try:
        report_path = result_dir / "report.json"
        assert proc.returncode != 0
        assert report_path.exists(), "the error cause must be recorded: " + proc.stdout + proc.stderr
        report = json.loads(report_path.read_text())
        assert report["disposition"] == "error"
        assert any(d["code"] == "persistence-failed" for d in report["diagnostics"])
        assert not (result_dir / "pinned" / "Cargo.toml").exists()
    finally:
        (result_dir / "pinned").chmod(0o755)
    assert before == snapshot(root)


def test_failed_baseline_is_recorded_not_attributed_to_the_candidate(tmp_path: Path) -> None:
    proc, report, result_dir, before, after = evaluate_case(
        tmp_path, "baseline-failure", "1.2.3", contract_for("1.2.3")
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "refused"
    assert any(d["code"] == "baseline-failed" for d in report["diagnostics"])
    assert before == after
