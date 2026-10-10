# Purpose: Red-first command-level runtime tests for the update planning
#   slice (beads wild-nic.1): the `wild update plan` CLI against a supplied
#   Cargo project bundle for a named package target.
# Responsibilities: Build the real binary once per session and exercise
#   `wild update plan` as a subprocess against constructed project bundles
#   in tempdirs. Pin the `plan-without-changing-the-application` scenario
#   from the add-consumer-update-workflow spec delta: a target outside the
#   original range yields a plan naming the exact range change and
#   base-file preconditions while manifest, lockfile, and source bytes stay
#   untouched; ambiguous package identities, inherited workspace ranges,
#   unsupported lock versions, and unsupported manifest layouts refuse with
#   diagnostics instead of guessing; a plan-ready result always carries
#   Unknown assurance and a disclosed pending-check set, and never claims a
#   delivered update or checked compatibility. Assert observable records
#   and exit codes, never implementation internals.
# Rationale: The slice's acceptance is an honest read-only planning
#   workflow whose refusals survive separate runs; synthetic success or
#   assertions mirroring the implementation would prove nothing. Written
#   before any update implementation exists per the ticket's TDD mandate;
#   every test here must fail red against the current binary (which only
#   implements extract/check) and stay green unchanged once the slice
#   lands.

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from test_extract import BIN, REPO, sha

MANIFEST = """[package]
name = "consumer"
version = "0.1.0"
edition = "2021"

[dependencies]
provider = "1.0"
"""

LOCK = """version = 4

[[package]]
name = "consumer"
version = "0.1.0"
dependencies = [
 "provider",
]

[[package]]
name = "provider"
version = "1.0.0"
"""

LIB_RS = """pub fn use_provider() -> u32 { provider::add_one(1) }
"""


def write_project(
    root: Path,
    manifest: str = MANIFEST,
    lock: str = LOCK,
) -> dict[str, str]:
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "Cargo.toml": manifest,
        "Cargo.lock": lock,
        "src/lib.rs": LIB_RS,
    }
    for rel, text in files.items():
        dest = root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    return files


def update_request(
    root: Path,
    files: dict[str, str],
    **overrides,
) -> dict:
    record = {
        "version": "local-1",
        "kind": "update-request",
        "bundle_root": str(root),
        "files": {rel: sha(text) for rel, text in files.items()},
        "manifest": "Cargo.toml",
        "package": "provider",
        "release": "2.0.0",
        "source_digest": sha("registry-archive-bytes"),
        "target": "x86_64-unknown-linux-gnu",
        "toolchain": "stable",
        "features": [],
        "consumer": "consumer",
        "policy": {"structural": "accretion"},
        "catalog": {"kind": "local-fixture", "digest": sha("catalog-snapshot-v0")},
        "planner": {"name": "wild", "digest": sha("wild-planner-v0")},
    }
    record.update(overrides)
    return record


def run_plan(record: dict, output: Path) -> subprocess.CompletedProcess[str]:
    output.parent.mkdir(parents=True, exist_ok=True)
    request_path = output.parent / "update-request.json"
    request_path.write_text(json.dumps(record))
    try:
        return subprocess.run(
            [str(BIN), "update", "plan", "--request", str(request_path), "--output", str(output)],
            capture_output=True,
            text=True,
            cwd=REPO,
        )
    except FileNotFoundError:
        pytest.fail(f"wild binary missing at {BIN}; build the extractor first")


def envelope(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


def digests_of(root: Path, files: dict[str, str]) -> dict[str, str]:
    return {
        rel: sha((root / rel).read_text()) for rel in files
    }


def test_plan_records_exact_change_without_touching_the_project(tmp_path: Path) -> None:
    root = tmp_path / "project"
    files = write_project(root)
    output = tmp_path / "out" / "plan.json"
    proc = run_plan(update_request(root, files), output)
    assert proc.returncode == 0, proc.stderr
    env = envelope(proc)
    assert env["command"] == "update-plan"
    assert env["decision"] == "accept"
    # Planning is not a compatibility verdict: assurance stays Unknown.
    assert env["assurance"] == "Unknown"

    plan = json.loads(output.read_text())
    assert plan["version"] == "local-1"
    assert plan["kind"] == "update-plan"
    assert plan["package"] == "provider"
    assert plan["release"] == "2.0.0"
    assert plan["original_range"] == "1.0"
    assert plan["edit"] == {
        "file": "Cargo.toml",
        "table": "dependencies",
        "package": "provider",
        "from": "1.0",
        "to": "=2.0.0",
    }
    # Preconditions bind the exact base-file digests the plan was built on.
    assert plan["preconditions"] == {
        "Cargo.toml": sha(MANIFEST),
        "Cargo.lock": sha(LOCK),
    }
    # A plan-ready result discloses pending validation and never claims a
    # delivered update or checked compatibility.
    assert set(plan["pending_checks"]) == {
        "baseline-build",
        "baseline-test",
        "cargo-resolution",
        "closure-inspection",
        "contract-checks",
        "protected-obligations",
    }
    assert plan["disposition"] == "plan-ready"
    assert plan["assurance"] == "Unknown"
    assert "delivered" not in json.dumps(plan)
    # The exact range change is identified as plan friction.
    assert plan["excluded_by_original_range"] is True

    # The original manifest, lockfile, and source stay byte-identical.
    assert digests_of(root, files) == {rel: sha(text) for rel, text in files.items()}


def test_plan_refuses_ambiguous_package_identity(tmp_path: Path) -> None:
    root = tmp_path / "project"
    ambiguous = MANIFEST + "\n[dev-dependencies]\nprovider = \"1.0\"\n"
    files = write_project(root, manifest=ambiguous)
    output = tmp_path / "out" / "plan.json"
    proc = run_plan(update_request(root, files), output)
    assert proc.returncode == 1
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert env["assurance"] == "Unknown"
    codes = [d["code"] for d in env["tier_reports"]] if env["tier_reports"] else []
    assert "ambiguous-package" in codes or any(
        d.get("code") == "ambiguous-package" for d in env.get("diagnostics", [])
    )
    assert not output.exists()


def test_plan_refuses_inherited_workspace_range(tmp_path: Path) -> None:
    root = tmp_path / "project"
    inherited = MANIFEST.replace('provider = "1.0"', "provider = { workspace = true }")
    files = write_project(root, manifest=inherited)
    output = tmp_path / "out" / "plan.json"
    proc = run_plan(update_request(root, files), output)
    assert proc.returncode == 1
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert any(d.get("code") == "inherited-range" for d in env.get("diagnostics", []))
    assert not output.exists()


def test_plan_refuses_unsupported_lock_version(tmp_path: Path) -> None:
    root = tmp_path / "project"
    files = write_project(root, lock=LOCK.replace("version = 4", "version = 5"))
    output = tmp_path / "out" / "plan.json"
    proc = run_plan(update_request(root, files), output)
    assert proc.returncode == 1
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert any(d.get("code") == "unsupported-lock" for d in env.get("diagnostics", []))
    assert not output.exists()


def test_plan_refuses_unsupported_manifest_layout(tmp_path: Path) -> None:
    root = tmp_path / "project"
    git_dep = MANIFEST.replace(
        'provider = "1.0"',
        'provider = { git = "https://example.invalid/provider" }',
    )
    files = write_project(root, manifest=git_dep)
    output = tmp_path / "out" / "plan.json"
    proc = run_plan(update_request(root, files), output)
    assert proc.returncode == 1
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert any(d.get("code") == "unsupported-manifest" for d in env.get("diagnostics", []))
    assert not output.exists()


def test_plan_refuses_stale_base_commitment(tmp_path: Path) -> None:
    root = tmp_path / "project"
    files = write_project(root)
    record = update_request(root, files)
    # The committed manifest digest no longer matches the actual bytes.
    (root / "Cargo.toml").write_text(MANIFEST + "\n# drifted\n")
    output = tmp_path / "out" / "plan.json"
    proc = run_plan(record, output)
    assert proc.returncode == 1
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert not output.exists()


def test_plan_error_on_malformed_request(tmp_path: Path) -> None:
    root = tmp_path / "project"
    files = write_project(root)
    record = update_request(root, files)
    text = json.dumps(record)
    # Duplicate object key: refused by the v1 reader rules.
    text = text[:-1] + ',"package": "other"}'
    output = tmp_path / "out" / "plan.json"
    request_path = output.parent / "update-request.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    request_path.write_text(text)
    proc = subprocess.run(
        [str(BIN), "update", "plan", "--request", str(request_path), "--output", str(output)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert proc.returncode == 2
    env = envelope(proc)
    assert env["decision"] == "refuse"
    assert env["assurance"] == "Unknown"
    assert not output.exists()
