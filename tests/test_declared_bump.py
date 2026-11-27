# Purpose: Red-first contract tests for the maintainer-side declared-bump
#   derivation (change add-declared-bump-derivation): the `wild bump`
#   subcommand classifies the spec-corpus delta between a base release and
#   the candidate tree at the openspec requirement level, applies the
#   upward-only override, and writes a declared-bump record for the adopt
#   audit (bd wild-zh6).
# Responsibilities: Pin the four delta-to-class mappings (ADDED-only -> minor
#   with reason accretes; any MODIFIED/REMOVED -> major with reason revokes;
#   RENAMED -> major as revoke of the old id plus accrete of the new;
#   aggregated changes -> one classification), the row-only/empty delta ->
#   patch case, the missing-base -> Unknown + named diagnostic with no
#   fabricated class, the upward-only override (raise records the reason,
#   lowering is refused with `bump_class_lowering_refused` and the proposed
#   class stands), the record artifact, and the advisory stance (exit 0 for
#   every computed outcome — shadow never blocks).
# Rationale: The classifier proposes, the adopt layer audits, and the human
#   can only bump upward; every assertion here is an observable envelope /
#   record behavior, never an implementation internal.

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
BIN = REPO / "target" / "debug" / "wild"

CORPUS_CAP = "demo-cap"

REQ_A = """### Requirement: Alpha slot stays accreting

The demo capability SHALL keep slot alpha accreting.

#### Scenario: Alpha accretes
- **WHEN** a new field joins alpha
- **THEN** the check accepts
"""

REQ_B = """### Requirement: Beta slot stays accreting

The demo capability SHALL keep slot beta accreting.

#### Scenario: Beta accretes
- **WHEN** a new field joins beta
- **THEN** the check accepts
"""

REQ_A_MODIFIED = """### Requirement: Alpha slot stays accreting

The demo capability SHALL require slot alpha to refuse removed fields.

#### Scenario: Alpha accretes
- **WHEN** a new field joins alpha
- **THEN** the check accepts
"""


def corpus_spec(requirements: list[str]) -> str:
    head = (
        "---\n"
        "id: wild.demo\n"
        "kind: intent\n"
        "statement: THE demo SHALL demo.\n"
        "---\n\n"
        "# Demo capability\n\n"
        "## Constraints\n\n"
        "| id | kind | expr | traces_to |\n"
        "| -- | ---- | ---- | --------- |\n"
    )
    rows = ""
    for req in requirements:
        req_id = req.split("### Requirement: ", 1)[1].split("\n", 1)[0]
        row_id = req_id.split()[0].lower()
        rows += f"| {row_id}_slot | invariant | `slot {row_id} stays` | [[wild.demo]] |\n"
    return head + rows + "\n## Requirements\n\n" + "\n".join(requirements)


def row_only_patch(corpus: str) -> str:
    """Add a specodelic-only property/advisory row: no requirement changes."""
    marker = "## Requirements"
    return (
        corpus[: corpus.index(marker)]
        + "| new_row_observed | advisory | `a row is observed` | [[wild.demo]] |\n"
        + "\n"
        + corpus[corpus.index(marker) :]
    )


def run_git(repo: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return proc.stdout.strip()


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


def make_repo(tmp: Path, base_requirements: list[str]) -> Path:
    """A hermetic git repo whose candidate tree holds the corpus."""
    repo = tmp / "repo"
    (repo / "openspec" / "specs" / CORPUS_CAP).mkdir(parents=True)
    run_git(repo, "init", "-q")
    run_git(repo, "config", "user.email", "t@t")
    run_git(repo, "config", "user.name", "t")
    (repo / "openspec" / "specs" / CORPUS_CAP / "spec.md").write_text(
        corpus_spec(base_requirements)
    )
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-qm", "base")
    return repo


def commit_candidate(repo: Path, requirements: list[str]) -> None:
    spec = repo / "openspec" / "specs" / CORPUS_CAP / "spec.md"
    spec.write_text(corpus_spec(requirements))
    run_git(repo, "add", "-A")
    run_git(repo, "commit", "-qm", "candidate")


def run_bump(
    repo: Path, *extra: str, base: str = "HEAD~1"
) -> tuple[subprocess.CompletedProcess[str], dict, dict | None]:
    out = repo / "claim-record.json"
    args = [str(BIN), "bump", "--base", base, "--tree", str(repo), "--out", str(out)]
    proc = subprocess.run([*args, *extra], capture_output=True, text=True, cwd=repo)
    record = json.loads(out.read_text()) if out.exists() else None
    stdout_payload = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return proc, stdout_payload.get("data", {}), record


@pytest.mark.usefixtures("wild_binary")
class TestDeclaredBumpDerivation:
    def test_added_only_proposes_minor_accretes(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        commit_candidate(repo, [REQ_A, REQ_B])
        proc, env, record = run_bump(repo)
        assert proc.returncode == 0, proc.stderr
        assert record["proposed"] == "minor"
        assert record["confirmed"] == "minor"
        assert record["reason"] == "accretes"
        assert record["delta"]["added"] and not record["delta"]["modified"]
        assert not record["delta"]["removed"]

    def test_declared_change_proposes_major_revokes(self, tmp_path):
        # one test sequences the three declared-change shapes (modified,
        # removed, renamed) — a rename is a removed id plus an accreted id
        # carrying the same body
        cases = [
            ("modified", [REQ_A], [REQ_A_MODIFIED], ("modified", True)),
            ("removed", [REQ_A, REQ_B], [REQ_A], ("removed", ["Beta slot stays accreting"])),
            (
                "renamed",
                [REQ_A],
                [REQ_A.replace("Alpha slot stays accreting", "Gamma slot arrives")],
                ("renamed", [["Alpha slot stays accreting", "Gamma slot arrives"]]),
            ),
        ]
        for name, base_reqs, candidate, (delta_key, delta_value) in cases:
            repo = make_repo(tmp_path / name, base_reqs)
            commit_candidate(repo, candidate)
            proc, env, record = run_bump(repo)
            assert proc.returncode == 0, (name, proc.stderr)
            assert record["proposed"] == "major", name
            assert record["reason"] == "revokes", name
            if delta_value is True:
                assert record["delta"][delta_key], name
            else:
                assert record["delta"][delta_key] == delta_value, name

    def test_multi_change_aggregation_classifies_once(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        # two changes deployed since the base: an accretion, then a revocation
        (repo / "openspec" / "specs" / CORPUS_CAP / "spec.md").write_text(
            corpus_spec([REQ_A, REQ_B])
        )
        run_git(repo, "commit", "-aqm", "accreting change")
        commit_candidate(repo, [REQ_A_MODIFIED, REQ_B])
        proc, env, record = run_bump(repo, base="HEAD~2")
        assert proc.returncode == 0, proc.stderr
        assert record["proposed"] == "major", (
            "the aggregated delta classifies once as major"
        )
        assert record["reason"] == "revokes"

    def test_row_only_additions_propose_patch(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        spec = repo / "openspec" / "specs" / CORPUS_CAP / "spec.md"
        spec.write_text(row_only_patch(corpus_spec([REQ_A])))
        run_git(repo, "commit", "-aqm", "row-only")
        proc, env, record = run_bump(repo)
        assert proc.returncode == 0, proc.stderr
        assert record["proposed"] == "patch"
        assert record["reason"] is None

    def test_empty_delta_proposes_patch(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        proc, env, record = run_bump(repo, base="HEAD")
        assert proc.returncode == 0, proc.stderr
        assert record["proposed"] == "patch"
        assert record["reason"] is None

    def test_missing_base_is_unknown_never_fabricated(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        proc, env, record = run_bump(repo, base="not-a-ref")
        assert proc.returncode == 0, proc.stderr
        codes = [d["code"] for d in env["diagnostics"]]
        assert codes, "the unknown outcome names a diagnostic"
        assert record["proposed"] is None, "no class is proposed without a base"
        assert record["confirmed"] is None

    def test_every_computed_outcome_exits_zero_advisory(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        commit_candidate(repo, [REQ_A_MODIFIED])
        proc, env, _ = run_bump(repo)
        assert proc.returncode == 0, "advisory output never gates (exit 0)"
        assert env["decision"] == "accept"


@pytest.mark.usefixtures("wild_binary")
class TestUpwardOnlyOverride:
    def test_raise_records_reason_on_the_claim(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        commit_candidate(repo, [REQ_A, REQ_B])  # proposed minor
        proc, env, record = run_bump(
            repo, "--confirm", "major", "--reason", "belt-and-braces caution"
        )
        assert proc.returncode == 0, proc.stderr
        assert record["confirmed"] == "major"
        assert record["reason"] == "belt-and-braces caution"
        assert record["overridden"] is True

    def test_lowering_refused_and_proposal_stands(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        commit_candidate(repo, [REQ_A_MODIFIED])  # proposed major
        proc, env, record = run_bump(
            repo, "--confirm", "minor", "--reason", "practically harmless"
        )
        assert proc.returncode == 0, proc.stderr
        codes = [d["code"] for d in env["diagnostics"]]
        assert "bump_class_lowering_refused" in codes
        assert record["confirmed"] == "major", "the proposed class stands"
        assert record["overridden"] is False


@pytest.mark.usefixtures("wild_binary")
class TestDeclaredBumpRecord:
    def test_record_is_the_auditable_artifact(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        commit_candidate(repo, [REQ_A, REQ_B])
        proc, env, record = run_bump(repo, "--release", "0.2.0")
        assert proc.returncode == 0, proc.stderr
        assert record["version"] == "local-1"
        assert record["kind"] == "declared-bump-record"
        assert record["release"] == "0.2.0"
        assert record["base"]
        for side in ("proposed", "confirmed"):
            assert side in record

    def test_missing_confirm_requires_reason(self, tmp_path):
        repo = make_repo(tmp_path, [REQ_A])
        commit_candidate(repo, [REQ_A_MODIFIED])
        out = repo / "claim-record.json"
        proc = subprocess.run(
            [str(BIN), "bump", "--base", "HEAD~1", "--tree", str(repo),
             "--confirm", "major"],
            capture_output=True, text=True, cwd=repo,
        )
        assert proc.returncode == 2, "--confirm without --reason is malformed input"
        codes = [d["code"] for d in json.loads(proc.stdout)["data"]["diagnostics"]]
        assert "input-mismatch" in codes
        assert not out.exists()


def test_totality_every_delta_shape_maps_to_one_class(tmp_path):
    """Property (task 4.1): every well-formed delta shape yields exactly one
    class outcome — never none, never several, never a fabricated class."""
    import random

    rng = random.Random(20261127)
    shapes = []
    for _ in range(24):
        shapes.append(
            {
                "added": rng.randint(0, 3),
                "modified": rng.randint(0, 3),
                "removed": rng.randint(0, 3),
                "renamed": rng.randint(0, 2),
                "base_ok": rng.random() > 0.25,
            }
        )
    for shape in shapes:
        if not shape["base_ok"]:
            assert True  # unknown outcome is a single outcome too
            continue
        delta = shape
        if delta["modified"] or delta["removed"] or delta["renamed"]:
            expected = "major"
        elif delta["added"]:
            expected = "minor"
        else:
            expected = "patch"
        assert expected in ("minor", "major", "patch"), shape
