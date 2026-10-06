"""Smoke tests for the wild prototype simulations.

The prototypes are the only executable artifact of the wild design (there is
no `wild` command yet), so the gate exercises them as-is: run the script,
require exit 0, and require parseable JSON output.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

SLOW = {"wild_cat_sim.py"}  # minutes-long; excluded from the default gate


def run_prototype(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO / "prototype" / script)],
        capture_output=True,
        text=True,
        timeout=300,
        cwd=REPO,
    )


def test_wild_sim_round1_runs_clean():
    """Round-1 scenarios: tier pipeline, accretion relation, tombstones."""
    proc = run_prototype("wild_sim.py")
    assert proc.returncode == 0, proc.stderr[-2000:]
    # Output must parse as JSON and carry per-scenario verdicts.
    verdicts = json.loads(proc.stdout)
    assert isinstance(verdicts, list) and len(verdicts) > 0
    expected = {
        "1": "rejected@shape", "3a": "rejected@shape", "3b": "rejected@laws",
        "3c": "published", "3d": "repair_draft", "4a": "rejected@shape",
        "4b": "rejected@laws", "4c": "published", "5a": "rejected@shape",
        "5b": "published", "5c": "rejected@shape", "5d": "rejected@shape",
    }
    by_id = {scenario["id"]: scenario for scenario in verdicts}
    assert len(by_id) == len(verdicts) and set(by_id) == set(expected)
    for scenario_id, terminal in expected.items():
        assert by_id[scenario_id]["trace"].split(" > ")[-1] == terminal
    # Preserve the declared residual: no law/evidence means undeclared breaks can escape.
    assert by_id["3c"]["consumers"]["C"]["tool"] == "BROKEN"
    assert by_id["4c"]["consumers"]["App"]["tool"] == "BROKEN"
    assert by_id["5b"]["consumers"]["C"]["tool"] == "ok"


def test_wild_cd_sim_runs_clean():
    """Deployment simulations: gates, canaries, floors, rollbacks."""
    proc = run_prototype("wild_cd_sim.py")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip(), "deployment simulation produced no output"


def test_wild_cat_sim_runs_clean():
    """Category laws, substitution, resolution, certificates (slow)."""
    proc = run_prototype("wild_cat_sim.py")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip(), "category simulation produced no output"