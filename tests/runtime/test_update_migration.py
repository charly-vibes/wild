# Purpose: Red-first command-level runtime tests for the supplied-migration
#   slice (beads wild-nic.4, change add-consumer-update-workflow): a caller
#   submits a consumer/adapter patch as a separately committed update plan
#   and obtains a validated migration diff — without rewriting the original
#   intended outcomes.
# Responsibilities: Assemble the e5 migration fixture, plan the exact
#   candidate with a `migration_patch` map bound by `migration_digest`, pin
#   the external authority, and run evaluation as a subprocess against real
#   Cargo. Pin the scenarios owned by this slice from the spec delta:
#   (a) an update that passes only after a supplied consumer-code patch is
#   delivered with that patch included and reports `migration`, never
#   direct; (b) a migration that deletes a protected consumer test is
#   refused (`protected-obligation-removed`) — the removed assertion is not
#   preserved behavior and cannot manufacture a direct-update success;
#   (c) the same removal under an explicitly authorized intent transition is
#   delivered as `intent-change`, separately labelled and excluded from
#   backward-compatible direct results; (d) a plan whose migration digest
#   does not bind the committed patch files is refused.
# Rationale: The slice's acceptance requires actual Cargo builds/tests and
#   durable output, not canned success responses. The unpatched consumer is
#   also evaluated to prove the migration is necessary. Assertions mirror
#   observable records, never internals.

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from test_direct_update import (
    assemble_consumer,
    canonical,
    contract_for,
    digest,
    migration_digest,
    run_evaluate,
    run_plan,
    sha_bytes,
    snapshot,
    trusted_pin,
)
from test_extract import BIN, REPO


def make_authority_at(tmp_path: Path, plan: dict, bundle: str, actions: list[str]) -> dict:
    return {
        "version": "local-1",
        "kind": "update-authority",
        "plan_digest": digest(plan),
        "bundle_root": str(tmp_path / bundle),
        "invocation": {"name": "trusted-ci", "digest": sha_bytes(b"trusted-ci-v0")},
        "allowed_actions": actions,
        "environment": {"toolchain": "1.98.1", "target": "x86_64-unknown-linux-gnu"},
        "policy": {"structural": "complete-structure"},
    }


def evaluate_migration(
    tmp_path: Path,
    release: str,
    patch: dict[str, str | None],
    actions: list[str],
    dirname: str,
):
    """Plan and evaluate one migration scenario against its own consumer copy."""
    root = assemble_consumer("migration-supplied", tmp_path / dirname)
    scratch = tmp_path / (dirname + "-scratch")
    scratch.mkdir(parents=True, exist_ok=True)
    before = snapshot(root)
    plan = run_plan(root, scratch, release, contract_for(release), migration=patch)
    authority = make_authority_at(tmp_path, plan, dirname, actions)
    proc, result_dir = run_evaluate(plan, authority, trusted_pin(plan, authority), scratch)
    report_path = result_dir / "report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else None
    return proc, report, result_dir, before, root, plan


REPAIR_PATCH = {"tests/farewell.rs": "migration/farewell.rs.v2"}


def test_consumer_repair_migration_is_labelled_migration(tmp_path: Path) -> None:
    proc, report, result_dir, before, root, plan = evaluate_migration(
        tmp_path, "2.1.0", REPAIR_PATCH, ["evaluate"], "consumer"
    )
    # The plan carries the supplied migration and extends the allowed paths.
    assert plan["migration"]["digest"] == migration_digest(REPAIR_PATCH, root)
    assert plan["migration"]["patch"] == REPAIR_PATCH
    assert plan["allowed_changed_paths"] == [
        "Cargo.toml", "Cargo.lock", "tests/farewell.rs",
    ]
    # The unpatched consumer cannot deliver: the migration is necessary.
    proc0, report0, result0, before0, root0, _ = evaluate_migration(
        tmp_path, "2.1.0", None, ["evaluate"], "consumer-unpatched"
    )
    assert proc0.returncode == 1, proc0.stdout + proc0.stderr
    assert report0["disposition"] == "refused"
    assert any(d["code"] == "consumer-break" for d in report0["diagnostics"])
    assert before0 == snapshot(root0)
    # The patched consumer is delivered as a migration, not a direct update.
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "delivered"
    assert report["update_class"] == "migration"
    assert report["update_class"] != "direct"
    assert report["actual"]["version"] == "2.1.0"
    # The report includes the supplied patch and every consumer/adapter edit.
    assert report["migration"]["digest"] == migration_digest(REPAIR_PATCH, root)
    paths = [d["path"] for d in report["diff"]]
    assert set(paths) == {"Cargo.toml", "Cargo.lock", "tests/farewell.rs"}
    entry = next(d for d in report["diff"] if d["path"] == "tests/farewell.rs")
    v2 = (root / "migration" / "farewell.rs.v2").read_bytes()
    baseline = (root / "tests" / "farewell.rs").read_bytes()
    assert entry["before_digest"] == sha_bytes(baseline)
    assert entry["after_digest"] == sha_bytes(v2)
    # The migrated test still carries the protected assertion shape.
    assert b"#[test]" in v2 and b"assert" in v2
    # Durable pinned output includes the migrated file.
    pinned = result_dir / "pinned" / "tests" / "farewell.rs"
    assert pinned.is_file()
    assert pinned.read_bytes() == v2
    assert sha_bytes(pinned.read_bytes()) == entry["after_digest"]
    # The original worktree remains unchanged.
    assert before == snapshot(root)


def test_removed_assertion_cannot_deliver_without_intent_authority(tmp_path: Path) -> None:
    proc, report, result_dir, before, root, plan = evaluate_migration(
        tmp_path, "2.1.0", {"tests/farewell.rs": None}, ["evaluate"], "consumer"
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "refused"
    # No direct-update success was manufactured: no update_class claim and
    # no delivered diff accompany the refusal.
    assert report.get("update_class") != "direct"
    assert not report.get("diff")
    assert any(
        d["code"] == "protected-obligation-removed" for d in report["diagnostics"]
    )
    # The refusal preserves the requested and actual identities and the
    # original evidence: the deletion manufactured no delivered update.
    assert report["requested"]["release"] == "2.1.0"
    assert report["actual"]["version"] == "2.1.0"
    assert not (result_dir / "pinned").exists()
    assert before == snapshot(root)


def test_authorized_intent_transition_is_separately_labelled(tmp_path: Path) -> None:
    proc, report, result_dir, before, root, plan = evaluate_migration(
        tmp_path, "2.1.0", {"tests/farewell.rs": None},
        ["evaluate", "intent-change"], "consumer",
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert report is not None
    assert report["disposition"] == "delivered"
    # Intentional obligation transitions are excluded from backward-
    # compatible direct results.
    assert report["update_class"] == "intent-change"
    assert report["update_class"] != "direct"
    assert report["actual"]["version"] == "2.1.0"
    # The removal is recorded in the diff with a null after-digest.
    entry = next(d for d in report["diff"] if d["path"] == "tests/farewell.rs")
    assert entry["after_digest"] is None
    assert not (result_dir / "pinned" / "tests" / "farewell.rs").exists()
    assert (result_dir / "pinned" / "Cargo.toml").is_file()
    assert before == snapshot(root)


def test_plan_refuses_a_migration_digest_that_binds_nothing(tmp_path: Path) -> None:
    root = assemble_consumer("migration-supplied", tmp_path / "consumer")
    request = {
        "version": "local-1",
        "kind": "update-request",
        "bundle_root": str(root),
        "files": {
            p.relative_to(root).as_posix(): sha_bytes(p.read_bytes())
            for p in sorted(root.rglob("*")) if p.is_file()
        },
        "manifest": "Cargo.toml",
        "package": "dept",
        "release": "2.1.0",
        "source_digest": sha_bytes((root / "registry-mirror" / "dept-2.1.0.crate").read_bytes()),
        "target": "x86_64-unknown-linux-gnu",
        "toolchain": "1.98.1",
        "features": [],
        "consumer": "consumer",
        "policy": {"structural": "complete-structure"},
        "catalog": {"kind": "local-fixture", "digest": sha_bytes(b"catalog-snapshot-v0")},
        "planner": {"name": "wild", "digest": sha_bytes(b"wild-planner-v0")},
        "contracts": contract_for("2.1.0"),
        "migration_patch": REPAIR_PATCH,
        "migration_digest": digest({"unbound": None}),
    }
    request_path = tmp_path / "update-request.json"
    request_path.write_text(canonical(request))
    output = tmp_path / "plan.json"
    proc = subprocess.run(
        [str(BIN), "update", "plan", "--request", str(request_path), "--output", str(output)],
        capture_output=True, text=True, cwd=REPO,
    )
    assert proc.returncode != 0
    assert "migration" in proc.stdout
    assert not output.exists()
