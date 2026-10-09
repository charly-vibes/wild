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

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())