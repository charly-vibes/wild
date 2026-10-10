// Purpose: `wild` executable entrypoint (beads wild-mh5.1, wild-mh5.2, wild-nic.1).
// Responsibilities: Parse the `extract --request <file> --output <dir>`,
//   `check --request <file> --format json --report <file>` and
//   `update plan --request <file> --output <file>` command lines,
//   load and validate the local-1 requests through wild::formats /
//   wild::extract / wild::check, write the requested record artifacts only
//   to the requested output locations (extraction: contract/demand/
//   provenance/report records under --output; check: the check-report at
//   --report plus extracted base/candidate fact records under its parent's
//   facts/ subdirectories), print the v1 envelope on stdout, and map
//   outcomes to exits per the design: accept 0, refuse 1, error 2.
// Rationale: The design requires every command to emit a v1 envelope, to
//   refuse with exit 1 for unknown/reject and exit 2 for malformed input or
//   failed orchestration, and to never write outside the requested output
//   locations or perform network access. The check command's facts layout
//   is part of the declared report contract (docs/wild-local-v1.md), so the
//   fact records are explicitly requested outputs. The update plan command
//   is strictly read-only toward the project bundle: it writes only the
//   requested plan file and never executes project or candidate code
//   (beads wild-nic.1, state transitions 1-2 of the change design).

use wild::check;
use wild::extract::{self, PROFILE};
use wild::formats::{self, Value};
use wild::update;

fn envelope(command: &str, decision: &str, assurance: &str, diagnostics: Vec<Value>, slots: Vec<String>, checker: Value, coverage: (i64, i64)) -> Value {
    let (numerator, denominator) = coverage;
    let ratio_ppm = if denominator > 0 {
        Value::Int(numerator * 1_000_000 / denominator)
    } else {
        Value::Null
    };
    formats::obj(vec![
        ("schema_version", formats::s("1")),
        ("kind", formats::s("envelope")),
        ("command", formats::s(command)),
        ("assurance", formats::s(assurance)),
        ("decision", formats::s(decision)),
        ("tier_reports", formats::arr(Vec::new())),
        ("slots", formats::arr(slots.into_iter().map(|s| formats::s(&s)).collect())),
        (
            "coverage",
            formats::obj(vec![
                ("numerator", formats::i(numerator)),
                ("denominator", formats::i(denominator)),
                ("ratio_ppm", ratio_ppm),
            ]),
        ),
        ("checker", checker),
        ("known_consumers", formats::arr(Vec::new())),
        ("undeclared_consumers_covered", Value::Bool(false)),
        ("deployment", Value::Null),
        ("diagnostics", formats::arr(diagnostics)),
    ])
}

fn diagnostic(code: &'static str, reason: String) -> Value {
    formats::obj(vec![
        ("code", formats::s(code)),
        ("severity", formats::s("error")),
        ("source", Value::Null),
        ("slots", formats::arr(Vec::new())),
        ("reason", formats::s(&reason)),
    ])
}

fn report_record(complete: bool, diagnostics: Vec<Value>) -> Value {
    formats::obj(vec![
        ("version", formats::s("local-1")),
        ("kind", formats::s("extraction-report")),
        ("profile", formats::s(PROFILE)),
        ("complete_inventory", Value::Bool(complete)),
        ("diagnostics", formats::arr(diagnostics)),
    ])
}

fn write_outputs(output_dir: &std::path::Path, files: &[(&str, String)]) -> Result<(), String> {
    std::fs::create_dir_all(output_dir)
        .map_err(|e| format!("cannot create output directory: {e}"))?;
    for (name, content) in files {
        let path = output_dir.join(name);
        std::fs::write(&path, content)
            .map_err(|e| format!("cannot write requested output `{}`: {e}", path.display()))?;
    }
    Ok(())
}

fn run_extract(args: &[String]) -> i32 {
    let usage = "usage: wild extract --request <file> --output <dir>";
    if args.len() != 6 || args[2] != "--request" || args[4] != "--output" {
        eprintln!("{usage}");
        let envelope = envelope(
            "extract",
            "refuse",
            "Unknown",
            vec![diagnostic("input-mismatch", usage.to_string())],
            Vec::new(),
            Value::Null,
            (0, 0),
        );
        println!("{}", formats::canonical(&envelope));
        return 2;
    }
    let request_path = std::path::PathBuf::from(&args[3]);
    let output_dir = std::path::PathBuf::from(&args[5]);

    let outcome: Result<(extract::ExtractionOutcome, Value), String> = (|| {
        let text = std::fs::read_to_string(&request_path)
            .map_err(|e| format!("input-mismatch: request unreadable: {e}"))?;
        let request = formats::parse(&text)
            .map_err(|e| format!("input-mismatch: malformed request: {e}"))?;
        // v1 envelopes require a checker digest: bind it to the committed
        // extractor identity; an unparseable request cannot supply one
        let checker = request
            .get("extractor")
            .and_then(|e| e.str_field("digest").ok())
            .map(formats::s)
            .unwrap_or_else(|| formats::s(&formats::sha256_digest(b"wild-extractor-unknown")));
        extract::extract(&request).map(|outcome| (outcome, checker))
    })();

    let (exit_code, envelope_value, report) = match &outcome {
        Ok((outcome, checker)) => {
            let (decision, assurance) =
                if outcome.complete_inventory && outcome.diagnostics.is_empty() {
                    ("accept", "PassDeclared")
                } else {
                    ("refuse", "Unknown")
                };
            let code = if decision == "accept" { 0 } else { 1 };
            let envelope_value = envelope(
                "extract",
                decision,
                assurance,
                outcome.diagnostics.clone(),
                outcome.slot_names.clone(),
                checker.clone(),
                (0, 0),
            );
            let report = report_record(outcome.complete_inventory, outcome.diagnostics.clone());
            (code, envelope_value, report)
        }
        Err(msg) => {
            let diagnostics = vec![diagnostic("input-mismatch", msg.clone())];
            let envelope_value = envelope(
                "extract",
                "refuse",
                "Unknown",
                diagnostics.clone(),
                Vec::new(),
                Value::Null,
                (0, 0),
            );
            let report = report_record(false, diagnostics);
            (2, envelope_value, report)
        }
    };

    let mut files: Vec<(&str, String)> = Vec::new();
    if let Ok((outcome, _checker)) = &outcome {
        files.push(("contract.json", formats::canonical(&outcome.contract)));
        files.push(("demand.json", formats::canonical(&outcome.demand)));
        files.push(("provenance.json", formats::canonical(&outcome.provenance)));
    }
    files.push(("report.json", formats::canonical(&report)));
    if let Err(msg) = write_outputs(&output_dir, &files) {
        eprintln!("error: {msg}");
        return 2;
    }
    println!("{}", formats::canonical(&envelope_value));
    exit_code
}

fn run_check(args: &[String]) -> i32 {
    let usage = "usage: wild check --request <file> --format json --report <file>";
    if args.len() != 8
        || args[2] != "--request"
        || args[4] != "--format"
        || args[5] != "json"
        || args[6] != "--report"
    {
        eprintln!("{usage}");
        let envelope = envelope(
            "check",
            "refuse",
            "Unknown",
            vec![diagnostic("input-mismatch", usage.to_string())],
            Vec::new(),
            Value::Null,
            (0, 0),
        );
        println!("{}", formats::canonical(&envelope));
        return 2;
    }
    let request_path = std::path::PathBuf::from(&args[3]);
    let report_path = std::path::PathBuf::from(&args[7]);

    let outcome: Result<(check::CheckOutcome, Value), String> = (|| {
        let text = std::fs::read_to_string(&request_path)
            .map_err(|e| format!("input-mismatch: request unreadable: {e}"))?;
        let request = formats::parse(&text)
            .map_err(|e| format!("input-mismatch: malformed request: {e}"))?;
        // v1 envelopes require a checker digest: bind it to the committed
        // checker identity; an unparseable request cannot supply one
        let checker = request
            .get("checker")
            .and_then(|c| c.str_field("digest").ok())
            .map(formats::s)
            .unwrap_or_else(|| formats::s(&formats::sha256_digest(b"wild-checker-unknown")));
        check::check(&request).map(|outcome| (outcome, checker))
    })();

    let (exit_code, envelope_value, report) = match &outcome {
        Ok((outcome, checker)) => {
            let code = if outcome.decision == "accept" { 0 } else { 1 };
            let envelope_value = envelope(
                "check",
                outcome.decision,
                outcome.assurance,
                outcome.diagnostics.clone(),
                outcome.demanded.clone(),
                checker.clone(),
                outcome.coverage,
            );
            (code, envelope_value, outcome.report.clone())
        }
        Err(msg) => {
            let diagnostics = vec![diagnostic("input-mismatch", msg.clone())];
            let envelope_value = envelope(
                "check",
                "refuse",
                "Unknown",
                diagnostics.clone(),
                Vec::new(),
                Value::Null,
                (0, 0),
            );
            let report = check_error_report(diagnostics);
            (2, envelope_value, report)
        }
    };

    // Declared report contract (docs/wild-local-v1.md): the check-report
    // record at the requested path, plus extracted base/candidate fact
    // records under the report location's facts/ subdirectories.
    if let Err(msg) = write_report_outputs(&report_path, &outcome, &report) {
        eprintln!("error: {msg}");
        return 2;
    }
    println!("{}", formats::canonical(&envelope_value));
    exit_code
}

fn check_error_report(diagnostics: Vec<Value>) -> Value {
    formats::obj(vec![
        ("version", formats::s("local-1")),
        ("kind", formats::s("check-report")),
        ("profile", formats::s(PROFILE)),
        ("consumer", formats::s("unknown")),
        ("policy", Value::Null),
        ("law_methods", formats::arr(Vec::new())),
        ("base", Value::Null),
        ("candidate", Value::Null),
        ("demanded_slots", formats::arr(Vec::new())),
        ("decision", formats::s("refuse")),
        ("assurance", formats::s("Unknown")),
        ("diagnostics", formats::arr(diagnostics)),
    ])
}

/// Write the check report artifacts: the check-report record at the
/// requested path and, when checking succeeded, the extracted base and
/// candidate fact records under `<report dir>/facts/{base,candidate}/`.
fn write_report_outputs(
    report_path: &std::path::Path,
    outcome: &Result<(check::CheckOutcome, Value), String>,
    report: &Value,
) -> Result<(), String> {
    let report_dir = report_path
        .parent()
        .ok_or_else(|| "report path has no parent directory".to_string())?;
    std::fs::create_dir_all(report_dir)
        .map_err(|e| format!("cannot create report directory: {e}"))?;
    std::fs::write(report_path, formats::canonical(report))
        .map_err(|e| format!("cannot write requested report `{}`: {e}", report_path.display()))?;
    if let Ok((outcome, _)) = outcome {
        for (rel, content) in &outcome.facts {
            let path = report_dir.join("facts").join(rel);
            if let Some(parent) = path.parent() {
                std::fs::create_dir_all(parent)
                    .map_err(|e| format!("cannot create report subdirectory: {e}"))?;
            }
            std::fs::write(&path, content)
                .map_err(|e| format!("cannot write requested report `{}`: {e}", path.display()))?;
        }
    }
    Ok(())
}

fn run_update(args: &[String]) -> i32 {
    // args: [prog, update, plan, --request, <file>, --output, <file>]
    let usage = "usage: wild update plan --request <file> --output <file>";
    if args.len() != 7 || args[2] != "plan" || args[3] != "--request" || args[5] != "--output" {
        eprintln!("{usage}");
        let envelope_value = envelope(
            "update-plan",
            "refuse",
            "Unknown",
            vec![diagnostic("input-mismatch", usage.to_string())],
            Vec::new(),
            Value::Null,
            (0, 0),
        );
        println!("{}", formats::canonical(&envelope_value));
        return 2;
    }
    let request_path = std::path::PathBuf::from(&args[4]);
    let output_path = std::path::PathBuf::from(&args[6]);

    let outcome: Result<update::PlanOutcome, String> = (|| {
        let text = std::fs::read_to_string(&request_path)
            .map_err(|e| format!("input-mismatch: request unreadable: {e}"))?;
        let request = formats::parse(&text)
            .map_err(|e| format!("input-mismatch: malformed request: {e}"))?;
        update::plan(&request)
    })();

    let (exit_code, envelope_value, plan) = match &outcome {
        Ok(outcome) => (
            0,
            envelope(
                "update-plan",
                "accept",
                "Unknown",
                Vec::new(),
                Vec::new(),
                formats::s(&formats::sha256_digest(b"wild-planner-v0")),
                (0, 0),
            ),
            Some(&outcome.plan),
        ),
        Err(msg) => {
            // Diagnostic kodu mesajın prefixindən çıxarılır (məs. "ambiguous-package: ...").
            let code = msg.split(':').next().unwrap_or("input-mismatch");
            let code_static: &'static str = match code {
                "ambiguous-package"     => "ambiguous-package",
                "inherited-range"       => "inherited-range",
                "unsupported-lock"      => "unsupported-lock",
                "unsupported-manifest"  => "unsupported-manifest",
                "unknown-package"       => "unknown-package",
                "base-changed"          => "base-changed",
                _                        => "input-mismatch",
            };
            let reason = match msg.split_once(": ") {
                Some((_, rest)) => rest.to_string(),
                None => msg.clone(),
            };
            // Malformed/unreadable input = error (exit 2); semantic refusals = exit 1.
            let is_error = code_static == "input-mismatch";
            (
                if is_error { 2 } else { 1 },
                envelope(
                    "update-plan",
                    "refuse",
                    "Unknown",
                    vec![diagnostic(code_static, reason)],
                    Vec::new(),
                    Value::Null,
                    (0, 0),
                ),
                None,
            )
        }
    };

    // Yalnız istənilən plan faylı yazılır — layihəyə heç bir yazı yoxdur.
    if let Some(plan) = plan {
        if let Some(parent) = output_path.parent() {
            if let Err(e) = std::fs::create_dir_all(parent) {
                eprintln!("error: cannot create output directory: {e}");
                return 2;
            }
        }
        if let Err(e) = std::fs::write(&output_path, formats::canonical(plan)) {
            eprintln!("error: cannot write plan `{}`: {e}", output_path.display());
            return 2;
        }
    }
    println!("{}", formats::canonical(&envelope_value));
    exit_code
}

fn run() -> i32 {
    let args: Vec<String> = std::env::args().collect();
    match args.get(1).map(String::as_str) {
        Some("extract") => run_extract(&args),
        Some("check") => run_check(&args),
        Some("update") => run_update(&args),
        _ => {
            let usage = "usage: wild <extract|check|update> ...";
            eprintln!("{usage}");
            let envelope = envelope(
                "unknown",
                "refuse",
                "Unknown",
                vec![diagnostic("input-mismatch", usage.to_string())],
                Vec::new(),
                Value::Null,
                (0, 0),
            );
            println!("{}", formats::canonical(&envelope));
            2
        }
    }
}

fn main() {
    std::process::exit(run());
}
