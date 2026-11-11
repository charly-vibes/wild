#!/usr/bin/env python3
# Purpose: Derive the sealed wild-1xk held-out comparison corpus from the
#   committed e5 cohort (beads wild-1xk remaining scope).
# Responsibilities: Map the cohort's independently established verdicts
#   (real Cargo replay before any miner tuning) into the landed heldout_eval
#   harness's case/oracle shapes; exclude oracle-unresolvable (unresolved)
#   cases with recorded reasons; emit real-adapter case context and the
#   four-checker registration for the harness. wild-zfw: optionally merge
#   the python execution-oracle matrix (section-2 recorded cells + fresh
#   cells, drift-poisoned cells excluded with reasons) into a multi-
#   ecosystem corpus.
# Rationale: The harness (experiments/heldout_eval.py) is checker-agnostic
#   and sealed-oracle-gated; this slice supplies its honest inputs. The
#   committed cohort is never rewritten — the corpus is derived read-only.

from __future__ import annotations

import argparse
import json
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXPECTED_SCHEMA = "wild-e5-cases-v1"
VERDICTS = {"compatible": "ok", "incompatible": "break"}
CARGO_ADAPTER_FLAGS = {
    "host_ranges": ["--context", "experiments/heldout/case_context.json"],
    "ecosystem": ["--context", "experiments/heldout/case_context.json"],
    "wild": ["--context", "experiments/heldout/case_context.json"],
    # ci replays through update_eval.py against the frozen registry and
    # takes its case context from the cohort fixtures, not the corpus.
    "ci": ["--fixtures", "experiments/update_fixtures/e5"],
}
PY_ADAPTER_FLAGS = {
    "py_declared": ["--context", "experiments/heldout/case_context.json"],
    "py_wild": ["--context", "experiments/heldout/case_context.json",
                "--python-root", "/tmp/wild-zfw-scratch/pytrees"],
}
UNRESOLVED_REASON = (
    "oracle-unresolvable: e5 independent_verdict is unresolved "
    "(resolution-level refusal, not an upgrade-compatibility outcome)"
)


def _die(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _repo_rel(path: Path) -> str:
    """Repo-relative when possible, absolute otherwise (tmp-scope tests)."""
    resolved = path.resolve()
    if resolved.is_relative_to(REPO):
        return str(resolved.relative_to(REPO))
    return str(resolved)


def _base_version(consumer: Path) -> str:
    lock = consumer / "Cargo.lock"
    try:
        data = tomllib.loads(lock.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"unreadable Cargo.lock at {lock}: {exc}") from exc
    for package in data.get("package", []):
        if package.get("name") == "dept":
            return package["version"]
    raise ValueError(f"no dept package in {lock}")


def cmd_build(args: argparse.Namespace) -> int:
    cohort_path = Path(args.cohort)
    try:
        cohort = json.loads(cohort_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return _die(f"cohort: unreadable cohort file: {exc}")
    if cohort.get("schema") != EXPECTED_SCHEMA or not isinstance(
            cohort.get("cases"), list):
        return _die(
            f"cohort: unexpected schema {cohort.get('schema')!r} "
            f"(expected {EXPECTED_SCHEMA!r} with a cases list)")

    seen_ids: set[str] = set()
    for case in cohort["cases"]:
        case_id = case.get("id")
        if not case_id:
            return _die("cohort: case missing id")
        if case_id in seen_ids:
            return _die(f"cohort: duplicate case id {case_id!r}")
        seen_ids.add(case_id)

    fixtures_root = cohort_path.parent
    cases: list[dict] = []
    outcomes: list[dict] = []
    excluded: list[dict] = []
    context: list[dict] = []
    for case in cohort["cases"]:
        case_id = case.get("id")
        split = case.get("split")
        verdict = case.get("independent_verdict")
        if not case_id or split not in {"development", "evaluation"}:
            return _die(f"cohort: case {case_id!r} missing id/split")
        if verdict == "unresolved":
            excluded.append({"id": case_id, "family": case_id,
                             "reason": UNRESOLVED_REASON})
            continue
        if verdict not in VERDICTS:
            return _die(
                f"cohort: case {case_id} has unknown independent_verdict "
                f"{verdict!r}")
        consumer = case.get("consumer")
        target = case.get("target")
        if not consumer or not target:
            return _die(f"cohort: case {case_id} missing consumer/target")
        consumer_dir = (fixtures_root / consumer).resolve()
        if not (consumer_dir / "Cargo.lock").is_file():
            return _die(f"cohort: case {case_id} consumer tree missing "
                        f"Cargo.lock at {consumer_dir}")
        try:
            base = _base_version(consumer_dir)
        except ValueError as exc:
            return _die(str(exc))
        cases.append({
            "id": case_id,
            "family": case_id,
            "pool": "held_out" if split == "evaluation" else "development",
            "human_minutes": {"value": None, "basis": "unavailable"},
        })
        outcomes.append({"case_id": case_id, "outcome": VERDICTS[verdict]})
        context.append({
            "id": case_id,
            "consumer": _repo_rel(consumer_dir),
            "target": target,
            "base": base,
        })

    cases.sort(key=lambda c: c["id"])
    outcomes.sort(key=lambda o: o["case_id"])
    excluded.sort(key=lambda e: e["id"])
    context.sort(key=lambda c: c["id"])

    if args.python_matrix:
        matrix = json.loads(Path(args.python_matrix).read_text(encoding="utf-8"))
        if matrix.get("kind") != "heldout-python-matrix" or not isinstance(
                matrix.get("cells"), list):
            return _die(f"python-matrix: unexpected kind {matrix.get('kind')!r}")
        for cell in matrix["cells"]:
            cid = cell["id"]
            if cid in seen_ids:
                return _die(f"python-matrix: duplicate case id {cid!r}")
            seen_ids.add(cid)
            oracle = cell.get("oracle")
            if not oracle or oracle.get("outcome") not in {"ok", "break"}:
                return _die(f"python-matrix: cell {cid} lacks an ok/break oracle outcome")
            cons = cid.split("--")[0].split("py-", 1)[1]  # e.g. flask-2.2.5
            consumer, _, consumer_version = cons.rpartition("-")
            provider, _, target = cid.split("--")[1].rpartition("-")
            dev = matrix["consumers"][consumer]["dev"][consumer_version]
            cases.append({"id": cid, "family": cell["family"], "pool": "held_out",
                          "ecosystem": "python",
                          "human_minutes": {"value": None, "basis": "unavailable"}})
            outcomes.append({"case_id": cid, "outcome": oracle["outcome"],
                             "basis": oracle["basis"], "source": cell["source"]})
            context.append({"id": cid, "ecosystem": "python",
                            "consumer": consumer, "consumer_version": consumer_version,
                            "provider": provider, "target": target, "dev": dev})
        for rec in matrix.get("excluded", []):
            excluded.append({"id": rec["id"], "family": rec["family"],
                             "reason": rec["reason"]})
        excluded.sort(key=lambda e: e["id"])

    if not any(case["pool"] == "held_out" for case in cases):
        return _die(
            "cohort: no adjudicable held_out cases remain after excluding "
            "oracle-unresolvable verdicts; nothing to compare")

    for case in cases:
        case.setdefault("ecosystem", "cargo")
    for entry in context:
        entry.setdefault("ecosystem", "cargo")

    out = Path(args.out)
    _write_json(out / "cases.json",
                {"version": 1, "kind": "heldout-cases", "cases": cases})
    _write_json(out / "oracle.json",
                {"oracle": "independent-prepared", "outcomes": outcomes})
    _write_json(out / "excluded.json",
                {"version": 1, "kind": "heldout-excluded",
                 "excluded": excluded})
    _write_json(out / "case_context.json",
                {"version": 1, "kind": "heldout-case-context",
                 "cases": context})
    context_arg = _repo_rel(out / "case_context.json")
    adapter_flags = {name: ["--context", context_arg] if f[0] == "--context" else list(f)
                     for name, f in CARGO_ADAPTER_FLAGS.items()}
    adapter_flags["ci"] = list(CARGO_ADAPTER_FLAGS["ci"])
    for name, f in PY_ADAPTER_FLAGS.items():
        adapter_flags[name] = ["--context", context_arg] + list(f)[2:]
    names = ("host_ranges", "ci", "ecosystem", "wild") + (
        ("py_declared", "py_wild") if args.python_matrix else ())
    ecosystems = {name: ["cargo"] for name in (
        "host_ranges", "ci", "ecosystem", "wild")}
    ecosystems.update({name: ["python"] for name in ("py_declared", "py_wild")})
    _write_json(out / "checkers.json", {
        "version": 1,
        "kind": "heldout-checkers",
        "checkers": [
            {"name": name, "ecosystems": ecosystems[name],
             "cmd": ["python3", f"experiments/heldout_adapters/{name}.py",
                     *adapter_flags[name]]}
            for name in names
        ],
    })
    eco = {e for e in (c.get("ecosystem") for c in cases)}
    print(f"corpus: {len(cases)} case(s) "
          f"({sum(1 for c in cases if c['pool'] == 'held_out')} held_out, "
          f"{len(excluded)} excluded) across ecosystems {sorted(eco)}, "
          f"{len(outcomes)} oracle outcome(s), {len(names)} adapter(s) "
          f"registered in {out}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="derive the sealed held-out corpus from the committed e5 "
                    "cohort (wild-1xk)")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser(
        "build", help="derive corpus cases, sealed-oracle outcomes, excluded "
                      "records, case context, and adapter registration")
    build.add_argument("--cohort", required=True,
                       help="path to the committed e5 cases.json")
    build.add_argument("--out", required=True,
                       help="output directory for the corpus artifacts")
    build.add_argument("--python-matrix",
                       default="experiments/heldout/python_matrix.json",
                       help="python execution-oracle matrix to merge (wild-zfw); "
                            "pass an empty string to build the legacy cargo-only "
                            "corpus")
    build.set_defaults(func=cmd_build)
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())