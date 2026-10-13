#!/usr/bin/env python3
# Purpose: Held-out checker adapter — the Wild checker itself (real binary).
# Responsibilities: For one case id, materialize base and candidate consumer
#   workspaces through real Cargo against the frozen registry, vendor the
#   provider source into a rust-cargo-local-1 extraction bundle, run real
#   `wild extract` + scoped `wild check`, and map the envelope to a verdict.
# Rationale: "Wild as an additional check" arm of the wild-1xk comparison.
#   The verdict comes from the real extractor binary over real source bytes
#   at both versions — never from a canned response. Workspace assembly
#   mirrors the committed replay machinery's local-registry discipline
#   (index + flat .crate mirror merged temp-scope; committed artifacts stay
#   untouched). One disclosed adapter transformation, applied identically to
#   base and candidate: the rust-cargo-local-1 profile extracts from
#   src/lib.rs, so a consumer shipping only src/main.rs gets its main.rs
#   bytes mirrored into src/lib.rs (same demand surface; no fixture tree is
#   modified).

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PROFILE = "rust-cargo-local-1"
EXTRACTOR_DIGEST = "sha256:" + hashlib.sha256(b"wild-extractor-v0").hexdigest()
TARGET_TRIPLE = "x86_64-unknown-linux-gnu"


def map_envelope(envelope: dict) -> str:
    decision = envelope.get("decision")
    assurance = envelope.get("assurance")
    if decision == "accept":
        return "accept"
    if decision == "refuse" and assurance == "Reject":
        return "reject"
    if decision == "refuse" and assurance == "Unknown":
        return "unknown"
    return "error"


def _envelope_note(envelope: dict) -> str:
    """Carry the envelope's own story into the comparison record: the first
    diagnostic code for refusals, coverage numbers for accepts."""
    diagnostics = envelope.get("diagnostics") or []
    codes = [d.get("code", "") for d in diagnostics if d.get("code")]
    if codes:
        return "envelope: " + ",".join(codes[:4])
    coverage = envelope.get("coverage") or {}
    numerator, denominator = coverage.get("numerator"), coverage.get("denominator")
    if numerator is not None and denominator is not None:
        return f"envelope: coverage {numerator}/{denominator}"
    return ""


def _emit(verdict: str, note: str = "") -> None:
    payload = {"verdict": verdict}
    if note:
        payload["note"] = note
    print(json.dumps(payload))


def _files_digests(bundle: Path) -> dict[str, str]:
    return {
        str(path.relative_to(bundle)): "sha256:" + hashlib.sha256(
            path.read_bytes()).hexdigest()
        for path in sorted(bundle.rglob("*")) if path.is_file()
    }


def _lock_dept_version(workspace: Path) -> str | None:
    data = tomllib.loads((workspace / "Cargo.lock").read_text(encoding="utf-8"))
    for package in data.get("package", []):
        if package.get("name") == "dept":
            return package["version"]
    return None


def _pin_dept(manifest: Path, target: str) -> None:
    text = manifest.read_text(encoding="utf-8")
    new = re.sub(r'(dept\s*=\s*)"[^"]*"',
                 lambda m: f'{m.group(1)}"={target}"', text)
    manifest.write_text(new, encoding="utf-8")


def _cargo_home(tmp: Path) -> Path:
    home = tmp / "cargo-home"
    home.mkdir(exist_ok=True)
    return home


def _cargo(cmd: list[str], cwd: Path, home: Path,
           timeout: float = 120) -> subprocess.CompletedProcess:
    """Mirror the committed replay machinery: inherit the host environment,
    override only CARGO_HOME (no user registry interference)."""
    env = dict(os.environ)
    env["CARGO_HOME"] = str(home)
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True,
                          text=True, timeout=timeout)


def _cargo_home(tmp: Path) -> Path:
    home = tmp / "cargo-home"
    home.mkdir(exist_ok=True)
    return home


def _assemble_local_registry(fixtures: Path, tmp: Path) -> Path:
    """Merge the committed index + flat .crate mirror into one local-registry
    directory (Cargo needs both in one dir); temp-scope only."""
    local_reg = tmp / "local-registry"
    shutil.copytree(fixtures / "registry" / "index", local_reg / "index")
    shutil.copy2(fixtures / "registry" / "index" / "config.json",
                 local_reg / "config.json")
    for crate in sorted((fixtures / "consumer-mirror").glob("*.crate")):
        shutil.copy2(crate, local_reg / crate.name)
    return local_reg


def _materialize_workspace(fixtures: Path, local_reg: Path, consumer: Path,
                           version: str, tmp: Path, home: Path,
                           label: str) -> Path:
    """Resolve the consumer tree at an exact dept version through real Cargo.

    The committed base lock intentionally carries a stale checksum (the
    graded baseline-failure discipline), so a base-state workspace is used
    exactly as committed — no cargo update, which would trip checksum
    verification. Only a changed target goes through a real authorized
    resolution (pin + cargo update), matching the replay machinery.
    """
    workspace = tmp / f"{label}-workspace"
    shutil.copytree(consumer, workspace)
    (workspace / ".cargo").mkdir(exist_ok=True)
    (workspace / ".cargo" / "config.toml").write_text(
        '[source.crates-io]\nreplace-with = "wild-lr"\n\n'
        f'[source.wild-lr]\nlocal-registry = "{local_reg}"\n',
        encoding="utf-8")
    current = _lock_dept_version(workspace)
    if current == version:
        return workspace
    _pin_dept(workspace / "Cargo.toml", version)
    update = _cargo(["cargo", "update", "--offline"], workspace, home)
    if update.returncode != 0:
        raise RuntimeError(
            f"cargo update for {version} exited {update.returncode}: "
            f"{update.stderr[-300:]!r}")
    resolved = _lock_dept_version(workspace)
    if resolved != version:
        raise RuntimeError(
            f"lock resolved to {resolved!r}, expected {version!r}")
    return workspace

def _build_bundle(fixtures: Path, workspace: Path, version: str,
                  tmp: Path, label: str, local_reg: Path) -> Path:
    """Vendor the provider source and lay out a rust-cargo-local-1 bundle."""
    crate_path = fixtures / "consumer-mirror" / f"dept-{version}.crate"
    if not crate_path.is_file():
        raise RuntimeError(f"provider crate missing: {crate_path}")
    bundle = tmp / f"{label}-bundle"
    (bundle / "consumer").mkdir(parents=True)
    for item in workspace.iterdir():
        if item.name == ".cargo":
            continue
        shutil.copytree(item, bundle / "consumer" / item.name) \
            if item.is_dir() else shutil.copy2(item, bundle / "consumer" / item.name)
    provider = bundle / "provider"
    provider.mkdir()
    with tarfile.open(crate_path, "r:gz") as tar:
        for member in tar.getmembers():
            if not member.name.startswith(f"dept-{version}/"):
                continue
            rel = member.name[len(f"dept-{version}/"):]
            if not rel or rel.endswith("/"):
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            dest = provider / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(extracted.read())
    if not (provider / "Cargo.toml").is_file() or \
            not (provider / "src").is_dir():
        raise RuntimeError(f"crate {crate_path.name} unpacked no provider source")
    # Disclosed transformation: mirror main.rs into lib.rs so the
    # rust-cargo-local-1 profile can extract the consumer's demand surface.
    consumer_src = bundle / "consumer" / "src"
    if not (consumer_src / "lib.rs").is_file():
        if not (consumer_src / "main.rs").is_file():
            raise RuntimeError("consumer has neither src/lib.rs nor src/main.rs")
        shutil.copy2(consumer_src / "main.rs", consumer_src / "lib.rs")
    _pin_provider_path(bundle / "consumer" / "Cargo.toml")
    (bundle / "Cargo.toml").write_text(
        '[workspace]\nresolver = "2"\nmembers = ["consumer", "provider"]\n',
        encoding="utf-8")
    # The provider's own crates.io dependencies (dept 1.9.0 needs deputil)
    # must resolve offline inside the bundle: mirror the committed
    # local-registry source replacement into the bundle root.
    (bundle / ".cargo").mkdir(exist_ok=True)
    (bundle / ".cargo" / "config.toml").write_text(
        '[source.crates-io]\nreplace-with = "wild-lr"\n\n'
        f'[source.wild-lr]\nlocal-registry = "{local_reg}"\n',
        encoding="utf-8")
    update = _cargo(["cargo", "update", "--offline"],
                    bundle, tmp / "cargo-home")
    if update.returncode != 0:
        raise RuntimeError(
            f"bundle lock regeneration exited {update.returncode}: "
            f"{update.stderr[-300:]!r}")
    return bundle


def _pin_provider_path(manifest: Path) -> None:
    text = manifest.read_text(encoding="utf-8")
    new = re.sub(r'(dept\s*=\s*)"[^"]*"', r'\1{ path = "../provider" }', text)
    manifest.write_text(new, encoding="utf-8")


def _run_wild(bin: Path, args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([str(bin), *args], cwd=REPO,
                          capture_output=True, text=True, timeout=120)


def _check(bin: Path, base: dict, candidate: dict, tmp: Path) -> dict:
    request = {
        "version": "local-1",
        "kind": "check-request",
        "profile": PROFILE,
        "consumer": "consumer",
        "base": base,
        "candidate": candidate,
        "target": TARGET_TRIPLE,
        "toolchain": "stable",
        "features": [],
        "policy": {"structural": "accretion"},
        "obligations": None,
        "checker": {"name": "wild", "digest": EXTRACTOR_DIGEST},
    }
    request_path = tmp / "check.json"
    report_path = tmp / "report.json"
    request_path.write_text(json.dumps(request))
    proc = _run_wild(bin, ["check", "--request", str(request_path),
                           "--format", "json", "--report", str(report_path)])
    if proc.returncode not in (0, 1):
        raise RuntimeError(
            f"wild check exited {proc.returncode}: {proc.stdout[-300:]!r}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"unparseable wild check envelope: {exc}") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="real Wild checker for one held-out case")
    parser.add_argument("case_id")
    parser.add_argument("--context", default="experiments/heldout/case_context.json")
    parser.add_argument("--fixtures", default="experiments/update_fixtures/e5")
    parser.add_argument("--bin", default="target/debug/wild")
    args = parser.parse_args()

    bin_path = REPO / args.bin
    if not bin_path.exists():
        build = subprocess.run(["cargo", "build", "-q"], cwd=REPO,
                               capture_output=True, text=True, timeout=600)
        if build.returncode != 0 or not bin_path.exists():
            _emit("error", f"wild binary missing and build failed: "
                           f"{build.stderr[-200:]!r}")
            return 0

    context = json.loads(Path(args.context).read_text(encoding="utf-8"))
    entry = next((c for c in context["cases"] if c["id"] == args.case_id), None)
    if entry is None:
        _emit("error", f"case {args.case_id!r} not in context")
        return 0
    fixtures = REPO / args.fixtures
    consumer = REPO / entry["consumer"]

    try:
        with tempfile.TemporaryDirectory(prefix="wild-heldout-") as raw:
            tmp = Path(raw)
            home = _cargo_home(tmp)
            local_reg = _assemble_local_registry(fixtures, tmp)
            base_ws = _materialize_workspace(
                fixtures, local_reg, consumer, entry["base"], tmp, home, "base")
            cand_ws = _materialize_workspace(
                fixtures, local_reg, consumer, entry["target"], tmp, home,
                "candidate")
            base_bundle = _build_bundle(
                fixtures, base_ws, entry["base"], tmp, "base", local_reg)
            cand_bundle = _build_bundle(
                fixtures, cand_ws, entry["target"], tmp, "candidate", local_reg)
            base_files = _files_digests(base_bundle)
            cand_files = _files_digests(cand_bundle)
            envelope = _check(bin_path,
                              {"bundle_root": str(base_bundle),
                               "files": base_files},
                              {"bundle_root": str(cand_bundle),
                               "files": cand_files},
                              tmp)
            verdict = map_envelope(envelope)
            note = _envelope_note(envelope)
            _emit(verdict, note)
            return 0
    except (RuntimeError, OSError, subprocess.TimeoutExpired, ValueError,
            tomllib.TOMLDecodeError, json.JSONDecodeError) as exc:
        _emit("error", str(exc))
        return 0


if __name__ == "__main__":
    sys.exit(main())