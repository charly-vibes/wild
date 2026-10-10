// Purpose: Integrated delivery validation for an authorized update plan
//   (beads wild-nic.3, change add-consumer-update-workflow).
// Responsibilities: After verified host selection, run the fixed-lock
//   build/test stage (the bundle's committed test suite carries the
//   protected obligations in this first profile), check full closure
//   coverage where uncontracted entries stay visible as Unknown and refuse
//   delivery, enforce the manifest/lock-only scope of a direct update, and
//   produce the durable pinned diff — written and digest-verified under
//   the output directory. Every stage refusal carries the requested and
//   actual identities; wrong targets, failed tests, changed inputs, or
//   failed persistence never claim a delivered update.
// Rationale: The design's state transitions 5-8 separate adjudicated
//   refusals (consumer break, unknown dependency, scope violation) from
//   execution errors (persistence), and make delivery require actual
//   build/test, coverage, and durable output. Contract coverage comes from
//   the plan's committed `contracts` map — the plan is externally pinned,
//   so its contract commitments are caller obligations audited by
//   wild-nic.6.

use crate::cargo_host::{evidence_value, local_registry_of, run_cargo_cmd, tail, write_report, Evaluated, Facts};
use crate::formats::{self, Value};
use crate::update::{confined, diagnostic};
use std::path::Path;

/// The shared identity facts for one evaluation's validation stages.
pub(crate) struct Stage<'a> {
    pub plan: &'a Value,
    pub plan_digest: &'a str,
    pub authority_digest: &'a str,
    pub package: &'a str,
    pub release: &'a str,
    pub facts: &'a Facts,
}

impl<'a> Stage<'a> {
    /// Build a refusal/error report for this stage and persist it. A stage
    /// refusal always carries the requested and actual identities.
    pub fn refusal(
        &self,
        disposition: &str,
        diagnostics: Vec<Value>,
        evidence: Vec<Value>,
        closure: Option<Vec<Value>>,
    ) -> Result<Evaluated, String> {
        let mut report = report_record(
            self.plan_digest,
            self.authority_digest,
            self.package,
            self.release,
            Some(&self.facts.actual_version),
            self.facts.actual_digest.as_deref(),
            self.facts.lock_source.as_deref(),
            disposition,
            diagnostics,
            Value::Null,
            self.plan.get("source_digest").cloned().unwrap_or(Value::Null),
            self.plan.get("lock_version").cloned().unwrap_or(Value::Null),
            evidence,
        );
        if let Some(closure) = closure {
            report = extend(report, vec![("closure", formats::arr(closure))]);
        }
        Ok(Evaluated {
            decision: "refuse",
            report,
            cargo_stderr: None,
        })
    }
}

fn closure_values(closure: &[ClosureEntry]) -> Vec<Value> {
    closure
        .iter()
        .map(|c| {
            formats::obj(vec![
                ("package", formats::s(&c.package)),
                ("version", formats::s(&c.version)),
                ("status", formats::s(c.status)),
                ("assurance", formats::s(c.assurance)),
            ])
        })
        .collect()
}

/// State transitions 5-7: fixed-lock build/test, full closure coverage with
/// uncontracted entries visible, the manifest/lock-only scope check, and
/// the durable pinned diff. Delivery requires every stage to succeed.
#[allow(clippy::too_many_arguments)]
pub(crate) fn validate_and_deliver(
    plan: &Value,
    authority: &Value,
    workspace: &Path,
    output_dir: &Path,
    plan_digest: &str,
    authority_digest: &str,
    package: &str,
    cargo_home: &Path,
    baseline_lock_text: &str,
    facts: Facts,
) -> Result<Evaluated, String> {
    let stage = Stage {
        plan,
        plan_digest,
        authority_digest,
        package,
        release: &plan.str_field("release")?.to_string(),
        facts: &facts,
    };
    let consumer = plan.str_field("consumer")?.to_string();
    let manifest_rel = plan
        .get("edit")
        .ok_or_else(|| "input-mismatch: plan carries no edit".to_string())?
        .str_field("file")?
        .to_string();
    let bundle_root = authority.str_field("bundle_root")?.to_string();

    let evidence = vec![evidence_value(
        "baseline-test",
        "cargo test --offline --locked",
        0,
    )];

    // Fixed-lock build and test in the same frozen environment.
    let mut state = match fixed_lock_checks(workspace, cargo_home, &stage, output_dir, evidence)? {
        Ok(evidence) => evidence,
        Err(refusal) => return Ok(refusal),
    };
    // Full closure coverage: uncontracted entries stay visible as Unknown
    // and refuse delivery in this first profile.
    let lock_text = std::fs::read_to_string(workspace.join("Cargo.lock"))
        .map_err(|e| format!("input-mismatch: resolved lock unreadable: {e}"))?;
    let closure = closure_entries(&lock_text, baseline_lock_text, plan, package, &consumer)?;
    state = match closure_check(&closure, &stage, output_dir, state)? {
        Ok(evidence) => evidence,
        Err(refusal) => return Ok(refusal),
    };
    // A direct update changes only manifest/lock.
    let evidence = match scope_check(&manifest_rel, &bundle_root, workspace, &stage, output_dir, state)? {
        Ok(evidence) => evidence,
        Err(refusal) => return Ok(refusal),
    };
    deliver(
        plan,
        output_dir,
        &stage,
        &manifest_rel,
        &bundle_root,
        baseline_lock_text,
        workspace,
        &closure,
        evidence,
    )
}

/// The bundle's committed test suite carries the protected base obligations
/// in this first profile; a failure is an adjudicated candidate
/// incompatibility.
fn fixed_lock_checks(
    workspace: &Path,
    cargo_home: &Path,
    stage: &Stage<'_>,
    output_dir: &Path,
    mut evidence: Vec<Value>,
) -> Result<Result<Vec<Value>, Evaluated>, String> {
    let build = run_cargo_cmd(workspace, cargo_home, &["build", "--offline", "--locked"], "fixed-lock-build")?;
    let test = run_cargo_cmd(workspace, cargo_home, &["test", "--offline", "--locked"], "fixed-lock-test")?;
    evidence.push(evidence_value("fixed-lock-build", "cargo build --offline --locked", build.status.code().unwrap_or(-1) as i64));
    evidence.push(evidence_value("fixed-lock-test", "cargo test --offline --locked", test.status.code().unwrap_or(-1) as i64));
    let failed = if !build.status.success() {
        Some(("fixed-lock-build", &build))
    } else if !test.status.success() {
        Some(("fixed-lock-test", &test))
    } else {
        None
    };
    if let Some((role, output)) = failed {
        let evaluated = stage.refusal(
            "refused",
            vec![diagnostic(
                "consumer-break",
                "error",
                &format!(
                    "the candidate resolved but failed the required {role} command against the fixed lock: {}",
                    tail(&output.stderr)
                ),
            )],
            evidence,
            None,
        )?;
        write_report(output_dir, &evaluated.report)?;
        return Ok(Err(evaluated));
    }
    Ok(Ok(evidence))
}

/// Full closure coverage: every lock entry is accounted for. Entries with
/// no usable contract stay visible as Unknown — build success never
/// manufactures a contract.
fn closure_check(
    closure: &[ClosureEntry],
    stage: &Stage<'_>,
    output_dir: &Path,
    mut evidence: Vec<Value>,
) -> Result<Result<Vec<Value>, Evaluated>, String> {
    let unknown: Vec<&str> = closure
        .iter()
        .filter(|c| c.assurance == "Unknown")
        .map(|c| c.package.as_str())
        .collect();
    if unknown.is_empty() {
        return Ok(Ok(evidence));
    }
    let evaluated = stage.refusal(
        "refused",
        vec![diagnostic(
            "unknown-dependency",
            "error",
            &format!(
                "the resolved closure contains required entries with no usable contract: {} they remain in closure and coverage as Unknown and refuse delivery in this profile",
                unknown.join(", ")
            ),
        )],
        std::mem::take(&mut evidence),
        Some(closure_values(closure)),
    )?;
    write_report(output_dir, &evaluated.report)?;
    Ok(Err(evaluated))
}

/// A direct update changes only manifest/lock. Everything else that changed
/// in the workspace is a scope violation.
#[allow(clippy::too_many_arguments)]
fn scope_check(
    manifest_rel: &str,
    bundle_root: &str,
    workspace: &Path,
    stage: &Stage<'_>,
    output_dir: &Path,
    evidence: Vec<Value>,
) -> Result<Result<Vec<Value>, Evaluated>, String> {
    let allowed = [manifest_rel, "Cargo.lock"];
    let mirror_rel = local_registry_of(workspace)?;
    let excludes = ["target", ".wild-cargo-home", mirror_rel.as_str()];
    let before_files = scan_changed_files(Path::new(bundle_root), &excludes);
    let after_files = scan_changed_files(workspace, &excludes);
    let before_map: std::collections::HashMap<&str, &str> = before_files
        .iter()
        .map(|(rel, digest)| (rel.as_str(), digest.as_str()))
        .collect();
    let violations: Vec<String> = after_files
        .iter()
        .filter(|(rel, digest)| {
            !allowed.contains(&rel.as_str())
                && before_map.get(rel.as_str()) != Some(&digest.as_str())
        })
        .map(|(rel, _)| rel.clone())
        .collect();
    if violations.is_empty() {
        return Ok(Ok(evidence));
    }
    let evaluated = stage.refusal(
        "refused",
        vec![diagnostic(
            "scope-violation",
            "error",
            &format!(
                "the evaluation changed files outside the allowed manifest/lock scope: {}",
                violations.join(", ")
            ),
        )],
        evidence,
        None,
    )?;
    write_report(output_dir, &evaluated.report)?;
    Ok(Err(evaluated))
}

/// Durable pinned diff: exact post-update manifest and lock contents,
/// re-read and digest-verified after writing. Delivery requires
/// persistence to complete.
#[allow(clippy::too_many_arguments)]
fn deliver(
    plan: &Value,
    output_dir: &Path,
    stage: &Stage<'_>,
    manifest_rel: &str,
    bundle_root: &str,
    baseline_lock_text: &str,
    workspace: &Path,
    closure: &[ClosureEntry],
    evidence: Vec<Value>,
) -> Result<Evaluated, String> {
    let manifest_after = std::fs::read_to_string(workspace.join(manifest_rel))
        .map_err(|e| format!("persistence-failed: manifest unreadable after update: {e}"))?;
    let lock_after = std::fs::read_to_string(workspace.join("Cargo.lock"))
        .map_err(|e| format!("persistence-failed: lock unreadable after update: {e}"))?;
    let diff = vec![
        (
            manifest_rel,
            std::fs::read_to_string(confined(bundle_root, manifest_rel, "precondition")?)
                .map_err(|e| format!("persistence-failed: {e}"))?,
            manifest_after.clone(),
        ),
        ("Cargo.lock", baseline_lock_text.to_string(), lock_after.clone()),
    ]
    .into_iter()
    .map(|(path, before, after)| {
        formats::obj(vec![
            ("path", formats::s(path)),
            (
                "before_digest",
                formats::s(&formats::sha256_digest(before.as_bytes())),
            ),
            (
                "after_digest",
                formats::s(&formats::sha256_digest(after.as_bytes())),
            ),
        ])
    })
    .collect::<Vec<_>>();
    let diff_digest = formats::sha256_digest(
        formats::canonical(&formats::arr(diff.clone())).as_bytes(),
    );
    if let Err(msg) = persist_pinned(output_dir, &manifest_after, &lock_after) {
        // Failed output persistence cannot deliver: record the error cause
        // with zero delivered-update claim.
        let evaluated = stage.refusal(
            "error",
            vec![diagnostic("persistence-failed", "error", &msg)],
            evidence,
            None,
        )?;
        write_report(output_dir, &evaluated.report)?;
        return Ok(evaluated);
    }
    let report = report_record(
        stage.plan_digest,
        stage.authority_digest,
        stage.package,
        stage.release,
        Some(&stage.facts.actual_version),
        stage.facts.actual_digest.as_deref(),
        stage.facts.lock_source.as_deref(),
        "delivered",
        Vec::new(),
        formats::arr(Vec::new()),
        plan.get("source_digest").cloned().unwrap_or(Value::Null),
        plan.get("lock_version").cloned().unwrap_or(Value::Null),
        Vec::new(),
    );
    let report = extend(
        report,
        vec![
            ("scope", formats::s("local")),
            ("resolution", formats::s("host-selected")),
            ("update_class", formats::s("direct")),
            ("closure", formats::arr(closure_values(closure))),
            ("evidence", formats::arr(evidence)),
            ("diff", formats::arr(diff)),
            ("diff_digest", formats::s(&diff_digest)),
        ],
    );
    Ok(Evaluated {
        decision: "accept",
        report,
        cargo_stderr: None,
    })
}

fn persist_pinned(output_dir: &Path, manifest_after: &str, lock_after: &str) -> Result<(), String> {
    let pinned_dir = output_dir.join("pinned");
    write_pinned(&pinned_dir, "Cargo.toml", manifest_after)?;
    write_pinned(&pinned_dir, "Cargo.lock", lock_after)?;
    for (name, content) in [("Cargo.toml", manifest_after), ("Cargo.lock", lock_after)] {
        let path = pinned_dir.join(name);
        let read_back = std::fs::read_to_string(&path)
            .map_err(|e| format!("persistence-failed: pinned {name} cannot be read back: {e}"))?;
        if read_back != content {
            return Err(format!(
                "persistence-failed: pinned {name} does not read back identical"
            ));
        }
    }
    Ok(())
}

/// Insert additional fields into a report record, keeping the original order.
fn extend(report: Value, extra: Vec<(&str, Value)>) -> Value {
    let Value::Obj(mut entries) = report else {
        return report;
    };
    for (key, value) in extra {
        entries.push((key.to_string(), value));
    }
    Value::Obj(entries)
}

fn write_pinned(dir: &Path, name: &str, content: &str) -> Result<(), String> {
    std::fs::create_dir_all(dir)
        .map_err(|e| format!("persistence-failed: cannot create pinned output directory: {e}"))?;
    std::fs::write(dir.join(name), content)
        .map_err(|e| format!("persistence-failed: cannot write pinned {name}: {e}"))
}

pub(crate) struct ClosureEntry {
    pub package: String,
    pub version: String,
    pub status: &'static str,
    pub assurance: &'static str,
}

/// Classify every package entry in the resolved lock against the baseline
/// closure and the plan's committed contracts map.
fn closure_entries(
    lock_text: &str,
    baseline_text: &str,
    plan: &Value,
    package: &str,
    consumer: &str,
) -> Result<Vec<ClosureEntry>, String> {
    let parse_pkgs = |text: &str| -> Result<Vec<(String, String)>, String> {
        let lock: toml::Value =
            toml::from_str(text).map_err(|e| format!("input-mismatch: lock is not valid TOML: {e}"))?;
        Ok(lock
            .get("package")
            .and_then(toml::Value::as_array)
            .map(|pkgs| {
                pkgs.iter()
                    .filter_map(|p| {
                        let name = p.get("name").and_then(toml::Value::as_str)?;
                        let version = p.get("version").and_then(toml::Value::as_str)?;
                        Some((name.to_string(), version.to_string()))
                    })
                    .collect()
            })
            .unwrap_or_default())
    };
    let baseline = parse_pkgs(baseline_text)?;
    let contracts = plan
        .get("contracts")
        .and_then(Value::as_obj)
        .map(|entries| entries.to_vec())
        .unwrap_or_default();
    let mut entries = Vec::new();
    for (name, version) in parse_pkgs(lock_text)? {
        let (status, assurance) = if name == consumer {
            ("root", "Contract")
        } else if name == package {
            ("target", "Contract")
        } else if baseline.iter().any(|(n, v)| n == &name && v == &version) {
            ("unchanged", "Contract")
        } else if contracts.iter().any(|(n, _)| n == &name) {
            ("changed", "Contract")
        } else {
            ("new", "Unknown")
        };
        entries.push(ClosureEntry {
            package: name,
            version,
            status,
            assurance,
        });
    }
    Ok(entries)
}

/// Relative-path -> digest scan of a directory tree, skipping whole
/// subtrees named in `exclude` and anything unreadable.
fn scan_changed_files(root: &Path, exclude: &[&str]) -> Vec<(String, String)> {
    let mut out = Vec::new();
    walk(root, root, exclude, &mut out);
    out.sort();
    out
}

fn walk(root: &Path, dir: &Path, exclude: &[&str], out: &mut Vec<(String, String)>) {
    let Ok(entries) = std::fs::read_dir(dir) else {
        return;
    };
    for entry in entries.flatten() {
        let path = entry.path();
        let name = entry.file_name().to_string_lossy().to_string();
        if exclude.contains(&name.as_str()) {
            continue;
        }
        if path.is_dir() {
            walk(root, &path, exclude, out);
        } else if let Ok(bytes) = std::fs::read(&path) {
            let rel = path
                .strip_prefix(root)
                .unwrap_or(&path)
                .to_string_lossy()
                .replace('\\', "/");
            out.push((rel, formats::sha256_digest(&bytes)));
        }
    }
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn report_record(
    plan_digest: &str,
    authority_digest: &str,
    package: &str,
    release: &str,
    actual_version: Option<&str>,
    actual_digest: Option<&str>,
    lock_source: Option<&str>,
    disposition: &str,
    diagnostics: Vec<Value>,
    pending_checks: Value,
    requested_digest: Value,
    lock_version: Value,
    extra: Vec<Value>,
) -> Value {
    let report = formats::obj(vec![
        ("version", formats::s("local-1")),
        ("kind", formats::s("update-report")),
        ("package", formats::s(package)),
        ("release", formats::s(release)),
        ("plan_digest", formats::s(plan_digest)),
        ("authority_digest", formats::s(authority_digest)),
        (
            "requested",
            formats::obj(vec![
                ("release", formats::s(release)),
                ("source_digest", requested_digest),
            ]),
        ),
        (
            "actual",
            formats::obj(vec![
                (
                    "version",
                    actual_version.map(formats::s).unwrap_or(Value::Null),
                ),
                (
                    "source_digest",
                    actual_digest.map(formats::s).unwrap_or(Value::Null),
                ),
                (
                    "lock_source",
                    lock_source.map(formats::s).unwrap_or(Value::Null),
                ),
            ]),
        ),
        ("disposition", formats::s(disposition)),
        ("assurance", formats::s("Unknown")),
        ("pending_checks", pending_checks),
        ("lock_version", lock_version),
        ("diagnostics", formats::arr(diagnostics)),
    ]);
    let mut entries = Vec::new();
    if let Value::Obj(base) = report {
        entries = base;
    }
    if !extra.is_empty() {
        entries.push(("evidence".to_string(), formats::arr(extra)));
    }
    Value::Obj(entries)
}

