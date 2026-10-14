"""Smoke tests for the wild prototype simulations.

The prototypes are the only executable artifact of the wild design (there is
no `wild` command yet), so the gate exercises them as-is: run the script,
require exit 0, and require parseable JSON output.
"""

import importlib.util
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


def load_wild_cd_sim():
    """Import prototype/wild_cd_sim.py by explicit path (no sys.path pollution)."""
    spec = importlib.util.spec_from_file_location(
        "wild_cd_sim_under_test", REPO / "prototype" / "wild_cd_sim.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wild_cd_sim_unikernel_scenarios_deterministic():
    """wild-5gb: unikernel scenario arms (E-H) are seeded-deterministic — two
    calls, identical dict output — and the parameterization is in place."""
    sim = load_wild_cd_sim()
    assert sim.PARAMS["boot_min"] == 0.2, "ASSUMED Firecracker-class boot missing"
    assert sim.PARAMS["farm_slots"] == 4, "ASSUMED build-farm slots missing"
    for fn in (sim.overlap_unikernel, sim.order_unikernel,
               sim.pipeline_unikernel, sim.sensitivity_unikernel):
        first, second = fn(), fn()
        assert first == second, f"{fn.__name__} is not deterministic"


def test_wild_cat_sim_runs_clean():
    """Category laws, substitution, resolution, certificates (slow)."""
    proc = run_prototype("wild_cat_sim.py")
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip(), "category simulation produced no output"


def load_wild_compose():
    """Import prototype/wild_compose.py by explicit path (no sys.path pollution)."""
    spec = importlib.util.spec_from_file_location(
        "wild_compose_under_test", REPO / "prototype" / "wild_compose.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_wild_compose_certificate_deterministic_and_verified():
    """wild-m8c: whole-graph composition certificate. The synthetic fleet DAG
    is seeded-deterministic (build+certify twice, identical dicts), the clean
    certificate verifies, and both tamper mutations are refused with the
    distinct labeled refusals required by ruling D5."""
    compose = load_wild_compose()
    assert compose.PARAMS["layers"] == 4, "ASSUMED fleet depth missing"
    assert compose.PARAMS["services_per_layer"] == [6, 12, 18, 24], \
        "ASSUMED fleet shape (60 services) missing"
    assert compose.PARAMS["fan_out"] == 3, "ASSUMED fan-out missing"

    fleet1 = compose.build_fleet()
    cert1, contracts1 = compose.certify(fleet1)
    fleet2 = compose.build_fleet()
    cert2, contracts2 = compose.certify(fleet2)
    assert cert1 == cert2, "certify is not deterministic"
    assert contracts1 == contracts2, "fleet build is not deterministic"
    assert cert1["kind"] == "composition" and cert1["version"] == 1
    assert cert1["verdict"] == "accept", cert1["verdict"]
    assert cert1["merkle_root"], "missing merkle root"

    assert compose.verify(cert1, contracts1) == "ok", "clean cert refused"

    # D5: two distinct tamper labels, verifier must not trust cert verdicts.
    tampered_digest = compose.tamper_component_digest(cert1)
    tampered_verdict = compose.tamper_edge_verdict(cert1)
    labels = {
        compose.verify(tampered_digest, contracts1),
        compose.verify(tampered_verdict, contracts1),
    }
    assert "tampered:components" in labels, labels
    assert "tampered:edges" in labels, labels