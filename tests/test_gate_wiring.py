"""Gating tests for the gates-wired-and-standard-true hardcoded gate.

The wiring gate: the repo's hard gates (ah + pretender + testaruda +
specodelic) are wired — tool configs exist on disk, parse clean, carry the
standard sections, follow the hardcoded-gate pattern, the openspec spec
corpus is lint-clean and reference-closed, and the gated tests run clean.
"""

import json
import pathlib
import shutil
import subprocess

import tomllib

import pytest

REPO = pathlib.Path(__file__).parent.parent
GATES = REPO / ".espectacular"
LEFTHOOK = REPO / "lefthook.yml"


def run(cmd: list[str]) -> dict:
    return subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)


# ---- tool availability: the wired gates must be callable ----

@pytest.mark.parametrize("tool", ["ah", "pretender", "testaruda", "spk", "just", "lefthook"])
def test_tools_available(tool: str) -> None:
    assert shutil.which(tool), f"wired gate tool '{tool}' not on PATH"


# ---- config validity: wired gate configs exist and parse clean ----

@pytest.mark.parametrize("config", ["testaruda.toml", "pretender.toml"])
def test_configs_parse_clean(config: str) -> None:
    path = REPO / config
    assert path.exists(), f"wired gate config '{config}' missing"
    parsed = tomllib.loads(path.read_text())
    assert parsed, f"{config} is not a parseable TOML config"
    # testaruda.toml additionally validates via its own doctor.
    if config == "testaruda.toml":
        r = run(["testaruda", "doctor"])
        assert r.returncode == 0, f"testaruda doctor red: {r.stderr}"


# ---- standard sections: wired gate configs carry the standard blocks ----

def test_configs_standard_sections() -> None:
    testaruda = tomllib.loads((REPO / "testaruda.toml").read_text())
    pretender = tomllib.loads((REPO / "pretender.toml").read_text())
    # testaruda standard shape: adapters + discover (match the suite defaults).
    assert "adapters" in testaruda, "testaruda.toml missing [adapters] section"
    assert "discover" in testaruda, "testaruda.toml missing [discover] section"
    # pretender gate-mode standard shape: mode gate + [thresholds].
    assert pretender["pretender"]["mode"] == "gate", "pretender.toml not in gate mode"
    assert "thresholds" in pretender, "pretender.toml missing [thresholds] section"


# ---- gate recipe: justfile ci entry point + lefthook managed blocks ----

def test_justfile_gate_recipe() -> None:
    justfile = (REPO / "justfile").read_text()
    # exactly one ci entry point running all four gates
    assert "ci:" in justfile, "justfile missing ci entry point"
    for gate in ("ah-gate", "pretender-gate", "spec-lint", "testaruda-gate"):
        assert gate in justfile, f"justfile ci missing gate '{gate}'"
    r = run(["just", "--list"])
    assert r.returncode == 0, f"justfile parses via just --list, got: {r.stderr}"
    # lefthook.yml is the pre-push/pre-commit hard-gate hook config.
    assert LEFTHOOK.exists(), "lefthook.yml missing"
    hooks = LEFTHOOK.read_text()
    for block in ("ah:managed:start", "SPK:START", "PRETENDER:START", "testaruda-config"):
        assert block in hooks, f"lefthook.yml missing managed block '{block}'"


# ---- gate pattern: wired gates follow the validated hardcoded-gate shape ----

def test_gate_pattern() -> None:
    gate_files = sorted(GATES.glob("*/*.toml"))
    gate_files = [p for p in gate_files if p.name != "config.toml"]
    assert len(gate_files) >= 1, "no hardcoded gates beyond config.toml"
    for gate in gate_files:
        d = tomllib.loads(gate.read_text())
        for field in ("id", "description", "archetype", "status", "authored_with"):
            assert field in d, f"{gate.name} missing '{field}'"
        assert d["archetype"] in ("PF", "SA", "RE"), f"{gate.name} bad archetype"
        assert d["status"] == "active", f"{gate.name} not active"
        assert "tests" in d, f"{gate.name} missing [tests]"
        tests = d["tests"].get("pytest") or []
        assert tests, f"{gate.name} [tests.pytest] empty"
        for t in tests:
            assert "tests/test_" in t.get("flags", ""), (
                f"{gate.name} [tests.pytest] entry does not point at tests/"
            )


# ---- openspec: spec corpus is present, lint-clean, and reference-closed ----

def test_openspec_corpus() -> None:
    corpus = REPO / "openspec" / "specs"
    assert corpus.exists(), "openspec spec corpus missing"
    specs = sorted(corpus.rglob("spec.md"))
    assert len(specs) == 9, f"expected 9 openspec specs, found {len(specs)}"
    r = run(["spk", "lint", "openspec/specs"])
    assert r.returncode == 0, f"spk lint failed: {r.stderr}"
    d = run(["spk", "graph", "openspec/specs"])
    assert d.returncode == 0, f"spk graph failed: {d.stderr}"
    payload = json.loads(d.stdout)
    data = payload.get("data", payload)
    assert not data.get("dangling"), (
        f"openspec spec graph has dangling refs: {data['dangling'][:5]}"
    )
