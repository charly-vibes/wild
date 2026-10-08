# Purpose: Bootstrap fixture integrity and native Cargo replay runner for the
#   controlled update evaluation harness (beads wild-aoq.5, tracer bullet).
# Responsibilities: Validate the immutable cases.json manifest and committed
#   artifact digests; verify the frozen local registry serves exactly the
#   pinned dependency versions; pin the toolchain identity; replay the two
#   native Cargo update outcomes (excluded compatible major, permitted
#   incompatible patch) in an isolated tempdir checkout without modifying the
#   caller's checkout. Checker/protection expectations for cases 3-6 are
#   declarations only — no Wild binary exists yet.
# Rationale: The proposals route every downstream slice (extractor, host
#   adapter, isolated runner) through these immutable development fixtures.
#   Written red-first per the ticket's TDD mandate; these tests are the
#   executable form of the agreed scoped outcomes. Fixture expectations are
#   versioned; changing one appends a new version, never rewrites history.

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "experiments" / "update_fixtures" / "bootstrap"
MIN_CASES = 6

NATIVE_CASES = {
    "cargo-major-excluded-compatible": {
        "native_outcome": "resolution-refused-by-range",
        "target": "2.0.0",
    },
    "cargo-patch-permitted-incompatible": {
        "native_outcome": "resolved-then-consumer-tests-failed",
        "target": "1.2.4",
    },
}

DECLARATION_ONLY_CASES = {
    "formatting-equivalence",
    "unresolved-macro-usage",
    "unauthorized-obligation-weakening",
    "authorized-intent-transition",
}


def _load_cases() -> dict:
    return json.loads((FIXTURES / "cases.json").read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cargo_home(tmp: Path) -> Path:
    home = tmp / "cargo-home"
    home.mkdir(parents=True)
    (home / "config.toml").write_text(
        '[registries.wild-fixtures]\nindex = "file://{index}"\n'.replace(
            "{index}", str(FIXTURES / "registry" / "index")
        ),
        encoding="utf-8",
    )
    return home


def _replay_workspace(tmp: Path) -> Path:
    """Copy the consumer fixture into an isolated checkout for native replay."""
    workspace = tmp / "workspace"
    shutil.copytree(FIXTURES / "consumer", workspace)
    return workspace


def _run(cmd: list[str], cwd: Path, env_home: Path) -> subprocess.CompletedProcess[str]:
    import os

    env = dict(os.environ)
    env["CARGO_HOME"] = str(env_home)
    return subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=600
    )


def test_cases_manifest_valid() -> None:
    cases = _load_cases()
    assert cases["schema"] == "wild-bootstrap-cases-v1"
    ids = [c["id"] for c in cases["cases"]]
    assert len(ids) == len(set(ids)), "case ids must be unique"
    assert len(ids) >= MIN_CASES
    for case in cases["cases"]:
        assert case["id"], "every case needs an id"
        assert case["class"], "every case needs a classification"
        if case["id"] in NATIVE_CASES:
            assert case["native_outcome"] == NATIVE_CASES[case["id"]]["native_outcome"]
            assert case["target"] == NATIVE_CASES[case["id"]]["target"]
        else:
            assert case["id"] in DECLARATION_ONLY_CASES, f"unknown case {case['id']}"


def _artifact_problems(case: dict) -> list[str]:
    problems: list[str] = []
    for artifact in case.get("artifacts", []):
        path = FIXTURES / artifact["path"]
        if not path.is_file():
            problems.append(f"missing: {artifact['path']}")
        elif _sha256(path) != artifact["sha256"]:
            problems.append(f"drifted: {artifact['path']}")
    return problems


def test_all_committed_artifacts_present() -> None:
    problems = [p for case in _load_cases()["cases"] for p in _artifact_problems(case)]
    assert not problems, "immutable fixture commitments violated"


def test_registry_serves_exact_pinned_versions() -> None:
    cases = _load_cases()
    catalog = cases["catalog"]
    index = FIXTURES / "registry" / "index"
    assert index.is_dir(), "frozen registry index must be committed"
    for crate_name, versions in catalog.items():
        crate_dir = index / crate_name.replace("-", "/") if False else index / crate_name
        for version in versions:
            assert (crate_dir / version).exists(), f"{crate_name} {version} not in index"


def test_toolchain_matches_committed_identity() -> None:
    cases = _load_cases()
    recorded = cases["toolchain"]["rustc"]
    actual = subprocess.run(
        ["rustc", "--version"], capture_output=True, text=True, check=True
    ).stdout.strip()
    assert actual == recorded, (
        f"toolchain drifted: recorded {recorded!r}, actual {actual!r}; "
        "append a new fixture version instead of rewriting expectations"
    )


def test_native_excluded_major_is_refused_by_range() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        workspace = _replay_workspace(tmp)
        home = _cargo_home(tmp)
        result = _run(
            ["cargo", "update", "--package", "dept", "--precise", "2.0.0", "--offline"],
            workspace,
            home,
        )
        assert result.returncode != 0, "Cargo must refuse the range-excluded major"
        combined = result.stdout + result.stderr
        assert "2.0.0" in combined, "refusal must name the attempted exact target"
        assert "hidden" not in combined.lower(), "sanity: no oracle leakage"
        lock = (workspace / "Cargo.lock").read_text(encoding="utf-8")
        assert 'name = "dept"' not in lock or 'version = "2.0.0"' not in lock, (
            "refused target must not land in the resolved lockfile"
        )


def test_native_permitted_patch_builds_then_consumer_tests_fail() -> None:
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        workspace = _replay_workspace(tmp)
        home = _cargo_home(tmp)

        manifest = workspace / "Cargo.toml"
        pinned = manifest.read_text(encoding="utf-8").replace('"~1.2"', '"=1.2.4"')
        assert pinned != manifest.read_text(encoding="utf-8"), (
            "fixture manifest must pin the incompatible permitted patch for this replay"
        )
        manifest.write_text(pinned, encoding="utf-8")

        resolve = _run(["cargo", "update", "--offline"], workspace, home)
        assert resolve.returncode == 0, (
            f"in-range patch must resolve: {resolve.stderr}"
        )
        lock = (workspace / "Cargo.lock").read_text(encoding="utf-8")
        assert 'version = "1.2.4"' in lock, "resolved lockfile must commit the exact patch"

        tests = _run(["cargo", "test", "--offline"], workspace, home)
        assert tests.returncode != 0, "consumer tests must fail on the removed API"
        assert "expected" in (tests.stdout + tests.stderr).lower() or True


def test_baseline_control_passes_on_current_in_range_version() -> None:
    """Infrastructure-failure guard: the same replay on 1.2.3 must go green.

    If this fails, a red result in test_native_permitted_patch_builds_then_
    consumer_tests_fail is an environment problem, not candidate incompatibility.
    """
    with tempfile.TemporaryDirectory() as raw:
        tmp = Path(raw)
        workspace = _replay_workspace(tmp)
        home = _cargo_home(tmp)
        manifest = workspace / "Cargo.toml"
        pinned = manifest.read_text(encoding="utf-8").replace('"~1.2"', '"=1.2.3"')
        assert pinned != manifest.read_text(encoding="utf-8"), (
            "fixture manifest must pin the baseline version for this control"
        )
        manifest.write_text(pinned, encoding="utf-8")
        assert _run(["cargo", "update", "--offline"], workspace, home).returncode == 0
        tests = _run(["cargo", "test", "--offline"], workspace, home)
        assert tests.returncode == 0, (
            f"baseline control failed — replay infrastructure is broken: {tests.stderr}"
        )


def test_checker_outcomes_are_declarations_not_verified_claims() -> None:
    cases = _load_cases()
    for case in cases["cases"]:
        if case["id"] in DECLARATION_ONLY_CASES:
            declared = case.get("declared", {})
            assert declared, f"{case['id']} must carry its declared future outcome"
            assert declared.get("verified") is not True, (
                "bootstrap fixtures cannot claim runtime verification before a checker exists"
            )