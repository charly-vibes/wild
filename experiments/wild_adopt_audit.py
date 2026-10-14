#!/usr/bin/env python3
# Purpose: Consecutive-release verdict audit driver (beads wild-cdp.2, rung 1
#   of the wild.adopt ladder — observe). Replays one crates.io crate's real
#   release history through the `wild` binary: for every consecutive release
#   pair, extract the previous tree, generate a consumer caller that demands
#   every supported public fn, run `wild check` (base = prev bundle,
#   candidate = next bundle), and audit the computed verdict against the
#   declared semver bump. Disagreements (semver claimed compatible, wild
#   computed a break) and abstentions (unknown verdicts with named gap
#   reasons) are disclosed, never smoothed over.
# Responsibilities: Fetch the version list and per-version sources from
#   crates.io (or consume a local --sources override so tests stay offline);
#   build base/candidate bundles; invoke the real `wild` binary for every
#   verdict (no fabricated rows, no retry-into-a-different-verdict); verify
#   extraction determinism per version; render a human audit table + summary
#   into the results file and emit the JSON audit rows on stdout separately.
# Rationale: `wild adopt` is spec'd but intentionally unimplemented — the
#   honest first measurement is this replay script. Version strings are
#   metadata for comparison only; every verdict line corresponds to a real
#   subprocess echoed with its command line and exit code.

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

CRATES_API = "https://crates.io/api/v1/crates/{crate}"
CRATES_DOWNLOAD = "https://crates.io/api/v1/crates/{crate}/{version}/download"
USER_AGENT = "wild-adopt-audit-research (charly-vibes)"

PROFILE = "rust-cargo-local-1"
CONSUMER = "consumer"
TARGET = "x86_64-unknown-linux-gnu"
TOOLCHAIN = "stable"
POLICY = {"structural": "accretion"}


def sha_bytes(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def sha_text(text: str) -> str:
    return sha_bytes(text.encode())


def die(message: str, code: int = 3) -> "NoReturn":  # type: ignore[name-defined]
    print(f"wild-adopt-audit: {message}", file=sys.stderr)
    sys.exit(code)


def run_wild(bin_path: Path, args: list[str], cwd: Path | None = None):
    cmd = [str(bin_path), *args]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    except FileNotFoundError:
        die(f"wild binary not found at {bin_path}; build it or pass --bin")
    echo = " ".join(cmd)
    return proc, echo


def fetch_json(url: str):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode())
    except OSError as exc:
        die(
            "network-unavailable: crates.io fetch failed and no --sources tree "
            f"was provided; refusing to synthesize release history ({exc})"
        )


def fetch_versions(crate: str) -> list[str]:
    doc = fetch_json(CRATES_API.format(crate=crate))
    versions = sorted(
        (v["num"] for v in doc.get("versions", [])), key=semver_key
    )
    if not versions:
        die(f"crates.io lists no versions for crate `{crate}`")
    return versions


def semver_key(version: str):
    try:
        core = version.split("-", 1)[0]
        return tuple(int(p) for p in core.split("."))
    except ValueError:
        return (0, 0, 0, version)


def bump_kind(prev: str, nxt: str) -> str:
    p, n = semver_key(prev)[:3], semver_key(nxt)[:3]
    if p[0] != n[0]:
        return "major"
    if p[1] != n[1]:
        return "minor"
    return "patch"


def unpack_crate_archive(crate: str, version: str, dest: Path) -> Path:
    """Download the .crate tarball and unpack it; return the tree root."""
    dest.mkdir(parents=True, exist_ok=True)
    url = CRATES_DOWNLOAD.format(crate=crate, version=version)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = resp.read()
    except OSError:
        return Path()  # caller records source-unavailable
    archive = dest / f"{crate}-{version}.tar.gz"
    archive.write_bytes(data)
    # `filter="data"` rejects absolute paths, traversal escapes, and devices
    with tarfile.open(archive, "r:gz") as tar:
        tar.extractall(dest, filter="data")
    return dest / f"{crate}-{version}"


def load_version_tree(crate: str, version: str, sources: Path | None, work: Path):
    """Return the crate tree root for one version, or None if unavailable."""
    if sources is not None:
        base = sources / version
        if not base.is_dir():
            return None
        candidates = [
            base,
            base / f"{crate}-{version}",
            base / crate,
        ]
        for cand in candidates:
            if (cand / "Cargo.toml").is_file():
                return cand
        return None
    return unpack_crate_archive(crate, version, work / "trees" / version)


def tree_files(tree: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for path in sorted(tree.rglob("*")):
        if path.is_file() and not path.is_symlink():
            files[path.relative_to(tree).as_posix()] = path.read_bytes()
    return files


def write_bundle(
    root: Path,
    crate: str,
    tree: Path,
    caller_lib: str,
    version_label: str,
) -> dict[str, bytes]:
    """Materialize a workspace bundle: workspace root + generated consumer +
    the provider tree verbatim. Returns rel-path -> raw bytes for digests."""
    root.mkdir(parents=True, exist_ok=True)
    workspace_toml = (
        "[workspace]\n"
        f'members = ["{CONSUMER}", "{crate}"]\n'
        'resolver = "2"\n'
    )
    consumer_toml = (
        "[package]\n"
        f'name = "{CONSUMER}"\n'
        'version = "0.0.0"\n'
        'edition = "2021"\n\n'
        "[dependencies]\n"
        f"{crate} = {{ path = \"../{crate}\" }}\n"
    )
    (root / "Cargo.toml").write_text(workspace_toml)
    (root / CONSUMER / "src").mkdir(parents=True, exist_ok=True)
    (root / CONSUMER / "Cargo.toml").write_text(consumer_toml)
    (root / CONSUMER / "src" / "lib.rs").write_text(caller_lib)
    crate_dir = root / crate
    if crate_dir.exists():
        shutil.rmtree(crate_dir)
    shutil.copytree(tree, crate_dir)

    # digests are computed over raw bytes so non-UTF-8 tree files (licenses,
    # images) never fork the committed digest from the file on disk
    files: dict[str, bytes] = {}
    files["Cargo.toml"] = workspace_toml.encode()
    files[f"{CONSUMER}/Cargo.toml"] = consumer_toml.encode()
    files[f"{CONSUMER}/src/lib.rs"] = caller_lib.encode()
    for rel, data in tree_files(crate_dir).items():
        files[f"{crate}/{rel}"] = data
    return files


def request_files(files: dict[str, bytes]) -> dict[str, str]:
    return {rel: sha_bytes(data) for rel, data in sorted(files.items())}


NOOP_CALLER = "// audit driver: inventory pass, no demand yet\npub fn audit_inventory() {}\n"


def literals_for(arg: dict) -> str:
    name = arg.get("name")
    if name == "integer":
        return "0"  # every supported integer interval contains 0
    if name == "boolean":
        return "true"
    if name == "text-borrowed":
        return '"w"'
    if name == "text-owned":
        return 'String::from("w")'
    if name == "unit":
        return "()"
    return "()"


def supported_slots(contract: dict, crate: str) -> list[dict]:
    slots = []
    for slot in contract.get("slots", []):
        name = slot.get("name", "")
        if not name.startswith(crate + "::"):
            continue
        if slot.get("type", {}).get("shape") == "function":
            slots.append(slot)
    return slots


def generated_caller(crate: str, slots: list[dict]) -> str:
    lines = ["// generated caller: one demand per inventoried supported fn"]
    for slot in slots:
        fn = slot["name"].split("::", 1)[1]
        args = slot.get("type", {}).get("arguments", [])
        literals = ", ".join(literals_for(a) for a in args)
        wrapper = "call_" + "".join(c if c.isalnum() else "_" for c in fn)
        lines.append(f"pub fn {wrapper}() {{ {crate}::{fn}({literals}); }}")
    return "\n".join(lines) + "\n"


def extract_request(bundle_root: Path, files: dict[str, str]) -> dict:
    return {
        "version": "local-1",
        "kind": "extraction-request",
        "profile": PROFILE,
        "bundle_root": str(bundle_root),
        "files": request_files(files),
        "target": TARGET,
        "toolchain": TOOLCHAIN,
        "features": [],
        "extractor": {"name": "wild", "digest": sha_text("wild-extractor-v0")},
    }


def check_request(
    base_root: Path, base_files: dict[str, str],
    cand_root: Path, cand_files: dict[str, str],
) -> dict:
    return {
        "version": "local-1",
        "kind": "check-request",
        "profile": PROFILE,
        "consumer": CONSUMER,
        "base": {"bundle_root": str(base_root), "files": request_files(base_files)},
        "candidate": {
            "bundle_root": str(cand_root),
            "files": request_files(cand_files),
        },
        "target": TARGET,
        "toolchain": TOOLCHAIN,
        "features": [],
        "policy": POLICY,
        "obligations": None,
        "checker": {"name": "wild", "digest": sha_text("wild-extractor-v0")},
    }


def run_extract(bin_path, request: dict, out_dir: Path, echoes: list[str]):
    out_dir.mkdir(parents=True, exist_ok=True)
    request_path = out_dir / "extraction.json"
    request_path.write_text(json.dumps(request, indent=1))
    proc, echo = run_wild(
        bin_path,
        ["extract", "--request", str(request_path), "--output", str(out_dir)],
    )
    echoes.append(f"$ {echo} -> exit {proc.returncode}")
    try:
        envelope = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        envelope = {}
    return proc, envelope


def run_check(bin_path, request: dict, out_dir: Path, echoes: list[str]):
    out_dir.mkdir(parents=True, exist_ok=True)
    request_path = out_dir / "check.json"
    request_path.write_text(json.dumps(request, indent=1))
    proc, echo = run_wild(
        bin_path,
        [
            "check", "--request", str(request_path), "--format", "json",
            "--report", str(out_dir / "report.json"),
        ],
    )
    echoes.append(f"$ {echo} -> exit {proc.returncode}")
    try:
        envelope = json.loads(proc.stdout) if proc.stdout.strip() else {}
    except json.JSONDecodeError:
        envelope = {}
    return proc, envelope


def diagnostic_codes(report: dict) -> list[str]:
    return sorted({d.get("code", "?") for d in report.get("diagnostics", [])})


def _read_report(out_dir: Path) -> dict:
    report_path = out_dir / "report.json"
    if not report_path.is_file():
        return {}
    try:
        return json.loads(report_path.read_text())
    except json.JSONDecodeError:
        return {}


def audit_pair(
    verdict: str,
    bump: str,
) -> str:
    if verdict == "error":
        return "errored"
    if verdict == "unknown":
        return "abstained"
    if bump in ("minor", "patch"):
        return "consistent" if verdict == "accept" else "disagreement"
    # major bump: semver over-claimed a break if accepted — noted, not a lie
    return "consistent"


def resolve_bin(args) -> Path:
    if args.bin:
        bin_path = Path(args.bin)
        if not bin_path.exists():
            die(f"--bin {args.bin} does not exist")
        return bin_path
    repo = Path(__file__).resolve().parent.parent
    bin_path = repo / "target" / "debug" / "wild"
    if not bin_path.exists():
        proc = subprocess.run(["cargo", "build", "-q"], cwd=repo)
        if proc.returncode != 0 or not bin_path.exists():
            die(f"wild binary missing at {bin_path} and cargo build failed")
    return bin_path


def inventory_versions(
    args, sources: Path | None, work: Path, bin_path: Path, echoes: list[str]
) -> tuple[dict[str, dict], list[str], list[str]]:
    """Phase 1: inventory every version tree, twice, to pin determinism."""
    inventories: dict[str, dict] = {}
    unavailable: list[str] = []
    determinism_failures: list[str] = []
    versions = (
        sorted(
            (d.name for d in sources.iterdir() if d.is_dir()), key=semver_key
        )
        if sources is not None
        else fetch_versions(args.crate)
    )
    if args.limit_pairs is not None:
        versions = versions[: args.limit_pairs + 1]
    for version in versions:
        tree = load_version_tree(args.crate, version, sources, work)
        if tree is None or not (tree / "Cargo.toml").is_file():
            unavailable.append(version)
            continue
        bundle = work / "inventory" / version
        files = write_bundle(bundle, args.crate, tree, NOOP_CALLER, version)
        first, _ = run_extract(
            bin_path, extract_request(bundle, files), work / "inv1" / version, echoes
        )
        run_extract(
            bin_path, extract_request(bundle, files), work / "inv2" / version, echoes
        )
        contract1 = (work / "inv1" / version / "contract.json").read_bytes()
        contract2 = (work / "inv2" / version / "contract.json").read_bytes()
        if first.returncode not in (0, 1):
            unavailable.append(version)
            echoes.append(f"  version {version}: extraction errored (exit 2 class)")
            continue
        if contract1 != contract2:
            determinism_failures.append(version)
        contract = json.loads(contract1)
        inventories[version] = {
            "tree": tree,
            "contract": contract,
            "slots": supported_slots(contract, args.crate),
            "complete": first.returncode == 0,
            "codes": diagnostic_codes(
                json.loads((work / "inv1" / version / "report.json").read_text())
            ),
        }
    return inventories, unavailable, determinism_failures


def check_pairs(
    args, inventories: dict[str, dict], work: Path, bin_path: Path,
    echoes: list[str],
) -> list[dict]:
    """Phase 2: consecutive pairs, base = prev bundle, candidate = next
    bundle, both carrying the same generated caller (demand from prev's
    surface)."""
    rows: list[dict] = []
    pairs = list(zip(list(inventories), list(inventories)[1:]))
    if args.limit_pairs is not None:
        pairs = pairs[: args.limit_pairs]
    for prev, nxt in pairs:
        prev_inv, nxt_inv = inventories[prev], inventories[nxt]
        bump = bump_kind(prev, nxt)
        base = work / "bundles" / f"{prev}-base"
        cand = work / "bundles" / f"{prev}-to-{nxt}"
        caller = generated_caller(args.crate, prev_inv["slots"])
        base_files = write_bundle(base, args.crate, prev_inv["tree"], caller, prev)
        cand_files = write_bundle(cand, args.crate, nxt_inv["tree"], caller, nxt)
        out_dir = work / "checks" / f"{prev}-to-{nxt}"
        proc, envelope = run_check(
            bin_path,
            check_request(base, base_files, cand, cand_files),
            out_dir,
            echoes,
        )
        if proc.returncode == 0:
            verdict = "accept"
        elif proc.returncode == 1:
            verdict = "reject" if envelope.get("assurance") == "Reject" else "unknown"
        else:
            verdict = "error"
        report = _read_report(out_dir)
        gaps = sorted(
            slot["name"]
            for slot in prev_inv["contract"].get("slots", [])
            if slot["name"].startswith(args.crate + "::")
            and slot.get("type", {}).get("shape") != "function"
        )
        reasons = diagnostic_codes(report)
        if not reasons and verdict == "error":
            reasons = [f"exit-{proc.returncode}"]
        detail = [
            f"{d.get('code')}: {d.get('reason')}"
            for d in report.get("diagnostics", [])[:3]
        ]
        rows.append(
            {
                "prev": prev,
                "next": nxt,
                "bump_kind": bump,
                "computed_verdict": verdict,
                "audit_row": audit_pair(verdict, bump),
                "decision": envelope.get("decision"),
                "assurance": envelope.get("assurance"),
                "exit_code": proc.returncode,
                "diagnostics": reasons,
                "diagnostic_detail": detail,
                "coverage_gaps": gaps,
                "prev_inventory_complete": prev_inv["complete"],
                "next_inventory_complete": nxt_inv["complete"],
            }
        )
    return rows


def render_results(
    args, rows: list[dict], inventories: dict[str, dict], unavailable: list[str],
    determinism_failures: list[str], echoes: list[str], out_path: Path,
) -> None:
    """Phase 3: render the human results file; JSON rows go to stdout only."""
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["audit_row"]] = counts.get(row["audit_row"], 0) + 1
    lines: list[str] = []
    lines.append("wild adopt audit — consecutive-release verdict replay")
    lines.append(f"crate: {args.crate}")
    lines.append(f"wild binary: {resolve_bin(args)}")
    lines.append(f"versions inventoried: {', '.join(inventories)}")
    if unavailable:
        lines.append(f"source-unavailable versions: {', '.join(unavailable)}")
    if determinism_failures:
        lines.append(
            "DETERMINISM LOSS: repeated extraction not byte-identical for: "
            + ", ".join(determinism_failures)
        )
    lines.append("")
    lines.append("## Coverage gaps (demand cannot see these)")
    for version, inv in inventories.items():
        opaque = [
            slot["name"]
            for slot in inv["contract"].get("slots", [])
            if slot["name"].startswith(args.crate + "::")
            and slot.get("type", {}).get("shape") != "function"
        ]
        lines.append(
            f"- {version}: complete_inventory={inv['complete']} "
            f"diagnostics={inv['codes']} "
            f"unsupported-signature slots (not called): {opaque or 'none'}"
        )
    lines.append("")
    lines.append("## Audit table")
    lines.append(
        "prev -> next | bump | verdict | decision/assurance | exit | audit_row | reasons"
    )
    for row in rows:
        label = row["audit_row"].upper() if row["audit_row"] == "disagreement" else row["audit_row"]
        lines.append(
            f"{row['prev']} -> {row['next']} | {row['bump_kind']} | "
            f"{row['computed_verdict']} | {row['decision']}/{row['assurance']} | "
            f"{row['exit_code']} | {label} | {row['diagnostics'] or '-'}"
        )
    lines.append("")
    lines.append("## Subprocess echo")
    lines.extend(echoes)
    lines.append("")
    lines.append("## Summary")
    audited = len(rows)
    abstained = counts.get("abstained", 0)
    lines.append(f"pairs audited: {audited}")
    for key in ("consistent", "disagreement", "abstained", "errored"):
        lines.append(f"{key}: {counts.get(key, 0)}")
    if unavailable:
        lines.append(f"source-unavailable: {len(unavailable)}")
    if audited:
        rate = round(100.0 * abstained / audited, 1)
        lines.append(f"unknown (abstention) rate: {rate}%")
    lines.append(
        "determinism (repeated extraction byte identity): "
        + ("FAIL: " + ", ".join(determinism_failures) if determinism_failures else "pass")
    )
    if audited and abstained > audited / 2:
        lines.append(
            "NOTE: >50% of pairs abstained — per the ticket's follow-up "
            "threshold, gap-rate measurement is the deliverable, not a failure"
        )
    out_path.write_text("\n".join(lines) + "\n")


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(
        description="Consecutive-release verdict audit via the real wild binary"
    )
    parser.add_argument("--crate", required=True)
    parser.add_argument("--out", required=True, help="results file to write")
    parser.add_argument("--limit-pairs", type=int, default=None)
    parser.add_argument(
        "--offline", action="store_true",
        help="refuse crates.io network access (use with --sources)",
    )
    parser.add_argument(
        "--sources", default=None,
        help="local dir mapping version -> unpacked crate tree (overrides fetch)",
    )
    parser.add_argument("--bin", default=None, help="path to the wild binary")
    args = parser.parse_args(argv)

    sources = Path(args.sources).resolve() if args.sources else None
    if args.offline and sources is None:
        die(
            "offline: --offline set and no --sources tree provided; refusing to "
            "synthesize release history — supply --sources or allow network"
        )
    if sources is not None and not any(
        p.is_dir() for p in sources.iterdir()
    ):
        die(f"offline: --sources dir {sources} has no version subdirectories")

    bin_path = resolve_bin(args)
    out_path = Path(args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    work = Path(tempfile.mkdtemp(prefix="wild-adopt-audit-"))
    echoes: list[str] = []

    inventories, unavailable, determinism_failures = inventory_versions(
        args, sources, work, bin_path, echoes
    )
    rows = check_pairs(args, inventories, work, bin_path, echoes)
    render_results(
        args, rows, inventories, unavailable, determinism_failures, echoes, out_path
    )
    print(json.dumps(rows, indent=1))


if __name__ == "__main__":
    main()
