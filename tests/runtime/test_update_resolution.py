# Purpose: Red-first command-level runtime tests for the update evaluation
#   slice (beads wild-nic.2, change add-consumer-update-workflow): the
#   `wild update evaluate` CLI resolving an authorized plan against real
#   offline Cargo in a disposable workspace.
# Responsibilities: Plan a real update against the frozen bootstrap consumer
#   fixture, pin an external authority over that exact plan, and run
#   evaluation as a subprocess. Pin the three scenarios owned by this slice
#   from the add-consumer-update-workflow spec delta: (a) candidate
#   self-authorization fails — an authority file not committed by the trusted
#   invocation pin refuses before any edit; (b) Cargo selects a different
#   artifact — evaluation refuses and records both requested and actual
#   identities; (c) an environment constraint (unsupported rust-version)
#   refuses delivery independently of compatibility. A successful evaluation
#   records evaluated host evidence only — never a delivered-update claim —
#   and the original worktree stays byte-identical. Assert observable records
#   and exit codes, never implementation internals.
# Rationale: The slice's acceptance requires actual offline Cargo resolution,
#   not canned success responses. Every scenario runs the real binary against
#   the committed local-registry mirror so refusals survive separate runs;
#   synthetic success or assertions mirroring the implementation would prove
#   nothing.

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from test_extract import BIN, REPO, sha

FIXTURE = REPO / "experiments" / "update_fixtures" / "bootstrap" / "consumer"
MIRROR = "registry-mirror"


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
    return {
        rel: sha_bytes((root / rel).read_bytes()) for rel in bundle_files(root)
    }


def prepare_consumer(tmp_path: Path) -> Path:
    root = tmp_path / "consumer"
    shutil.copytree(FIXTURE, root)
    return root


def run_plan(root: Path, tmp_path: Path, release: str = "2.0.0", **overrides) -> dict:
    request = {
        "version": "local-1",
        "kind": "update-request",
        "bundle_root": str(root),
        "files": bundle_files(root),
        "manifest": "Cargo.toml",
        "package": "dept",
        "release": release,
        "source_digest": sha_bytes((root / MIRROR / "dept-2.0.0.crate").read_bytes()),
        "target": "x86_64-unknown-linux-gnu",
        "toolchain": "1.98.1",
        "features": [],
        "consumer": "consumer",
        "policy": {"structural": "accretion"},
        "catalog": {"kind": "local-fixture", "digest": sha_bytes(b"catalog-snapshot-v0")},
        "planner": {"name": "wild", "digest": sha_bytes(b"wild-planner-v0")},
    }
    request.update(overrides)
    request_path = tmp_path / "update-request.json"
    request_path.write_text(canonical(request))
    output = tmp_path / "plan.json"
    proc = subprocess.run(
        [str(BIN), "update", "plan", "--request", str(request_path), "--output", str(output)],
        capture_output=True,
        text=True,
        cwd=REPO,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return json.loads(output.read_text())


def trusted_pin(plan: dict, authority: dict) -> dict:
    """The externally committed pin of the trusted invocation."""
    return {
        "version": "local-1",
        "kind": "update-authority-pin",
        "invocation": {"name": "trusted-ci", "digest": sha_bytes(b"trusted-ci-v0")},
        "plan_digest": digest(plan),
        "authority_digest": digest(authority),
    }


def run_evaluate(
    plan: dict,
    authority: dict,
    pin: dict,
    tmp_path: Path,
    output_dir: str = "result",
) -> subprocess.CompletedProcess[str]:
    plan_path = tmp_path / "evaluate-plan.json"
    authority_path = tmp_path / "authority.json"
    pin_path = tmp_path / "authority-pin.json"
    plan_path.write_text(canonical(plan))
    authority_path.write_text(canonical(authority))
    pin_path.write_text(canonical(pin))
    return subprocess.run(
        [
            str(BIN), "update", "evaluate",
            "--plan", str(plan_path),
            "--authority", str(authority_path),
            "--pin", str(pin_path),
            "--output", str(tmp_path / output_dir),
        ],
        capture_output=True,
        text=True,
        cwd=REPO,
    )


def make_authority(tmp_path: Path, plan: dict, **overrides) -> dict:
    authority = {
        "version": "local-1",
        "kind": "update-authority",
        "plan_digest": digest(plan),
        "bundle_root": str(tmp_path / "consumer"),
        "invocation": {"name": "trusted-ci", "digest": sha_bytes(b"trusted-ci-v0")},
        "allowed_actions": ["evaluate"],
        "environment": {
            "toolchain": "1.98.1",
            "target": "x86_64-unknown-linux-gnu",
        },
        "policy": {"structural": "accretion"},
    }
    authority.update(overrides)
    return authority


def test_evaluate_resolves_authorized_target_offline(tmp_path: Path) -> None:
    root = prepare_consumer(tmp_path)
    before = snapshot(root)
    plan = run_plan(root, tmp_path)

    authority = make_authority(tmp_path, plan)
    proc = run_evaluate(plan, authority, trusted_pin(plan, authority), tmp_path)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    env = json.loads(proc.stdout)
    assert env["command"] == "update-evaluate"
    # Host evidence is gathered here; delivered-update status waits for the
    # integrated checks and is never claimed by this slice.
    assert env["decision"] == "accept"
    assert env["assurance"] == "Unknown"

    report = json.loads((tmp_path / "result" / "report.json").read_text())
    assert report["version"] == "local-1"
    assert report["kind"] == "update-report"
    assert report["package"] == "dept"
    assert report["requested"]["release"] == "2.0.0"
    # The actual selected target is the exact intended release from the
    # approved source artifact.
    assert report["actual"]["version"] == "2.0.0"
    assert report["actual"]["source_digest"] == sha_bytes(
        (root / MIRROR / "dept-2.0.0.crate").read_bytes()
    )
    assert report["disposition"] == "host-evidence"
    assert "delivered" not in json.dumps(report)
    # Integrated checks remain pending in this slice.
    assert "contract-checks" in report["pending_checks"]
    assert "protected-obligations" in report["pending_checks"]

    # The original worktree stays byte-identical and hosts no workspace.
    assert snapshot(root) == before


def test_evaluate_refuses_candidate_supplied_authority(tmp_path: Path) -> None:
    root = prepare_consumer(tmp_path)
    before = snapshot(root)
    plan = run_plan(root, tmp_path)

    authority = make_authority(tmp_path, plan)
    pin = trusted_pin(plan, authority)
    # The candidate rewrites the authority after the trusted invocation
    # pinned its commitment: the pin no longer describes these bytes.
    authority["environment"]["toolchain"] = "9.9.9"
    proc = run_evaluate(plan, authority, pin, tmp_path)
    assert proc.returncode == 1
    env = json.loads(proc.stdout)
    assert env["decision"] == "refuse"
    assert env["assurance"] == "Unknown"
    assert any(
        d.get("code") == "authority-untrusted" for d in env.get("diagnostics", [])
    )
    # Refusal happens before any edit: no report, original worktree intact.
    assert not (tmp_path / "result" / "report.json").exists()
    assert snapshot(root) == before


def test_evaluate_refuses_wrong_selected_target(tmp_path: Path) -> None:
    root = prepare_consumer(tmp_path)
    before = snapshot(root)
    # The plan claims a source artifact the catalog does not back: the
    # trusted invocation pinned this wrong commitment, so evaluation must
    # compare the actually selected artifact and refuse the mismatch.
    plan = run_plan(
        root, tmp_path, source_digest=sha_bytes(b"mismatched-catalog-bytes")
    )
    authority = make_authority(tmp_path, plan)
    proc = run_evaluate(plan, authority, trusted_pin(plan, authority), tmp_path)
    assert proc.returncode == 1
    env = json.loads(proc.stdout)
    assert env["decision"] == "refuse"
    assert any(d.get("code") == "wrong-target" for d in env.get("diagnostics", []))

    report = json.loads((tmp_path / "result" / "report.json").read_text())
    assert report["disposition"] == "refused"
    # Both identities are recorded: requested vs actually selected.
    assert report["requested"]["release"] == "2.0.0"
    assert report["requested"]["source_digest"] == sha_bytes(b"mismatched-catalog-bytes")
    assert report["actual"]["version"] == "2.0.0"
    assert report["actual"]["source_digest"] == sha_bytes(
        (root / MIRROR / "dept-2.0.0.crate").read_bytes()
    )
    assert snapshot(root) == before


def test_evaluate_refuses_unsupported_rust_version(tmp_path: Path) -> None:
    root = prepare_consumer(tmp_path)
    # The otherwise compatible 2.0.0 target declares an unsupported
    # rust-version in the frozen catalog index.
    index = root / MIRROR / "index" / "de" / "pt" / "dept"
    lines = [
        (
            line.replace('"yanked":false}', '"yanked":false,"rust_version":"99.0.0"}')
            if '"vers":"2.0.0"' in line
            else line
        )
        for line in index.read_text().splitlines(keepends=True)
    ]
    index.write_text("".join(lines))
    before = snapshot(root)
    plan = run_plan(root, tmp_path)
    authority = make_authority(tmp_path, plan)
    proc = run_evaluate(plan, authority, trusted_pin(plan, authority), tmp_path)
    assert proc.returncode == 1
    env = json.loads(proc.stdout)
    assert env["decision"] == "refuse"
    # The constraint refuses delivery independently of compatibility.
    assert any(
        d.get("code") == "environment-constraint" for d in env.get("diagnostics", [])
    )
    report = json.loads((tmp_path / "result" / "report.json").read_text())
    assert report["disposition"] == "refused"
    assert "delivered" not in json.dumps(report)
    assert snapshot(root) == before
