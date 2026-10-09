#!/usr/bin/env python3
# Purpose: Deterministic validation and summary CLI for the controlled
#   update evaluation harness (beads wild-aoq.1).
# Responsibilities: Validate committed protocol and run records against
#   experiments/update-protocol.schema.json plus cross-record semantics
#   (unique ids, artifact commitments, cost honesty, confirmatory
#   preregistration); summarize candidate outcomes and task completions
#   with the exact denominators from the change design — never inflating
#   successes, hiding failed effort, or substituting zero for null.
# Rationale: The harness's first acceptance is a working measurement
#   pipeline (design.md 'Commands and records', 'Outcomes and exact
#   denominators'). Validation and summary are deterministic functions of
#   committed records; experimental execution (arms, agents, oracles) is
#   intentionally out of scope here and arrives in later slices. Records
#   are append-only in spirit: a defective record invalidates summaries
#   rather than being corrected in place.

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema

SCHEMA_PATH = Path(__file__).resolve().parent / "update-protocol.schema.json"
COST_FIELDS = ("human_minutes", "compute_cost_usd", "wall_time_minutes")
SCHEMA_VERSION = 1


class RecordErrors:
    """Collects validation errors; each message stands alone."""

    def __init__(self) -> None:
        self.items: list[str] = []

    def add(self, message: str) -> None:
        self.items.append(message)

    @property
    def ok(self) -> bool:
        return not self.items

    def report(self) -> str:
        return "\n".join(f"- {m}" for m in self.items)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def schema_validator() -> jsonschema.protocols.Validator:
    schema = load_json(SCHEMA_PATH)
    cls = jsonschema.validators.validator_for(schema)
    cls.check_schema(schema)
    return cls(schema)


def deepest_error(err: jsonschema.exceptions.ValidationError) -> jsonschema.exceptions.ValidationError:
    """Descend into oneOf/anyOf context to report the real failing path
    instead of a whole-instance mismatch at <root>."""
    best = err
    while best.context:
        best = max(best.context, key=lambda e: len(list(e.absolute_path)))
    return best


def structural_errors(instance: dict, validator, label: str, errors: RecordErrors) -> None:
    for err in sorted(validator.iter_errors(instance), key=lambda e: list(e.absolute_path)):
        deep = deepest_error(err)
        where = ".".join(str(p) for p in deep.absolute_path) or "<root>"
        errors.add(f"{label} schema violation at {where}: {deep.message}")


def check_digest(value: object, label: str, errors: RecordErrors) -> bool:
    if isinstance(value, str) and value.startswith("sha256:") and len(value) == 71:
        return True
    errors.add(f"{label}: not a committed sha256 digest")
    return False


def check_protocol_semantics(proto: dict, errors: RecordErrors) -> None:
    if proto.get("schema_version") != SCHEMA_VERSION:
        errors.add(
            f"unsupported schema_version {proto.get('schema_version')!r}; "
            f"this validator speaks version {SCHEMA_VERSION} only"
        )
    if proto.get("record_type") != "protocol":
        errors.add("protocol record_type must be 'protocol'")

    task_ids = [t.get("task_id") for t in proto.get("tasks", [])]
    dupes = sorted({i for i in task_ids if task_ids.count(i) > 1})
    if dupes:
        errors.add(f"duplicate task ids in protocol: {', '.join(sorted(dupes))}")

    # Confirmatory gate: refuse missing preregistration fields by name while
    # fixture-labelled runs stay possible.
    if proto.get("mode") == "confirmatory":
        pre = proto.get("preregistration")
        if not isinstance(pre, dict):
            errors.add(
                "confirmatory mode refused: missing fields risk_margin, "
                "completion_margin, stopping_rules"
            )
        else:
            missing = [f for f in ("risk_margin", "completion_margin", "stopping_rules") if f not in pre]
            if missing:
                errors.add(f"confirmatory mode refused: missing fields {', '.join(missing)}")

    for task in proto.get("tasks", []):
        tid = task.get("task_id", "<unnamed>")
        commit = task.get("oracle_commitment") or {}
        check_digest(commit.get("tests_digest"), f"task {tid} oracle_commitment.tests_digest", errors)


def check_task_result_semantics(result: dict, name: str, errors: RecordErrors) -> None:
    attempts = result.get("attempts", [])
    oracles = result.get("oracle_results", [])
    attempt_ids = [a.get("attempt_id") for a in attempts]
    dupes = sorted({i for i in attempt_ids if attempt_ids.count(i) > 1})
    if dupes:
        errors.add(f"{name}: duplicate attempt ids: {', '.join(sorted(dupes))}")
    oracle_ids = [o.get("attempt_id") for o in oracles]
    dupes = sorted({i for i in oracle_ids if oracle_ids.count(i) > 1})
    if dupes:
        errors.add(f"{name}: duplicate oracle result ids: {', '.join(sorted(dupes))}")

    by_attempt = {a.get("attempt_id"): a for a in attempts}
    graded = {o.get("attempt_id"): o for o in oracles}
    for oid, oracle in graded.items():
        if oid not in by_attempt:
            errors.add(f"{name}: oracle result references unknown attempt {oid!r}")
            continue
        requested = by_attempt[oid].get("requested_artifact", {}).get("digest")
        actual = oracle.get("graded_artifact", {}).get("digest")
        if requested != actual:
            errors.add(
                f"{name}: attempt {oid!r} requested/graded artifact mismatch: "
                f"requested {requested!r} but oracle graded {actual!r}"
            )

    delivered = result.get("delivered")
    if isinstance(delivered, dict) and delivered.get("attempt_id") not in by_attempt:
        errors.add(
            f"{name}: delivered references unknown attempt {delivered.get('attempt_id')!r}"
        )

    for att in attempts:
        aid = att.get("attempt_id", "<unnamed>")
        costs = att.get("costs") or {}
        for field in COST_FIELDS:
            entry = costs.get(field)
            if not isinstance(entry, dict):
                continue  # absent/ill-formed handled by the schema layer
            if entry.get("basis") in ("unavailable", "inapplicable") and "value" in entry:
                errors.add(
                    f"{name}: attempt {aid!r} cost {field} declares "
                    f"{entry['basis']} but carries a value — missing cost is "
                    "never zero; drop the value or measure it"
                )


def load_and_validate(protocol_path: Path, runs_dir: Path | None, errors: RecordErrors) -> tuple[dict, list[dict]]:
    validator = schema_validator()

    try:
        proto = load_json(protocol_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.add(f"cannot read protocol {protocol_path}: {exc}")
        return {}, []

    structural_errors(proto, validator, "protocol", errors)
    check_protocol_semantics(proto, errors)

    results: list[dict] = []
    if runs_dir is None:
        return proto, results
    if not runs_dir.is_dir():
        errors.add(f"runs directory not found: {runs_dir}")
        return proto, results

    seen_keys: dict[tuple, str] = {}
    for path in sorted(runs_dir.glob("*.json")):
        name = path.name
        try:
            result = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            errors.add(f"cannot read run record {name}: {exc}")
            continue
        structural_errors(result, validator, f"run {name}", errors)
        check_task_result_semantics(result, name, errors)
        key = (result.get("task_id"), result.get("arm"), result.get("trial"))
        if key in seen_keys:
            errors.add(f"duplicate task/arm/trial record: {name} repeats {seen_keys[key]}")
        else:
            seen_keys[key] = name
        results.append(result)
    return proto, results


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


def ratio(num: int, den: int, zero_reason: str) -> dict:
    if den == 0:
        return {"num": num, "den": 0, "value": None, "reason": zero_reason}
    return {"num": num, "den": den, "value": num / den}


def effort_field(attempts: list[dict], field: str) -> dict:
    measured = 0.0
    unavailable = 0
    inapplicable = 0
    for att in attempts:
        entry = (att.get("costs") or {}).get(field) or {}
        basis = entry.get("basis")
        if basis == "measured":
            measured += float(entry.get("value") or 0.0)
        elif basis == "unavailable":
            unavailable += 1
        elif basis == "inapplicable":
            inapplicable += 1
    return {"measured": measured, "unavailable_count": unavailable, "inapplicable_count": inapplicable}


def summarize(proto: dict, results: list[dict]) -> dict:
    attempts: list[tuple[dict, dict | None]] = []
    for result in results:
        graded = {o.get("attempt_id"): o for o in result.get("oracle_results", [])}
        for att in result.get("attempts", []):
            attempts.append((att, graded.get(att.get("attempt_id"))))

    assigned = len(attempts)
    eligible_adjudicated = []
    incompatible_pool = []
    compatible_pool = []
    policy_ineligible = 0
    ineligible_reasons: dict[str, int] = {}
    oracle_unresolved = 0
    accepted_oracle_unresolved = 0
    adjudicated = 0
    unknown_count = 0
    error_count = 0

    for att, oracle in attempts:
        outcome = att.get("checker_outcome")
        if outcome == "unknown":
            unknown_count += 1
        elif outcome == "error":
            error_count += 1
        verdict = (oracle or {}).get("verdict")
        if verdict in ("compatible", "incompatible"):
            adjudicated += 1
        if verdict == "unresolved":
            oracle_unresolved += 1
            if outcome == "accept":
                accepted_oracle_unresolved += 1
        eligible = (oracle or {}).get("eligibility", {}).get("eligible", False)
        if not eligible:
            policy_ineligible += 1
            for reason in (oracle or {}).get("eligibility", {}).get("reasons", []) or ["unspecified"]:
                ineligible_reasons[reason] = ineligible_reasons.get(reason, 0) + 1
            continue  # excluded from the binary table entirely
        if verdict == "incompatible":
            incompatible_pool.append((att, outcome))
        elif verdict == "compatible":
            compatible_pool.append((att, outcome))
        if verdict in ("compatible", "incompatible"):
            eligible_adjudicated.append((att, outcome, verdict))

    accepted_adjudicated = [x for x in eligible_adjudicated if x[1] == "accept"]
    unsafe = sum(1 for x in accepted_adjudicated if x[2] == "incompatible")
    compat_rejected_incompatible = sum(
        1 for att, outcome in incompatible_pool
        if outcome == "reject" and att.get("checker_reason") == "compatibility"
    )
    accepted_incompatible = sum(1 for att, outcome in incompatible_pool if outcome == "accept")
    compat_rejected_compatible = sum(
        1 for att, outcome in compatible_pool
        if outcome == "reject" and att.get("checker_reason") == "compatibility"
    )

    candidate_metrics = {
        "assigned": assigned,
        "eligible_adjudicated": len(eligible_adjudicated),
        "confusion": {
            "unsafe_acceptance": ratio(
                unsafe, len(accepted_adjudicated), "no-accepted-adjudicated-candidates"
            ),
            "detection_recall": ratio(
                compat_rejected_incompatible, len(incompatible_pool),
                "no-adjudicated-incompatible-candidates",
            ),
            "false_negative_rate": ratio(
                accepted_incompatible, len(incompatible_pool),
                "no-adjudicated-incompatible-candidates",
            ),
            "false_block_rate": ratio(
                compat_rejected_compatible, len(compatible_pool),
                "no-adjudicated-compatible-candidates",
            ),
        },
        "unknown_rate": ratio(unknown_count, assigned, "no-assigned-candidates"),
        "error_rate": ratio(error_count, assigned, "no-assigned-candidates"),
        "oracle_coverage": ratio(adjudicated, assigned, "no-assigned-candidates"),
        "excluded": {
            "policy_ineligible": {"count": policy_ineligible, "reasons": ineligible_reasons},
            "oracle_unresolved": {"count": oracle_unresolved},
        },
        "accepted_oracle_unresolved": accepted_oracle_unresolved,
    }

    # Task accounting: at most one independently valid delivered update per
    # task/arm/trial record; every attempt's effort is charged.
    assigned_tasks = len(results)
    completed = 0
    delivered_attempts = 0
    delivered_but_not_validated = 0
    delivered_attempt_ids: set[str] = set()
    all_attempts: list[dict] = []
    for result in results:
        by_attempt = {a.get("attempt_id"): a for a in result.get("attempts", [])}
        graded = {o.get("attempt_id"): o for o in result.get("oracle_results", [])}
        delivered = result.get("delivered")
        for att in result.get("attempts", []):
            all_attempts.append(att)
        if isinstance(delivered, dict):
            delivered_attempts += 1
            delivered_attempt_ids.add(delivered.get("attempt_id"))
            att = by_attempt.get(delivered.get("attempt_id"))
            oracle = graded.get(delivered.get("attempt_id")) or {}
            valid = (
                delivered.get("independently_valid") is True
                and oracle.get("verdict") == "compatible"
                and oracle.get("eligibility", {}).get("eligible") is True
            )
            if valid:
                completed += 1
            else:
                delivered_but_not_validated += 1

    effort = {f: effort_field(all_attempts, f) for f in COST_FIELDS}
    failed_attempts = [a for a in all_attempts if a.get("attempt_id") not in delivered_attempt_ids]
    effort_failed = {f: effort_field(failed_attempts, f) for f in COST_FIELDS}
    total_minutes = effort["human_minutes"]["measured"]
    if completed > 0:
        cost_per_valid_update = ratio(total_minutes, completed, "zero-deliveries")
    else:
        cost_per_valid_update = {
            "num": 0, "den": 0, "value": None, "reason": "zero-deliveries",
            "total_failed_effort_human_minutes": effort_failed["human_minutes"]["measured"],
        }

    task_metrics = {
        "assigned_tasks": assigned_tasks,
        "completed": completed,
        "completion_rate": ratio(completed, assigned_tasks, "no-assigned-tasks"),
        "delivered_attempts": delivered_attempts,
        "delivered_but_not_validated": delivered_but_not_validated,
        "attempts_total": len(all_attempts),
        "effort": effort,
        "effort_failed_attempts": effort_failed,
        "cost_per_valid_update": cost_per_valid_update,
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "record_type": "summary",
        "protocol_id": proto.get("protocol_id"),
        "mode": proto.get("mode"),
        "candidate_metrics": candidate_metrics,
        "task_metrics": task_metrics,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def cmd_validate(args: argparse.Namespace) -> int:
    errors = RecordErrors()
    runs_dir = Path(args.runs) if args.runs else None
    load_and_validate(Path(args.protocol), runs_dir, errors)
    if errors.ok:
        print("valid")
        return 0
    print(f"invalid ({len(errors.items)} error(s)):", file=sys.stderr)
    print(errors.report(), file=sys.stderr)
    return 1


def cmd_summarize(args: argparse.Namespace) -> int:
    errors = RecordErrors()
    proto, results = load_and_validate(Path(args.protocol), Path(args.runs), errors)
    if not errors.ok:
        print(f"refusing to summarize invalid records ({len(errors.items)} error(s)):", file=sys.stderr)
        print(errors.report(), file=sys.stderr)
        return 1
    summary = summarize(proto, results)
    text = json.dumps(summary, indent=2, sort_keys=True)
    if args.output and args.output != "-":
        Path(args.output).write_text(text + "\n")
    else:
        print(text)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    # This slice scaffolds a run: validate the committed protocol and record
    # its commitment. Arm execution arrives with later slices.
    errors = RecordErrors()
    proto, _ = load_and_validate(Path(args.protocol), None, errors)
    if not errors.ok:
        print(f"run refused: invalid protocol ({len(errors.items)} error(s)):", file=sys.stderr)
        print(errors.report(), file=sys.stderr)
        return 1
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)
    commitment = hashlib.sha256(
        json.dumps(proto, sort_keys=True).encode()
    ).hexdigest()
    manifest = {
        "record_type": "run_manifest",
        "schema_version": SCHEMA_VERSION,
        "protocol_id": proto.get("protocol_id"),
        "mode": proto.get("mode"),
        "protocol_digest": f"sha256:{commitment}",
        "status": "scaffolded",
    }
    (out_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(f"scaffolded run in {out_dir} (protocol {proto.get('protocol_id')})")
    return 0


# ---------------------------------------------------------------------------
# Replay: native fixture replay through real Cargo (beads wild-aoq.2)
# ---------------------------------------------------------------------------

KNOWN_OUTCOMES = {
    "resolution-refused-by-range", "resolution-conflict",
    "resolved-and-consumer-tests-passed", "resolved-then-consumer-tests-failed",
    "resolved-then-consumer-build-failed", "resolved-but-selected-target-mismatch",
    "resolved-and-selected-target-matches", "baseline-tests-passed",
    "baseline-tests-failed", "resolved",
}


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cargo_home(tmp: Path) -> Path:
    home = tmp / "cargo-home"
    home.mkdir(parents=True)
    (home / "config.toml").write_text(
        '[registries.wild-fixtures]\nindex = "file://{index}"\n'.replace(
            "{index}", str(tmp / "fixtures" / "registry" / "index")
        ),
        encoding="utf-8",
    )
    return home


def _cargo(cmd: list[str], cwd: Path, home: Path) -> subprocess.CompletedProcess[str]:
    import os
    env = dict(os.environ)
    env["CARGO_HOME"] = str(home)
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, timeout=900)


def _lock_dept_version(workspace: Path) -> str | None:
    lock = workspace / "Cargo.lock"
    if not lock.is_file():
        return None
    current: dict[str, str] = {}
    for line in lock.read_text(encoding="utf-8").splitlines():
        if line.startswith("[[package]]"):
            if current.get("name") == "dept":
                return current.get("version")
            current = {}
        elif line.startswith("name = "):
            current["name"] = line.split("= ", 1)[1].strip().strip('"')
        elif line.startswith("version = "):
            current["version"] = line.split("= ", 1)[1].strip().strip('"')
    return current.get("version") if current.get("name") == "dept" else None


def _pin_dept(workspace: Path, target: str) -> None:
    """Authorized manifest edit: rewrite the dept requirement to the exact
    target. This is fixture-scope authority, never a path replacement."""
    manifest = workspace / "Cargo.toml"
    text = manifest.read_text(encoding="utf-8")
    new = re.sub(r'(dept\s*=\s*)"[^"]*"', lambda m: f'{m.group(1)}"={target}"', text)
    manifest.write_text(new, encoding="utf-8")


def _replay_verify_manifest(fixtures: Path, errors: RecordErrors) -> dict:
    manifest_path = fixtures / "cases.json"
    try:
        manifest = load_json(manifest_path)
    except (OSError, json.JSONDecodeError) as exc:
        errors.add(f"cannot read e5 manifest {manifest_path}: {exc}")
        return {}
    if manifest.get("schema") != "wild-e5-cases-v1":
        errors.add(f"unexpected e5 manifest schema {manifest.get('schema')!r}")
    for artifact in manifest.get("artifacts", []):
        path = fixtures / artifact["path"]
        if not path.is_file():
            errors.add(f"e5 missing artifact: {artifact['path']}")
        elif _sha256_file(path) != artifact["sha256"]:
            errors.add(f"e5 drifted artifact: {artifact['path']}")
    split = manifest.get("split", {})
    ids = [c["id"] for c in manifest.get("cases", [])]
    if len(ids) != len(set(ids)):
        errors.add("e5 manifest has duplicate case ids")
    if set(split.get("development", [])) & set(split.get("evaluation", [])):
        errors.add("e5 development/evaluation split overlaps")
    if set(split.get("development", [])) | set(split.get("evaluation", [])) != set(ids):
        errors.add("e5 split does not cover the full frozen membership")
    return manifest


def _replay_phase(fixtures: Path, case: dict, phase_spec: dict, tmp: Path) -> dict:
    """Replay one phase against real Cargo; classify the observed outcome
    from process exit codes and lockfile content — never from a canned
    success response."""
    consumer = fixtures / case.get("consumer", "consumer-base")
    fixtures_copy = tmp / "fixtures"
    shutil.copytree(fixtures, fixtures_copy,
                    ignore=shutil.ignore_patterns("cases", "consumer-base", "*.json"))
    workspace = tmp / "workspace"
    shutil.copytree(consumer, workspace)
    # Cargo's local-registry source needs one directory holding the sparse
    # index under index/ and the .crate files flat at the root. The committed
    # corpus stores those pieces separately (registry/index/ carries the
    # index; consumer-mirror/ carries the byte-identical flat .crate mirror),
    # so the replay assembles the working copy from them — artifacts stay
    # committed and digest-verified, the merge is temp-scope only.
    index_src = fixtures / "registry" / "index"
    local_reg = fixtures_copy / "local-registry"
    shutil.copytree(index_src, local_reg / "index")
    shutil.copy2(index_src / "config.json", local_reg / "config.json")
    for crate in sorted((fixtures_copy / "consumer-mirror").glob("*.crate")):
        shutil.copy2(crate, local_reg / crate.name)
    (workspace / ".cargo").mkdir(exist_ok=True)
    (workspace / ".cargo" / "config.toml").write_text(
        '[source.crates-io]\nreplace-with = "wild-lr"\n\n'
        f'[source.wild-lr]\nlocal-registry = "{local_reg}"\n', encoding="utf-8")
    home = _cargo_home(tmp)
    target = case["target"]
    phase = phase_spec["phase"]
    evidence: dict = {"requested": phase_spec.get("requested", target),
                      "migration_applied": False, "without_migration": None}

    def classify(update_result, build_result=None, test_result=None) -> str:
        if update_result is not None and update_result.returncode != 0:
            return "resolution-conflict" if phase == "authorized" else "resolved"
        if phase == "no-update":
            selected = _lock_dept_version(workspace) or "none"
            evidence["selected"] = selected
            if selected != evidence["requested"]:
                return "resolved-but-selected-target-mismatch"
            return "resolved-and-selected-target-matches"
        if build_result is not None and build_result.returncode != 0:
            return "resolved-then-consumer-build-failed"
        if test_result is not None and test_result.returncode != 0:
            return "resolved-then-consumer-tests-failed"
        return "resolved-and-consumer-tests-passed"

    if phase == "original-range":
        result = _cargo(["cargo", "update", "--package", "dept", "--precise", target,
                          "--offline"], workspace, home)
        observed = "resolution-refused-by-range" if result.returncode != 0 else "resolved"
    elif phase == "baseline":
        # Baseline is the pre-update state: the committed lockfile pins the
        # original version, so no cargo update may run — updating here would
        # silently turn the baseline into an unauthorized update.
        tests = _cargo(["cargo", "test", "--offline"], workspace, home)
        observed = "baseline-tests-passed" if tests.returncode == 0 else "baseline-tests-failed"
    elif phase == "no-update":
        build = _cargo(["cargo", "build", "--offline"], workspace, home)
        observed = classify(None, build_result=build)
    else:  # authorized
        _pin_dept(workspace, target)
        update = _cargo(["cargo", "update", "--offline"], workspace, home)
        migration_rel = phase_spec.get("migration")
        if update.returncode != 0:
            observed = "resolution-conflict"
        else:
            build = _cargo(["cargo", "build", "--offline"], workspace, home)
            if migration_rel:
                pre = _cargo(["cargo", "test", "--offline"], workspace, home)
                evidence["without_migration"] = classify(
                    None, build_result=build, test_result=pre)
                migration_src = fixtures / migration_rel
                shutil.copy2(migration_src, workspace / phase_spec["migration_target"])
                evidence["migration_applied"] = True
                build = _cargo(["cargo", "build", "--offline"], workspace, home)
            tests = _cargo(["cargo", "test", "--offline"], workspace, home)
            observed = classify(None, build_result=build, test_result=tests)

    evidence["lock_dept_version"] = _lock_dept_version(workspace)
    evidence["combined_output"] = (result.stdout + result.stderr) if phase == "original-range" else (
        (update.stdout + update.stderr) if phase == "authorized" else
        (build.stdout + build.stderr) if phase == "no-update" else
        (tests.stdout + tests.stderr) if phase == "baseline" else "")
    return {"observed_outcome": observed, "evidence": evidence}


def cmd_replay(args: argparse.Namespace) -> int:
    import shutil
    import tempfile

    fixtures = Path(args.fixtures)
    errors = RecordErrors()
    manifest = _replay_verify_manifest(fixtures, errors)
    if not errors.ok:
        print(f"replay refused: invalid fixture corpus ({len(errors.items)} error(s)):", file=sys.stderr)
        print(errors.report(), file=sys.stderr)
        return 1
    cases = {c["id"]: c for c in manifest["cases"]}

    if args.expect_only:
        wanted = [cid for cid in cases
                  if (args.case and cid == args.case)
                  or (args.split and cases[cid].get("consumer") and
                      cases[cid]["id"] in manifest["split"].get(args.split, []))]
        report = {"record_type": "replay_report", "schema_version": SCHEMA_VERSION,
                  "cases": {}}
        invalid = 0
        for cid in wanted:
            case = cases[cid]
            problems: list[str] = []
            if not (fixtures / case.get("consumer", "consumer-base")).is_dir():
                problems.append(f"missing consumer tree {case['consumer']}")
            for spec in case["phases"]:
                if spec["expected_outcome"] not in KNOWN_OUTCOMES:
                    problems.append(f"unknown expected outcome {spec['expected_outcome']}")
                if spec.get("migration") and not (fixtures / spec["migration"]).is_file():
                    problems.append(f"missing migration {spec['migration']}")
            report["cases"][cid] = {"expectation_valid": not problems,
                                     "problems": problems}
            invalid += bool(problems)
        text = json.dumps(report, indent=2, sort_keys=True)
        (print(text) if (args.output or "-") == "-" else Path(args.output).write_text(text + "\n"))
        return 1 if invalid else 0

    if not args.case:
        print("replay requires --case (or --split with --expect-only)", file=sys.stderr)
        return 2
    case = cases.get(args.case)
    if case is None:
        print(f"unknown case {args.case!r}", file=sys.stderr)
        return 2
    phase_spec = next((p for p in case["phases"] if p["phase"] == args.phase), None)
    if phase_spec is None:
        print(f"case {args.case!r} has no phase {args.phase!r}", file=sys.stderr)
        return 2
    with tempfile.TemporaryDirectory(prefix="wild-replay-") as raw:
        tmp = Path(raw)
        outcome = _replay_phase(fixtures, case, phase_spec, tmp)
    record = {
        "record_type": "replay_record",
        "schema_version": SCHEMA_VERSION,
        "case_id": case["id"],
        "phase": args.phase,
        "expected_outcome": phase_spec["expected_outcome"],
        "observed_outcome": outcome["observed_outcome"],
        "match": outcome["observed_outcome"] == phase_spec["expected_outcome"],
        "independent_verdict": case["independent_verdict"],
        "origin": case["origin"],
        "evidence": outcome["evidence"],
    }
    print(json.dumps(record, indent=2, sort_keys=True))
    return 0 if record["match"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="update_eval.py", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="validate committed records")
    p_validate.add_argument("--protocol", required=True)
    p_validate.add_argument("--runs", help="optional directory of task_result records")
    p_validate.set_defaults(func=cmd_validate)

    p_sum = sub.add_parser("summarize", help="summarize run records with exact denominators")
    p_sum.add_argument("--protocol", required=True)
    p_sum.add_argument("--runs", required=True)
    p_sum.add_argument("--output", default="-", help="output path or '-' for stdout")
    p_sum.set_defaults(func=cmd_summarize)

    p_run = sub.add_parser("run", help="scaffold a run directory from a committed protocol")
    p_run.add_argument("--protocol", required=True)
    p_run.add_argument("--output", required=True)
    p_run.set_defaults(func=cmd_run)

    p_replay = sub.add_parser("replay", help="replay e5 fixture cases through real Cargo")
    p_replay.add_argument("--fixtures", required=True)
    p_replay.add_argument("--case")
    p_replay.add_argument("--phase", help="which committed phase to replay")
    p_replay.add_argument("--split", help="with --expect-only: structurally validate a split")
    p_replay.add_argument("--expect-only", action="store_true",
                          help="validate replayable expectations without executing cargo")
    p_replay.add_argument("--output", default="-")
    p_replay.set_defaults(func=cmd_replay)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())