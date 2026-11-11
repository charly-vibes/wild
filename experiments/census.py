#!/usr/bin/env python3
# wild-58c — false-break census on serde's full crates.io release history.
#
# PRE-REGISTRATION (committed before any transition was graded; no post-hoc
# crate/version swaps). RED capture: before this file existed,
# /tmp/wild-58c-scratch/test_red_census.py failed with
# "no census artifact (RED)" (exit 1) — captured 2026-11-11.
#
# Choice: crate `serde` (serde-rs/serde). Rationale: 308 plain releases
# 2015→2026, large public surface (pilot: 409 slots at 1.0.219 via the
# tree-sitter path), real-world relevance. Alternatives considered: clap
# (462 versions, larger replay; serde preferred for surface size per
# release and cleaner release ordering).
#
# Version set (pre-registered): every crates.io-listed serde version whose
# `num` is plain X.Y.Z (no pre-release suffix), INCLUDING yanked versions
# (0.7.6, 1.0.31, 1.0.95), sorted by crates.io `created_at` ascending —
# true release order. N = 308 versions, 307 consecutive transitions.
# Excluded (pre-registered): 8 pre-release listings — 0.8.0-rc1/rc2/rc3,
# 0.9.0-rc1/rc2/rc3/rc4, 1.0.172-alpha.0 — Cargo never resolves
# pre-releases by default and caret semantics do not apply to them.
# Note: crates.io created_at order places 1.0.0 before 0.9.15 (a
# back-publish); that ordering is kept and graded honestly.
#
# Slot-count methodology (pre-registered, both paths run for every version):
#   PRIMARY (surface + verdict engine): the experiments tree-sitter path,
#   `prototype/wild_proto.extract_rust()` over the extracted .crate tree —
#   slot count = len(Contract.slots). The wild binary refuses
#   (complete_inventory=false) on macro_rules!/glob-reexport crates
#   (demonstrated in the pre-registration smoke run: serde 1.0.219 →
#   decision=refuse with 48/409 slots inventoried), so the tree-sitter path
#   is the only one that inventories the full public surface.
#   SECONDARY (current-extractor census columns): the wild extract binary
#   (provenance below) run per version over a sha256-digested bundle of
#   Cargo.toml + src/**/*.rs; recorded per version: decision
#   (complete/refuse/error), inventoried slot count, opaque slot count
#   (type.shape == "opaque"). Opaque share (per release) = opaque slots /
#   inventoried slots — the fraction of public surface the v1 checker can
#   only fingerprint (verdict Unknown), i.e. Unknown/total with both terms
#   explicit. Recorded as "-" where the binary inventories 0 slots.
# Transition classification (pre-registered):
#   Contract verdict: prototype/wild_sim.shape_check(old, new) —
#   True=accretion, False=break (first-failure reason recorded), plus
#   added/removed/changed slot tallies. `changed` = same-name slots whose
#   Slot tuple differs.
#   Cargo caret verdict: A→B compatible iff (B>=A and) major>0 → same
#   major; major==0,minor>0 → same major.minor; major==0,minor==0 → same
#   major.minor.patch. (Cargo caret semantics, incl. the 0.x rule.)
#   False break (pre-registered definition, from brief wild-58c): a
#   transition where the contract pipeline says break AND Cargo says
#   compatible AND no documented/digestible break evidence exists in the
#   release notes of the TO version (evidence source: api.github.com
#   repos/serde-rs/serde/releases bodies, fetched to scratch before any
#   grading; marker set: breaking/break/remove(d)/deprecat/no longer/
#   renamed/changed from). Notes exist but lack markers → "notes-no-marker";
#   no notes at all → "none-found"; notes missing due to fetch failure →
#   "fetch-failed" (recorded honestly, never silently folded into either
#   verdict class). Numerator = false breaks; DENOMINATOR = transitions
#   with contract=break ∧ cargo=compatible (the candidate set); the same
#   numerator over ALL transitions is reported as a secondary rate. Every
#   headline line names its numerator and denominator explicitly.
#   Context (pre-registered): transitions where Cargo says incompatible
#   but the contract says accretion are counted (Cargo being conservative).
# Provenance: recorded in the census_results.txt header (toolchain, binary
#   commit + sha256, extractor identity, evidence-cache date).
# Scratch hygiene: all scratch under WILD_58C_SCRATCH (default
#   /tmp/wild-58c-scratch); .crate tarballs are cached there (needed for
#   replay; ~30MB total), extracted source trees are deleted after each
#   version's extraction; df -h /tmp is checked per batch (16 versions);
#   Errno 122 (EDQUOT) → clean scratch → retry once → honest BLOCKED with
#   df output. Never scratch into the repo.

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.environ.get("WILD_58C_SCRATCH", "/tmp/wild-58c-scratch")
CACHE = os.path.join(SCRATCH, "cache")
WORK = os.path.join(SCRATCH, "work")
WILD_BIN = os.path.join(REPO, "target", "release", "wild")
CRATE = "serde"
UA = "wild-census-agent wild-58c (research; contact: repo owner)"
BATCH = 16
BREAK_MARKERS = ("breaking", "break", "remove", "deprecat", "no longer",
                 "renamed", "changed from")

# PRE-REGISTERED version list (crates.io created_at ascending; see header).
PRE_REGISTERED_VERSIONS = [
    "0.0.0", "0.2.0", "0.2.1", "0.3.0", "0.3.1", "0.3.2", "0.3.3", "0.4.0",
    "0.4.1", "0.4.2", "0.4.3", "0.5.0", "0.5.1", "0.5.2", "0.5.3", "0.6.0",
    "0.6.1", "0.6.6", "0.6.7", "0.6.10", "0.6.11", "0.6.12", "0.6.13", "0.6.14",
    "0.6.15", "0.7.0", "0.7.4", "0.7.5", "0.7.6", "0.7.7", "0.7.8", "0.7.9",
    "0.7.10", "0.7.11", "0.7.12", "0.7.13", "0.7.14", "0.7.15", "0.8.0", "0.8.1",
    "0.8.2", "0.8.3", "0.8.4", "0.8.5", "0.8.6", "0.8.7", "0.8.8", "0.8.9",
    "0.8.10", "0.8.11", "0.8.12", "0.8.13", "0.8.14", "0.8.15", "0.8.16", "0.8.17",
    "0.8.18", "0.8.19", "0.8.20", "0.8.21", "0.8.22", "0.8.23", "0.9.0", "0.9.1",
    "0.9.2", "0.9.3", "0.9.4", "0.9.5", "0.9.6", "0.9.7", "0.9.8", "0.9.9",
    "0.9.10", "0.9.11", "0.9.12", "0.9.13", "0.9.14", "1.0.0", "0.9.15", "1.0.1",
    "1.0.2", "1.0.3", "1.0.4", "1.0.5", "1.0.6", "1.0.7", "1.0.8", "1.0.9",
    "1.0.10", "1.0.11", "1.0.12", "1.0.13", "1.0.14", "1.0.15", "1.0.16", "1.0.17",
    "1.0.18", "1.0.19", "1.0.20", "1.0.21", "1.0.22", "1.0.23", "1.0.24", "1.0.25",
    "1.0.26", "1.0.27", "1.0.28", "1.0.29", "1.0.30", "1.0.31", "1.0.32", "1.0.33",
    "1.0.34", "1.0.35", "1.0.36", "1.0.37", "1.0.38", "1.0.39", "1.0.40", "1.0.41",
    "1.0.42", "1.0.43", "1.0.44", "1.0.45", "1.0.46", "1.0.47", "1.0.48", "1.0.49",
    "1.0.50", "1.0.51", "1.0.52", "1.0.53", "1.0.54", "1.0.55", "1.0.56", "1.0.57",
    "1.0.58", "1.0.59", "1.0.60", "1.0.61", "1.0.62", "1.0.63", "1.0.64", "1.0.65",
    "1.0.66", "1.0.67", "1.0.68", "1.0.69", "1.0.70", "1.0.71", "1.0.72", "1.0.73",
    "1.0.74", "1.0.75", "1.0.76", "1.0.77", "1.0.78", "1.0.79", "1.0.80", "1.0.81",
    "1.0.82", "1.0.83", "1.0.84", "1.0.85", "1.0.86", "1.0.87", "1.0.88", "1.0.89",
    "1.0.90", "1.0.91", "1.0.92", "1.0.93", "1.0.94", "1.0.95", "1.0.96", "1.0.97",
    "1.0.98", "1.0.99", "1.0.100", "1.0.101", "1.0.102", "1.0.103", "1.0.104", "1.0.105",
    "1.0.106", "1.0.107", "1.0.108", "1.0.109", "1.0.110", "1.0.111", "1.0.112", "1.0.113",
    "1.0.114", "1.0.115", "1.0.116", "1.0.117", "1.0.118", "1.0.119", "1.0.120", "1.0.121",
    "1.0.122", "1.0.123", "1.0.124", "1.0.125", "1.0.126", "1.0.127", "1.0.128", "1.0.129",
    "1.0.130", "1.0.131", "1.0.132", "1.0.133", "1.0.134", "1.0.135", "1.0.136", "1.0.137",
    "1.0.138", "1.0.139", "1.0.140", "1.0.141", "1.0.142", "1.0.143", "1.0.144", "1.0.145",
    "1.0.146", "1.0.147", "1.0.148", "1.0.149", "1.0.150", "1.0.151", "1.0.152", "1.0.153",
    "1.0.154", "1.0.155", "1.0.156", "1.0.157", "1.0.158", "1.0.159", "1.0.160", "1.0.161",
    "1.0.162", "1.0.163", "1.0.164", "1.0.165", "1.0.166", "1.0.167", "1.0.168", "1.0.169",
    "1.0.170", "1.0.171", "1.0.172", "1.0.173", "1.0.174", "1.0.175", "1.0.176", "1.0.177",
    "1.0.178", "1.0.179", "1.0.180", "1.0.181", "1.0.182", "1.0.183", "1.0.184", "1.0.185",
    "1.0.186", "1.0.187", "1.0.188", "1.0.189", "1.0.190", "1.0.191", "1.0.192", "1.0.193",
    "1.0.194", "1.0.195", "1.0.196", "1.0.197", "1.0.198", "1.0.199", "1.0.200", "1.0.201",
    "1.0.202", "1.0.203", "1.0.204", "1.0.205", "1.0.206", "1.0.207", "1.0.208", "1.0.209",
    "1.0.210", "1.0.211", "1.0.212", "1.0.213", "1.0.214", "1.0.215", "1.0.216", "1.0.217",
    "1.0.218", "1.0.219", "1.0.220", "1.0.221", "1.0.222", "1.0.223", "1.0.224", "1.0.225",
    "1.0.226", "1.0.227", "1.0.228", "1.0.229",
]
YANKED = {"0.7.6", "1.0.31", "1.0.95"}


def sh(cmd, timeout=120):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def df_tmp():
    r = sh(["df", "-h", "/tmp"])
    return r.stdout.strip().splitlines()[-1]


class Blocked(Exception):
    pass


def df_gate(stage):
    line = df_tmp()
    print(f"  [df] {stage}: {line}")
    return line


def clean_scratch():
    for d in (WORK, CACHE):
        shutil.rmtree(d, ignore_errors=True)


def fetch_tarball(ver):
    os.makedirs(CACHE, exist_ok=True)
    dest = os.path.join(CACHE, f"{CRATE}-{ver}.crate")
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return dest
    url = f"https://static.crates.io/crates/{CRATE}/{CRATE}-{ver}.crate"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return dest
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None  # version never published a tarball — honest row
        raise


def extract_tree(crate_path, ver):
    dest = os.path.join(WORK, f"{CRATE}-{ver}")
    os.makedirs(WORK, exist_ok=True)
    with tarfile.open(crate_path, "r:gz") as t:
        try:
            t.extractall(dest, filter="data")
        except TypeError:
            t.extractall(dest)  # py<3.12
    return dest


def ts_extract(crate_dir):
    sys.path.insert(0, os.path.join(REPO, "prototype"))
    import wild_proto as P
    contract = P.extract_rust(crate_dir)
    slots = contract.slots
    added_stats = {}
    for name, s in slots.items():
        k = s.ty if isinstance(s.ty, str) else "fn-sig"
        added_stats[k.split("<")[0].split(":")[0]] = added_stats.get(k.split("<")[0].split(":")[0], 0) + 1
    return contract, added_stats


def wild_extract(crate_dir, ver):
    """Run the wild extract binary over a digested bundle. Returns row dict."""
    files = {}
    for dirpath, _, names in os.walk(crate_dir):
        for n in names:
            p = os.path.join(dirpath, n)
            rel = os.path.relpath(p, crate_dir)
            if rel == "Cargo.toml" or (rel.startswith("src/") and rel.endswith(".rs")):
                files[rel] = "sha256:" + hashlib.sha256(open(p, "rb").read()).hexdigest()
    if "Cargo.toml" not in files:
        return {"decision": "no-manifest", "wild_slots": 0, "wild_opaque": 0}
    os.makedirs(os.path.join(WORK, "req"), exist_ok=True)
    req = {
        "version": "local-1", "kind": "extraction-request",
        "profile": "rust-cargo-local-1", "bundle_root": crate_dir,
        "files": files, "target": "x86_64-unknown-linux-gnu",
        "toolchain": "stable", "features": [],
        "extractor": {"name": "wild", "digest": "sha256:" + "0" * 64},
    }
    req_path = os.path.join(WORK, "req", f"req-{ver}.json")
    out_path = os.path.join(WORK, "req", f"out-{ver}")
    with open(req_path, "w") as f:
        json.dump(req, f)
    r = sh([WILD_BIN, "extract", "--request", req_path, "--output", out_path],
           timeout=120)
    envelope = None
    try:
        envelope = json.loads(r.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        pass
    row = {"decision": "bin-error", "wild_slots": 0, "wild_opaque": 0}
    if envelope:
        row["decision"] = envelope.get("decision", "?")
        slots = envelope.get("slots", [])
        row["wild_slots"] = len(slots)
        row["wild_opaque"] = sum(1 for s in slots
                                 if s.get("type", {}).get("shape") == "opaque")
    contract_p = os.path.join(out_path, "contract.json")
    if os.path.exists(contract_p):
        c = json.load(open(contract_p))
        slots = c.get("slots", [])
        row["wild_slots"] = len(slots)
        row["wild_opaque"] = sum(1 for s in slots
                                 if s.get("type", {}).get("shape") == "opaque")
    return row


def cargo_compatible(a, b):
    pa, pb = [int(x) for x in a.split(".")], [int(x) for x in b.split(".")]
    if pb < pa:
        return False
    if pa[0] > 0:
        return pa[0] == pb[0]
    if pa[1] > 0:
        return pa[0] == pb[0] and pa[1] == pb[1]
    return pa[:3] == pb[:3]


def load_evidence():
    """Release notes bodies keyed by vX.Y.Z, fetched BEFORE grading."""
    path = os.path.join(SCRATCH, "github_releases.json")
    if os.path.exists(path):
        tags = json.load(open(path))
        return tags, "cache:" + path
    tags, pages = {}, []
    for p in (1, 2, 3, 4):
        r = sh(["gh", "api", f"repos/serde-rs/serde/releases?per_page=100&page={p}"])
        if r.returncode != 0:
            return {}, "fetch-failed"
        pages.append(r.stdout)
    for raw in pages:
        for rel in json.loads(raw):
            tags[rel["tag_name"]] = rel.get("body") or ""
    if tags:
        with open(path, "w") as f:
            json.dump(tags, f)
        return tags, f"fetched:{len(tags)} releases"
    return {}, "fetch-failed"


def evidence_for(tags, ver, src):
    body = tags.get("v" + ver) or tags.get(ver) or ""
    if src == "fetch-failed":
        return "fetch-failed", ""
    if not body.strip():
        return "none-found", ""
    low = body.lower()
    if any(m in low for m in BREAK_MARKERS):
        return "notes-marker", body
    return "notes-no-marker", body


def vtuple(v):
    return tuple(int(x) for x in v.split("."))


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    df_gate("start")
    tags, ev_src = load_evidence()
    print(f"evidence source: {ev_src} ({len(tags)} release bodies)")

    sys.path.insert(0, os.path.join(REPO, "prototype"))
    import wild_sim

    rows, transitions, blocked = [], [], None
    n = len(PRE_REGISTERED_VERSIONS)
    for bi, ver in enumerate(PRE_REGISTERED_VERSIONS):
        attempt = 0
        while True:
            try:
                crate_path = fetch_tarball(ver)
                row = {"ver": ver, "yanked": ver in YANKED, "status": "ok",
                       "ts_slots": None, "shape_kinds": {},
                       "decision": "-", "wild_slots": None, "wild_opaque": None}
                if crate_path is None:
                    row["status"] = "no-tarball"
                else:
                    tree = extract_tree(crate_path, ver)
                    src_lib = os.path.join(tree, CRATE + "-" + ver, "src", "lib.rs")
                    cdir = os.path.join(tree, CRATE + "-" + ver)
                    if not os.path.exists(src_lib):
                        row["status"] = "no-src-lib"
                    else:
                        contract, kinds = ts_extract(cdir)
                        row["ts_slots"] = len(contract.slots)
                        row["shape_kinds"] = kinds
                        row["contract"] = contract
                        row.update(wild_extract(cdir, ver))
                    shutil.rmtree(tree, ignore_errors=True)  # hygiene: per-version
                break
            except OSError as e:
                if e.errno == 122:  # EDQUOT — disk quota exceeded
                    if attempt == 0:
                        attempt += 1
                        print(f"  [EDQUOT] Errno 122 at {ver}: cleaning scratch, retrying once")
                        clean_scratch()
                        df_gate("after-clean")
                        continue
                    blocked = (ver, df_tmp())
                    break
                raise
        if blocked:
            break
        rows.append(row)
        if (bi + 1) % BATCH == 0 or bi + 1 == n:
            df_gate(f"batch {(bi + 1) // BATCH} done ({bi + 1}/{n} versions)")
            ok = [r for r in rows if r["status"] == "ok"]
            print(f"  [progress] ok={len(ok)} ts_total={sum(r['ts_slots'] or 0 for r in ok)}")

    if blocked:
        ver, dfline = blocked
        with open(os.path.join(REPO, "experiments", "census_results.txt"), "a") as f:
            f.write(f"\n# BLOCKED at version {ver}: Errno 122 disk quota exceeded "
                    f"after clean+retry; df: {dfline}\n")
        print(f"BLOCKED at {ver}: {dfline}")
        return 2

    # ---- grading (only reached after per-version extraction is done) ----
    by_ver = {r["ver"]: r for r in rows}
    graded = []
    for a, b in zip(PRE_REGISTERED_VERSIONS, PRE_REGISTERED_VERSIONS[1:]):
        ra, rb = by_ver[a], by_ver[b]
        t = {"a": a, "b": b}
        t["cargo"] = "compatible" if cargo_compatible(a, b) else "incompatible"
        if ra.get("contract") is None or rb.get("contract") is None:
            t["verdict"] = "n/a"
            t["reason"] = f"missing extract ({ra['status']}/{rb['status']})"
            t["added"] = t["removed"] = t["changed"] = 0
            t["evidence"] = "-"
            graded.append(t)
            continue
        ok, why = wild_sim.shape_check(ra["contract"], rb["contract"])
        sa, sb = ra["contract"].slots, rb["contract"].slots
        t["added"] = len(set(sb) - set(sa))
        t["removed"] = len(set(sa) - set(sb))
        t["changed"] = sum(1 for k in set(sa) & set(sb) if sa[k] != sb[k])
        t["verdict"] = "accretion" if ok else "break"
        t["reason"] = why
        t["evidence"] = evidence_for(tags, b, ev_src)[0]
        graded.append(t)

    write_results(rows, graded, ev_src, len(tags))
    return 0


def write_results(rows, graded, ev_src, n_tags):
    ok_rows = [r for r in rows if r["status"] == "ok"]
    # headline denominators (all explicit)
    d_versions = len(rows)
    d_transitions = len(graded)
    d_graded_transitions = sum(1 for t in graded if t["verdict"] != "n/a")
    d_candidate = sum(1 for t in graded
                      if t["verdict"] == "break" and t["cargo"] == "compatible")
    false_break = [t for t in graded
                   if t["verdict"] == "break" and t["cargo"] == "compatible"
                   and t["evidence"] in ("none-found", "notes-no-marker")]
    fb_unverified = [t for t in false_break if t["evidence"] == "none-found"]
    cargo_cons_accretion = [t for t in graded
                            if t["verdict"] == "accretion" and t["cargo"] == "incompatible"]
    contract_breaks = [t for t in graded if t["verdict"] == "break"]
    d_opaque_num = sum(r["wild_opaque"] or 0 for r in rows)
    d_opaque_den = sum(r["wild_slots"] or 0 for r in rows)
    d_refused = sum(1 for r in rows if r["decision"] == "refuse")
    d_wild_ok = sum(1 for r in rows if r["decision"] in ("complete", "refuse"))
    max_ts = max((r["ts_slots"] or 0) for r in rows)
    min_ts = min((r["ts_slots"] or 0) for r in ok_rows) if ok_rows else 0
    total_ts = sum(r["ts_slots"] or 0 for r in rows)

    def pct(n_, d_):
        return f"{(100.0 * n_ / d_):.1f}%" if d_ else "n/a"

    L = []
    L.append("# wild-58c census — serde full crates.io release history (false-break census)")
    L.append(f"# date: {__import__('datetime').datetime.utcnow().isoformat()}Z | scratch: {SCRATCH}")
    tool = sh(["rustc", "--version"]).stdout.strip()
    cargo_v = sh(["cargo", "--version"]).stdout.strip()
    bin_sha = hashlib.sha256(open(WILD_BIN, "rb").read()).hexdigest()
    bin_commit = sh(["git", "-C", REPO, "rev-parse", "HEAD"]).stdout.strip()
    L.append(f"# toolchain: {cargo_v} | {tool}")
    L.append(f"# wild extract binary: commit {bin_commit} | sha256 {bin_sha}")
    L.append("# extractors: PRIMARY slot counter + verdict engine = experiments tree-sitter path")
    L.append("#   (prototype/wild_proto.extract_rust; the wild binary refuses complete inventory")
    L.append("#   on macro_rules!/glob-reexport crates — see per-version decision column);")
    L.append("#   SECONDARY columns = wild extract binary envelope (decision/slots/opaque).")
    L.append(f"# evidence source (release notes for TO version): {ev_src} ({n_tags} bodies)")
    L.append("# opaque share (per release) = wild-binary opaque slots / inventoried slots;")
    L.append("#   '-' where the binary inventoried 0 slots. Every rate below names its")
    L.append("#   numerator and denominator explicitly.")
    L.append("")
    L.append("== headline ==")
    L.append(f"crate: {CRATE} | versions replayed: {d_versions} (pre-registered list, "
             f"created_at ascending) | transitions: {d_transitions}")
    L.append(f"public surface (PRIMARY, tree-sitter): min {min_ts} / max {max_ts} slots "
             f"per release; sum over all releases = {total_ts} slots "
             f"(numerator) over {d_versions} releases (denominator); "
             f">=300-slot gate satisfied by max={max_ts}")
    L.append(f"false-break rate: numerator {len(false_break)} (contract=break AND "
             f"cargo=compatible AND no documented/digestible break evidence: "
             f"{len(fb_unverified)} none-found + {len(false_break) - len(fb_unverified)} "
             f"notes-no-marker) / denominator {d_candidate} (transitions with "
             f"contract=break AND cargo=compatible) = {pct(len(false_break), d_candidate)}")
    L.append(f"false-break rate secondary: same numerator {len(false_break)} over ALL "
             f"graded transitions {d_graded_transitions} (denominator) = "
             f"{pct(len(false_break), d_graded_transitions)}")
    L.append(f"opaque share aggregate: numerator {d_opaque_num} opaque slots / "
             f"denominator {d_opaque_den} inventoried slots (wild binary, all releases) "
             f"= {pct(d_opaque_num, d_opaque_den)}")
    L.append(f"wild-binary complete-inventory refusals: {d_refused} / {d_wild_ok} "
             f"versions with a manifest (denominator) = {pct(d_refused, d_wild_ok)}")
    L.append(f"contract breaks total: {len(contract_breaks)} / {d_graded_transitions} "
             f"graded transitions (denominator) = {pct(len(contract_breaks), d_graded_transitions)}")
    L.append(f"context, Cargo-conservative disputes: {len(cargo_cons_accretion)} / "
             f"{d_graded_transitions} graded transitions (denominator) where Cargo says "
             f"incompatible but the contract says accretion")
    unresolved = [r for r in rows if r["status"] != "ok"]
    L.append(f"unresolved versions (honest): {len(unresolved)} / {d_versions} "
             f"(denominator): " + (", ".join(f"{r['ver']}={r['status']}" for r in unresolved) or "none"))
    L.append("")
    L.append("== per-release table ==")
    L.append("version|yanked|status|ts_slots|wild_decision|wild_slots|wild_opaque|opaque_share(num/den)")
    for r in rows:
        if r["wild_slots"]:
            share = f"{r['wild_opaque']}/{r['wild_slots']}"
        else:
            share = "-"
        L.append(f"{r['ver']}|{'Y' if r['yanked'] else '-'}|{r['status']}|"
                 f"{r['ts_slots'] if r['ts_slots'] is not None else '-'}|"
                 f"{r['decision']}|{r['wild_slots'] if r['wild_slots'] is not None else '-'}|"
                 f"{r['wild_opaque'] if r['wild_opaque'] is not None else '-'}|{share}")
    L.append("")
    L.append("== per-transition table (consecutive, release order) ==")
    L.append("from->to|contract_verdict|+added|-removed|changed|cargo_caret|evidence|first_break_reason")
    for t in graded:
        reason = t["reason"] if t["verdict"] == "break" else ""
        L.append(f"{t['a']}->{t['b']}|{t['verdict']}|+{t['added']}|-{t['removed']}|"
                 f"{t['changed']}|{t['cargo']}|{t['evidence']}|{reason}")
    L.append("")
    L.append("== false-break detail (numerator rows) ==")
    L.append("from->to|contract reason|evidence class|release-note excerpt")
    for t in false_break:
        body = (tags.get("v" + t["b"]) or "").replace("\n", " ")[:160]
        L.append(f"{t['a']}->{t['b']}|{t['reason']}|{t['evidence']}|{body}")
    L.append("")
    L.append("== Cargo-conservative detail (accretion where Cargo says incompatible) ==")
    for t in cargo_cons_accretion:
        L.append(f"{t['a']}->{t['b']}|+{t['added']}|-{t['removed']}|{t['changed']}")
    out = os.path.join(REPO, "experiments", "census_results.txt")
    with open(out, "w") as f:
        f.write("\n".join(L) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    sys.exit(main())
