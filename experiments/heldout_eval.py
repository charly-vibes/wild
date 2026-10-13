#!/usr/bin/env python3
# Purpose: Held-out validation harness for Wild upgrade decisions against
#   existing checks (beads wild-1xk).
# Responsibilities: Freeze and verify evaluation tooling digests; enforce the
#   sealed development/held-out split by repo/release family; seal independent
#   oracle outcomes before any held-out comparison; run pluggable checkers
#   (host declared ranges, CI, ecosystem compatibility tools, Wild) per case;
#   classify each verdict into exactly one outcome class; render a
#   separate-metrics report where missed breakages, false blocks, Unknown rate,
#   coverage, execution cost, and human contract-maintenance time each carry
#   their own denominator and are never merged into aggregate accuracy.
# Rationale: The viability evaluation showed aggregate accuracy conceals the
#   safety tradeoff (3/4 missed breakages vs 1/4 for declared ranges). Every
#   metric here is reported separately with explicit denominators. Outputs are
#   value-proposition validation only — never evidence about future v1 runtime
#   failure rates.

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

DISCLAIMER = (
    "This is validation of the value proposition, not evidence that the "
    "future v1 runtime has the prototype failure rates."
)

VERDICTS = {"accept", "reject", "unknown", "error"}
POOLS = {"development", "held_out"}
CHECKER_TIMEOUT_SECONDS = 60


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _die(message: str) -> int:
    print(message, file=sys.stderr)
    return 2


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


# --- freeze -----------------------------------------------------------------


def _freeze_entries(freeze_dir: Path) -> list[dict]:
    return _load_json(freeze_dir / "freeze.json")["tools"]


def _verify_freeze(freeze_dir: Path) -> int:
    for tool in _freeze_entries(freeze_dir):
        path = Path(tool["path"])
        if not path.exists():
            return _die(f"freeze drift: {path} is missing from the frozen toolchain")
        actual = _sha256_file(path)
        if actual != tool["sha256"]:
            return _die(
                f"freeze drift: {path} changed since freeze "
                f"(expected {tool['sha256'][:12]}, got {actual[:12]}); "
                "re-freeze before evaluating"
            )
    return 0


def cmd_freeze(args: argparse.Namespace) -> int:
    tools = []
    for raw in args.tool:
        path = Path(raw).resolve()
        if not path.exists():
            return _die(f"freeze: tool path does not exist: {path}")
        tools.append({"path": str(path), "sha256": _sha256_file(path)})
    _write_json(Path(args.out) / "freeze.json",
                {"kind": "heldout-freeze", "version": 1, "tools": tools})
    print(f"froze {len(tools)} tool(s) into {args.out}/freeze.json")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    return _verify_freeze(Path(args.freeze))


# --- split ------------------------------------------------------------------


def _split_document(cases: list[dict]) -> dict:
    """Deterministic split document; assumes family integrity was validated."""
    pool_by_case = {case["id"]: case["pool"] for case in cases}
    families: dict[str, str] = {}
    for case in sorted(cases, key=lambda c: c["id"]):
        families[case["family"]] = case["pool"]
    return {
        "kind": "heldout-split",
        "version": 1,
        "pool_by_case": dict(sorted(pool_by_case.items())),
        "families": dict(sorted(families.items())),
    }


def cmd_split(args: argparse.Namespace) -> int:
    cases = _load_json(Path(args.cases))["cases"]
    by_family: dict[str, set[str]] = {}
    for case in cases:
        if case["pool"] not in POOLS:
            return _die(f"split: case {case['id']} has unknown pool {case['pool']!r}")
        by_family.setdefault(case["family"], set()).add(case["pool"])
    for family, pools in by_family.items():
        if len(pools) > 1:
            return _die(
                f"split: family {family!r} spans pools {sorted(pools)} — "
                "a repo/release family must sit entirely in one pool "
                "(leakage guard); reassign and re-split"
            )
    split = _split_document(cases)
    _write_json(Path(args.out) / "split.json", split)
    print(f"split {len(cases)} case(s): "
          f"{sum(1 for p in split['pool_by_case'].values() if p == 'held_out')} held_out")
    return 0


def cmd_dev_select(args: argparse.Namespace) -> int:
    split = _load_json(Path(args.split) / "split.json")
    for case_id in args.ids.split(","):
        case_id = case_id.strip()
        if split["pool_by_case"].get(case_id) == "held_out":
            return _die(
                f"leakage guard: case {case_id} is held_out; development "
                "commands may not touch held_out data"
            )
        if case_id not in split["pool_by_case"]:
            return _die(f"dev-select: unknown case id {case_id!r}")
    print("all requested ids are development-side")
    return 0


# --- seal -------------------------------------------------------------------


def cmd_seal(args: argparse.Namespace) -> int:
    oracle_path = Path(args.oracle)
    oracle = _load_json(oracle_path)
    case_ids = sorted(o["case_id"] for o in oracle["outcomes"])
    _write_json(Path(args.out) / "oracle.seal.json", {
        "kind": "heldout-oracle-seal",
        "version": 1,
        "oracle_sha256": _sha256_file(oracle_path),
        "case_ids": case_ids,
    })
    print(f"sealed oracle covering {len(case_ids)} case(s) into {args.out}/oracle.seal.json")
    return 0


# --- compare ----------------------------------------------------------------


def _oracle_outcomes(oracle: dict) -> dict[str, str]:
    outcomes = {}
    for entry in oracle["outcomes"]:
        if entry["outcome"] not in {"break", "ok"}:
            continue
        outcomes[entry["case_id"]] = entry["outcome"]
    return outcomes


def _classify(verdict: str, oracle_outcome: str) -> str:
    if verdict in {"unknown", "error"}:
        return "unknown"
    if verdict == "accept":
        return "missed-breakage" if oracle_outcome == "break" else "correct-accept"
    return "correct-reject" if oracle_outcome == "break" else "false-block"


def _run_checker(cmd: list[str], case_id: str) -> tuple[str, float, str]:
    """Run one checker for one case.

    Strictness (intended, per RO5U EDGE-001): only the last non-empty stdout
    line is parsed as the verdict document; trailing diagnostics downgrade the
    verdict to error rather than being skipped over.
    """
    started = time.monotonic()
    try:
        proc = subprocess.run(
            [*cmd, case_id], capture_output=True, text=True,
            timeout=CHECKER_TIMEOUT_SECONDS,
        )
        elapsed = round(time.monotonic() - started, 6)
        lines = [line for line in proc.stdout.splitlines() if line.strip()]
        if proc.returncode != 0:
            return "error", elapsed, (
                f"checker exited {proc.returncode}; stderr tail: {proc.stderr[-200:]!r}")
        if lines:
            verdict = json.loads(lines[-1]).get("verdict")
            if verdict in VERDICTS:
                return verdict, elapsed, ""
        return "error", elapsed, f"unparseable checker output: {proc.stdout[-200:]!r}"
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError) as exc:
        elapsed = round(time.monotonic() - started, 6)
        return "error", elapsed, f"checker invocation failed: {exc}"


def cmd_compare(args: argparse.Namespace) -> int:
    freeze_dir = Path(args.freeze)
    rc = _verify_freeze(freeze_dir)
    if rc != 0:
        return rc

    split = _load_json(Path(args.split) / "split.json")
    pool = args.pool
    if pool not in POOLS:
        return _die(f"compare: unknown pool {pool!r}")
    case_ids = sorted(cid for cid, p in split["pool_by_case"].items() if p == pool)
    if not case_ids:
        return _die(f"compare: pool {pool!r} has no cases")

    seal_path = Path(args.seal) / "oracle.seal.json"
    if pool == "held_out":
        if not seal_path.exists():
            return _die(
                f"compare: no oracle seal at {seal_path}; held-out comparison "
                "requires sealed independent outcomes before any Wild run"
            )
        seal = _load_json(seal_path)
        actual = _sha256_file(Path(args.oracle))
        if actual != seal["oracle_sha256"]:
            return _die(
                f"compare: oracle digest mismatch after seal "
                f"(sealed {seal['oracle_sha256'][:12]}, now {actual[:12]}); "
                "held-out outcomes changed post-seal — evaluation is void"
            )

    oracle_path = Path(args.oracle)
    oracle = _load_json(oracle_path)
    missing = [cid for cid in case_ids if cid not in _oracle_outcomes(oracle)]
    if missing:
        return _die(
            f"compare: pool case(s) missing independent oracle outcome(s): "
            f"{', '.join(missing)} — seal outcomes for every pool case first"
        )
    outcomes = _oracle_outcomes(oracle)

    checkers = _load_json(Path(args.checkers))["checkers"]
    runs = []
    for checker in checkers:
        for case_id in case_ids:
            verdict, elapsed, note = _run_checker(checker["cmd"], case_id)
            runs.append({
                "case_id": case_id,
                "checker": checker["name"],
                "verdict": verdict,
                "outcome_class": _classify(verdict, outcomes[case_id]),
                "elapsed_seconds": elapsed,
                "note": note,
            })

    definite_failures = [r for r in runs
                         if r["outcome_class"] in {"missed-breakage", "false-block"}]
    _write_json(Path(args.out), {
        "kind": "heldout-compare",
        "version": 1,
        "pool": pool,
        "freeze_sha256": _sha256_file(freeze_dir / "freeze.json"),
        "oracle_sha256": _sha256_file(Path(args.oracle)),
        "runs": runs,
    })
    if definite_failures:
        print(f"comparison found {len(definite_failures)} definite failure(s); "
              f"report written to {args.out}")
        return 1
    print(f"comparison clean; report written to {args.out}")
    return 0


# --- report -----------------------------------------------------------------


def _ratio(count: int, denominator: int, reason: str) -> dict:
    if denominator == 0:
        return {"ratio": None, "denominator": 0,
                "reason": f"zero-denominator: {reason}"}
    return {"ratio": round(count / denominator, 4), "denominator": denominator}


def _checker_section(name: str, runs: list[dict], break_count: int, ok_count: int) -> list[str]:
    missed = sum(1 for r in runs if r["outcome_class"] == "missed-breakage")
    false_blocks = sum(1 for r in runs if r["outcome_class"] == "false-block")
    unknown = sum(1 for r in runs if r["outcome_class"] == "unknown")
    covered = len(runs) - unknown
    total = len(runs)
    lines = [
        f"## checker: {name}",
        "",
        "### missed-breakage",
        f"- count: {missed}",
        f"- denominator: {break_count} (definite-break cases)",
        f"- ratio: {json.dumps(_ratio(missed, break_count, 'no definite-break cases in pool'))}",
        "",
        "### false-block",
        f"- count: {false_blocks}",
        f"- denominator: {ok_count} (definite-ok cases)",
        f"- ratio: {json.dumps(_ratio(false_blocks, ok_count, 'no definite-ok cases in pool'))}",
        "",
        "### unknown-rate",
        f"- count: {unknown}",
        f"- denominator: {total} (cases run for this checker)",
        f"- ratio: {json.dumps(_ratio(unknown, total, 'no cases run'))}",
        "",
        "### coverage",
        f"- count: {covered}",
        f"- denominator: {total} (cases run for this checker)",
        f"- ratio: {json.dumps(_ratio(covered, total, 'no cases run'))}",
        "",
    ]
    return lines


def cmd_report(args: argparse.Namespace) -> int:
    compare = _load_json(Path(args.compare))
    cases = _load_json(Path(args.cases))["cases"]
    runs_by_checker: dict[str, list[dict]] = {}
    for run in compare["runs"]:
        runs_by_checker.setdefault(run["checker"], []).append(run)

    # Denominators come from the independent oracle outcomes, re-supplied by
    # the caller so the report stays honest even if verdicts were classified
    # in an earlier run.
    pool_cases = sorted({run["case_id"] for run in compare["runs"]})
    oracle_path = Path(args.oracle)
    oracle_digest = _sha256_file(oracle_path)
    sealed_digest = compare.get("oracle_sha256")
    if sealed_digest and oracle_digest != sealed_digest:
        return _die(
            f"report: oracle digest mismatch against the compare artifact "
            f"(compare {sealed_digest[:12]}, supplied {oracle_digest[:12]}); "
            "denominators must come from the oracle the runs were graded against"
        )
    oracle = _load_json(oracle_path)
    outcomes = _oracle_outcomes(oracle)
    break_count = sum(1 for cid in pool_cases if outcomes.get(cid) == "break")
    ok_count = sum(1 for cid in pool_cases if outcomes.get(cid) == "ok")

    lines = [
        "# Held-out evaluation report",
        "",
        DISCLAIMER,
        "",
        "## execution-cost",
    ]
    elapsed_by_checker: dict[str, list[float]] = {}
    for run in compare["runs"]:
        elapsed_by_checker.setdefault(run["checker"], []).append(run["elapsed_seconds"])
    for name, elapsed in sorted(elapsed_by_checker.items()):
        total = round(sum(elapsed), 6)
        lines.append(f"- {name}: {total}s measured (sum of per-run elapsed_seconds)")
    lines.append("")
    lines.append("## human-contract-maintenance-time")
    any_unavailable = False
    for case in cases:
        if case["id"] not in pool_cases:
            continue
        entry = case.get("human_minutes", {"value": None, "basis": "unavailable"})
        if entry.get("value") is None or entry.get("basis") != "measured":
            any_unavailable = True
            lines.append(f"- {case['id']}: unavailable (basis: {entry.get('basis')})")
        else:
            lines.append(f"- {case['id']}: {entry['value']} min (basis: measured)")
    if any_unavailable:
        lines.append("- unavailable entries are reported as null, never as fabricated zeros")
    lines.append("")

    for name in sorted(runs_by_checker):
        lines.extend(_checker_section(name, runs_by_checker[name], break_count, ok_count))

    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"report written to {args.out}")
    return 0


# --- CLI --------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="heldout_eval.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("freeze", help="freeze evaluation tooling digests")
    p.add_argument("--tool", action="append", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_freeze)

    p = sub.add_parser("verify", help="verify frozen tooling digests")
    p.add_argument("--freeze", required=True)
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("split", help="commit the development/held-out split")
    p.add_argument("--cases", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_split)

    p = sub.add_parser("dev-select", help="development-side case selection (leakage guard)")
    p.add_argument("--split", required=True)
    p.add_argument("--ids", required=True)
    p.set_defaults(func=cmd_dev_select)

    p = sub.add_parser("seal", help="seal independent oracle outcomes")
    p.add_argument("--oracle", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_seal)

    p = sub.add_parser("compare", help="run checkers and classify verdicts")
    p.add_argument("--freeze", required=True)
    p.add_argument("--split", required=True)
    p.add_argument("--cases", required=True)
    p.add_argument("--oracle", required=True)
    p.add_argument("--seal", required=True)
    p.add_argument("--checkers", required=True)
    p.add_argument("--pool", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_compare)

    p = sub.add_parser("report", help="render the separate-metrics report")
    p.add_argument("--compare", required=True)
    p.add_argument("--cases", required=True)
    p.add_argument("--oracle", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_report)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())