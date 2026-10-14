# Purpose: Command-level test for the fleet version probe (beads wild-9sm).
# Responsibilities: Pin that `wild --version` prints a plain version line
#   and exits 0 — ddl's generic version probe runs `$binary --version` and
#   currently finds nothing (wild exits 2 printing the JSON refusal
#   envelope, so ddl status shows wild as "v?"). Assert observable output
#   and exit codes, never implementation internals.
# Rationale: The probe contract is the ecosystem convention: plain
#   `--version` output with exit 0. The version string must match the
#   package version so probe-based inventory stays truthful.

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
BIN = REPO / "target" / "debug" / "wild"

PACKAGE_VERSION = (
    (REPO / "Cargo.toml")
    .read_text()
    .split('[package]', 1)[1]
    .split('version = "', 1)[1]
    .split('"', 1)[0]
)


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
class TestVersionProbe:
    def test_dash_dash_version_prints_plain_line_exit_zero(self):
        proc = subprocess.run(
            [str(BIN), "--version"], capture_output=True, text=True, cwd=REPO
        )
        assert proc.returncode == 0, (
            f"--version must exit 0 for fleet probes: rc={proc.returncode} "
            f"stdout={proc.stdout[:200]!r}"
        )
        assert not proc.stdout.lstrip().startswith("{"), (
            "--version must print a plain line, not a JSON refusal envelope"
        )
        assert PACKAGE_VERSION in proc.stdout

    def test_short_flag_v_prints_plain_line_exit_zero(self):
        proc = subprocess.run(
            [str(BIN), "-V"], capture_output=True, text=True, cwd=REPO
        )
        assert proc.returncode == 0
        assert PACKAGE_VERSION in proc.stdout

    def test_unknown_command_still_refuses_with_envelope(self):
        # the probe fix must not change the refusal contract for unknown
        # commands: JSON envelope on stdout, exit 2
        proc = subprocess.run(
            [str(BIN), "nonsense"], capture_output=True, text=True, cwd=REPO
        )
        assert proc.returncode == 2
        envelope = json.loads(proc.stdout)
        assert envelope["decision"] == "refuse"
