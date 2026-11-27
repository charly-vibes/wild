# Purpose: Red-first test for the consecutive-release verdict audit driver
#   (beads wild-cdp.2): experiments/wild_adopt_audit.py replaying a crate's
#   release history through `wild extract` + consecutive-release `wild check`
#   and auditing each declared semver bump against the computed verdict.
# Responsibilities: Feed the driver a synthetic 3-release corpus through the
#   --sources override (network never touched) and pin the audit semantics:
#   a minor bump that removes a demanded public fn audits as DISAGREEMENT, a
#   patch bump with an unchanged public surface audits consistent, the run
#   writes a results file and exits 0, and an offline run without sources
#   fails with a named diagnostic instead of synthesizing history. Assert
#   observable audit rows and exit codes, never driver internals.
# Rationale: The audit's acceptance is honest verdict provenance — every row
#   must come from a real `wild check` invocation, so the test pins the
#   verdict classes against verdicts the real binary actually computes.
#   Written before the driver exists; every test here must fail red on the
#   missing driver and stay green once the driver lands.

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
DRIVER = REPO / "experiments" / "wild_adopt_audit.py"
BIN = REPO / "target" / "debug" / "wild"

CRATE = "provider"

# 0.2.0 removes `greet`, which the generated caller demanded at 0.1.0; the
# declared minor bump claims compatibility — wild must compute a break.
# 0.2.1 changes nothing public, so the patch pair must audit consistent.
V010_LIB = """pub fn add_one(x: u32) -> u32 { x + 1 }
pub fn greet(x: u32) -> u32 { x + 2 }
"""
V020_LIB = """pub fn add_one(x: u32) -> u32 { x + 1 }
"""
V021_LIB = """pub fn add_one(x: u32) -> u32 { x + 1 }
// internal-only comment change; public surface identical to 0.2.0
"""

TOML = '[package]\nname = "provider"\nversion = "{v}"\nedition = "2021"\n'

CORPUS = (("0.1.0", V010_LIB), ("0.2.0", V020_LIB), ("0.2.1", V021_LIB))


def make_sources(root: Path) -> Path:
    for ver, lib in CORPUS:
        crate_dir = root / ver / CRATE
        (crate_dir / "src").mkdir(parents=True)
        (crate_dir / "Cargo.toml").write_text(TOML.format(v=ver))
        (crate_dir / "src" / "lib.rs").write_text(lib)
    return root


def run_driver(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DRIVER), *args], capture_output=True, text=True, cwd=REPO
    )


@pytest.fixture(scope="module")
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
class TestAdoptAuditDriver:
    def test_synthetic_corpus_verdicts_match_semver_expectations(self, tmp_path):
        sources = make_sources(tmp_path / "sources")
        out = tmp_path / "audit.txt"
        proc = run_driver(
            ["--crate", CRATE, "--sources", str(sources), "--out", str(out),
             "--bin", str(BIN)]
        )
        assert proc.returncode == 0, proc.stderr
        rows = json.loads(proc.stdout)
        assert len(rows) == 2, "two consecutive pairs from three releases"
        by_next = {r["next"]: r for r in rows}

        minor = by_next["0.2.0"]
        assert minor["bump_kind"] == "minor"
        assert minor["computed_verdict"] == "reject", (
            "a removed demanded fn is a computed break"
        )
        assert minor["audit_row"] == "disagreement", (
            "semver claimed compatible (minor bump), wild computed a break"
        )

        patch = by_next["0.2.1"]
        assert patch["bump_kind"] == "patch"
        assert patch["computed_verdict"] == "accept"
        assert patch["audit_row"] == "consistent"

        text = out.read_text()
        assert "DISAGREEMENT" in text, "the headline finding class is rendered"
        assert "consistent" in text
        assert "exit" in text, "every subprocess echo carries its exit code"

    def test_offline_without_sources_fails_with_named_diagnostic(self, tmp_path):
        out = tmp_path / "audit.txt"
        proc = run_driver(
            ["--crate", CRATE, "--out", str(out), "--offline", "--bin", str(BIN)]
        )
        assert proc.returncode != 0, "offline with no sources must fail loudly"
        combined = (proc.stderr + proc.stdout).lower()
        assert "offline" in combined, (
            "the failure must name the diagnostic, never synthesize history"
        )
        assert not out.exists() or "0.1.0" not in out.read_text(), (
            "no synthetic substitution of real history"
        )


# --- declared bump claims (change add-declared-bump-derivation, wild-zh6) ---
# The declared side the audit compares is now delta-derived: `wild bump`
# writes declared-bump-record artifacts, and the driver takes them as
# --claims (JSON map release -> record). Releases without a recorded
# declaration stay Unknown claims, excluded from agreement counts.



def make_claims_file(path: Path, claims: dict) -> Path:
    path.write_text(json.dumps(claims, indent=1))
    return path


@pytest.mark.usefixtures("wild_binary")
class TestDeclaredClaimRecord:
    def test_recorded_claim_is_compared_never_reconciled(self, tmp_path):
        sources = make_sources(tmp_path / "sources")
        out = tmp_path / "audit.txt"
        claims = make_claims_file(
            tmp_path / "claims.json",
            {
                "0.2.0": {
                    "proposed": "minor",
                    "confirmed": "minor",
                    "reason": "accretes",
                }
            },
        )
        before = claims.read_text()
        proc = run_driver(
            ["--crate", CRATE, "--sources", str(sources), "--out", str(out),
             "--bin", str(BIN), "--claims", str(claims)]
        )
        assert proc.returncode == 0, proc.stderr
        rows = json.loads(proc.stdout)
        minor = next(r for r in rows if r["next"] == "0.2.0")
        assert minor["declared_claim"] == "minor"
        assert minor["computed_verdict"] == "reject"
        assert minor["claim_row"] == "disagreement", (
            "declared minor against a computed revocation is a disagreement"
        )
        assert claims.read_text() == before, (
            "the audit never rewrites the declared record"
        )
        assert "DISAGREEMENT" in out.read_text()

    def test_absent_claim_stays_unknown_and_excluded_from_counts(self, tmp_path):
        sources = make_sources(tmp_path / "sources")
        out = tmp_path / "audit.txt"
        claims = make_claims_file(tmp_path / "claims.json", {})
        proc = run_driver(
            ["--crate", CRATE, "--sources", str(sources), "--out", str(out),
             "--bin", str(BIN), "--claims", str(claims)]
        )
        assert proc.returncode == 0, proc.stderr
        rows = json.loads(proc.stdout)
        assert all(r["declared_claim"] == "unknown" for r in rows)
        assert all(r["claim_row"] == "unknown" for r in rows)
        text = out.read_text()
        assert "declared agreements: 0" in text
        assert "declared disagreements: 0" in text, (
            "absent claims are excluded from agreement counts, never folded in"
        )

    def test_agreement_is_listed_when_declared_matches_verdict(self, tmp_path):
        sources = make_sources(tmp_path / "sources")
        out = tmp_path / "audit.txt"
        claims = make_claims_file(
            tmp_path / "claims.json",
            {"0.2.1": {"proposed": "patch", "confirmed": "patch", "reason": ""}},
        )
        proc = run_driver(
            ["--crate", CRATE, "--sources", str(sources), "--out", str(out),
             "--bin", str(BIN), "--claims", str(claims)]
        )
        assert proc.returncode == 0, proc.stderr
        rows = json.loads(proc.stdout)
        patch = next(r for r in rows if r["next"] == "0.2.1")
        assert patch["computed_verdict"] == "accept"
        assert patch["claim_row"] == "agreement"
        assert "declared agreements: 1" in out.read_text()
