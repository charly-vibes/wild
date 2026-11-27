# Purpose: Command-level test for the `wild feedback` subcommand (beads
#   wild-8g8, adopting the genesis::feedback contract: valid kinds
#   bug/feature/question/chore/aix-gap, stdin title/body derivation,
#   redaction, and a local report file as the network-free filing
#   outcome). Assert observable output and exit codes, never
#   implementation internals.
# Rationale: The feedback subcommand must be additive: its output goes
#   through the same emit() funnel as every other command (genesis
#   envelope shell on stdout, bd wild-lof), a dry run or a written report
#   accepts with exit 0, and an unknown kind is an error envelope with
#   exit 2. Human-readable previews go to stderr so stdout stays a single
#   JSON shell.

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
BIN = REPO / "target" / "debug" / "wild"


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


def run_feedback(
    args: list[str], stdin: str | None = None, cache: Path | None = None
) -> subprocess.CompletedProcess[str]:
    env = {"PATH": "/usr/bin:/bin:/usr/local/bin", "HOME": "/nonexistent-feedback-home"}
    if cache is not None:
        env["XDG_CACHE_HOME"] = str(cache)
    return subprocess.run(
        [str(BIN), "feedback", *args],
        input=stdin,
        capture_output=True,
        text=True,
        cwd=REPO,
        env=env,
    )


def shell(proc: subprocess.CompletedProcess[str]) -> dict:
    return json.loads(proc.stdout)


class TestFeedbackHappyPath:
    def test_dry_run_accepts_with_envelope_and_stderr_preview(self):
        proc = run_feedback(["bug", "--dry-run"], stdin="crash on check\nit fails badly\n")
        assert proc.returncode == 0
        sh = shell(proc)
        assert sh["ok"] is True
        assert sh["envelope_kind"] == "ok"
        assert sh["data"]["decision"] == "accept"
        assert sh["data"]["command"] == "feedback"
        # stderr carries the human-readable preview; stdout stays the shell
        assert "[bug] crash on check" in proc.stderr
        assert "Would file: gh issue create --repo charly-vibes/wild" in proc.stderr

    def test_single_line_stdin_uses_generic_title(self):
        proc = run_feedback(["bug", "--dry-run"], stdin="plain one-liner\n")
        assert proc.returncode == 0
        assert "[bug] feedback report" in proc.stderr
        assert "plain one-liner" in proc.stderr

    def test_writes_local_report_file(self, tmp_path):
        cache = tmp_path / "cache"
        proc = run_feedback(["bug"], stdin="check refuses valid input\n", cache=cache)
        assert proc.returncode == 0
        assert shell(proc)["data"]["decision"] == "accept"
        reports = list((cache / "wild" / "reports").glob("report-*.md"))
        assert len(reports) == 1, "exactly one report written under $XDG_CACHE_HOME/wild/reports"
        body = reports[0].read_text()
        assert "check refuses valid input" in body
        assert "## Environment" in body
        assert "- tool: wild" in body
        # the report path is announced on stderr, never on stdout
        assert str(reports[0]) in proc.stderr
        assert not proc.stdout.startswith("#")

    def test_title_flag_overrides_derived_title(self):
        proc = run_feedback(
            ["bug", "--title", "custom title", "--dry-run"], stdin="body text\n"
        )
        assert proc.returncode == 0
        assert "[bug] custom title" in proc.stderr


class TestFeedbackInvalidUsage:
    def test_unknown_kind_is_error_envelope_exit_two(self):
        proc = run_feedback(["bogus"], stdin="content\n")
        assert proc.returncode == 2
        sh = shell(proc)
        assert sh["ok"] is False
        assert sh["envelope_kind"] == "error"
        assert sh["data"]["decision"] == "error"
        reason = sh["data"]["diagnostics"][0]["reason"]
        assert "unknown kind: 'bogus'" in reason
        assert "Valid kinds: bug, feature, question, chore, aix-gap" in reason

    def test_missing_kind_refuses_with_usage_exit_two(self):
        proc = run_feedback([])
        assert proc.returncode == 2
        sh = shell(proc)
        assert sh["data"]["decision"] == "refuse"
        assert "usage: wild feedback <kind>" in sh["data"]["diagnostics"][0]["reason"]

    def test_unknown_flag_refuses_exit_two(self):
        proc = run_feedback(["bug", "--bogus-flag"], stdin="x\n")
        assert proc.returncode == 2
        sh = shell(proc)
        assert sh["data"]["decision"] == "refuse"

    def test_empty_stdin_without_from_last_error_errors(self):
        proc = run_feedback(["bug"], stdin="")
        assert proc.returncode == 2
        sh = shell(proc)
        assert sh["ok"] is False
        reason = sh["data"]["diagnostics"][0]["reason"]
        assert "No issue content specified" in reason

    def test_from_last_error_without_scratch_record_errors(self, tmp_path):
        cache = tmp_path / "empty-cache"
        proc = run_feedback(["bug", "--from-last-error"], cache=cache)
        assert proc.returncode == 2
        sh = shell(proc)
        reason = sh["data"]["diagnostics"][0]["reason"]
        assert "No recent error recorded for 'wild'" in reason
