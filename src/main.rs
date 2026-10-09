// Purpose: `wild` executable entrypoint (beads wild-mh5.1).
// Responsibilities: Parse the `extract --request <file> --output <dir>`
//   command line, load and validate the local-1 extraction request through
//   wild::formats / wild::extract, write the requested record artifacts
//   (contract.json, demand.json, provenance.json, report.json) only to the
//   requested output directory, print the v1 envelope on stdout, and map
//   outcomes to exits per the design: accept 0, refuse 1, error 2.
// Rationale: The design requires every command to emit a v1 envelope, to
//   refuse with exit 1 for unknown/reject and exit 2 for malformed input or
//   failed orchestration, and to never write outside the requested output
//   locations or perform network access.

use wild::extract::{self, PROFILE};
use wild::formats::{self, Value};

fn envelope(decision: &str, assurance: &str, diagnostics: Vec<Value>, slots: Vec<String>, checker: Value) -> Value {
    formats::obj(vec![
        ("schema_version", formats::s("1")),
        ("kind", formats::s("envelope")),
        ("command", formats::s("extract")),
        ("assurance", formats::s(assurance)),
        ("decision", formats::s(decision)),
        ("tier_reports", formats::arr(Vec::new())),
        ("slots", formats::arr(slots.into_iter().map(|s| formats::s(&s)).collect())),
        (
            "coverage",
            formats::obj(vec![
                ("numerator", formats::i(0)),
                ("denominator", formats::i(0)),
                ("ratio_ppm", Value::Null),
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

fn run() -> i32 {
    let args: Vec<String> = std::env::args().collect();
    let usage = "usage: wild extract --request <file> --output <dir>";
    if args.len() != 6 || args[1] != "extract" || args[2] != "--request" || args[4] != "--output" {
        eprintln!("{usage}");
        let envelope = envelope(
            "refuse",
            "Unknown",
            vec![diagnostic("input-mismatch", usage.to_string())],
            Vec::new(),
            Value::Null,
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
                decision,
                assurance,
                outcome.diagnostics.clone(),
                outcome.slot_names.clone(),
                checker.clone(),
            );
            let report = report_record(outcome.complete_inventory, outcome.diagnostics.clone());
            (code, envelope_value, report)
        }
        Err(msg) => {
            let diagnostics = vec![diagnostic("input-mismatch", msg.clone())];
            let envelope_value =
                envelope("refuse", "Unknown", diagnostics.clone(), Vec::new(), Value::Null);
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

fn main() {
    std::process::exit(run());
}
