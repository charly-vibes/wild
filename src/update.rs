// Purpose: Read-only update planning for the consumer update workflow
//   (beads wild-nic.1, change add-consumer-update-workflow).
// Responsibilities: Parse a local-1 `update-request` record, verify the
//   committed base-file digests of the named manifest and its adjacent
//   Cargo.lock, locate the single dependency declaration for the requested
//   package id, refuse ambiguous identities, inherited workspace ranges,
//   unsupported manifest layouts, and unsupported lock versions with
//   diagnostics instead of guessing, unsupported lock versions with
//   diagnostics instead of guessing, and produce a local-1 `update-plan`
//   record that names the original range, the exact proposed manifest edit
//   (pinning `=<release>`), the base-file digest preconditions, the allowed
//   changed paths, and the full pending-check set — with Unknown assurance
//   and never a delivered-update or checked-compatibility claim. A supplied
//   migration patch (beads wild-nic.4) is validated against its committed
//   source files and bound by the request's migration digest, echoed into
//   the plan, and added to the allowed changed paths; the plan still claims
//   nothing about compatibility.
// Rationale: The design's state transitions 1-2 require planning to read
//   only supplied inputs, write only the requested plan, and never execute
//   project or candidate code: planning success is a well-formed eligible
//   proposal, not an accepted compatibility check. Base commitments are
//   verified so a stale request cannot plan against drifted bytes; a
//   dependency alias is provenance, not an artifact identity, so the edit
//   targets the declared package name only.

use crate::formats::{self, Value};
use toml::Value as Toml;

/// Dependency tables inspected, in declaration order.
const DEP_TABLES: [&str; 3] = ["dependencies", "dev-dependencies", "build-dependencies"];

/// Cargo.lock versions this adapter understands.
const SUPPORTED_LOCK_VERSIONS: [&str; 2] = ["3", "4"];

pub struct PlanOutcome {
    pub plan: Value,
}

struct Found {
    table: &'static str,
    range: String,
}

/// Plan the exact manifest change for the requested package target.
pub fn plan(request: &Value) -> Result<PlanOutcome, String> {
    let bundle_root = request.str_field("bundle_root")?;
    let files = request
        .get("files")
        .and_then(Value::as_obj)
        .ok_or_else(|| "input-mismatch: missing `files` digest map".to_string())?;
    let manifest_rel = request.str_field("manifest")?;
    let package = request.str_field("package")?;
    let release = request.str_field("release")?;
    request.str_field("source_digest")?;

    let manifest_path = confined(bundle_root, manifest_rel, "manifest")?;
    let manifest_bytes = std::fs::read(&manifest_path)
        .map_err(|e| format!("input-mismatch: manifest unreadable: {e}"))?;
    verify_commitment(files, manifest_rel, &manifest_bytes)?;
    let lock_rel = lock_path_of(manifest_rel)?;
    let lock_path = confined(bundle_root, &lock_rel, "lockfile")?;
    let lock_bytes = std::fs::read(&lock_path)
        .map_err(|e| format!("input-mismatch: lockfile unreadable: {e}"))?;
    verify_commitment(files, &lock_rel, &lock_bytes)?;

    let manifest: Toml = toml::from_str(
        std::str::from_utf8(&manifest_bytes)
            .map_err(|e| format!("input-mismatch: manifest is not UTF-8: {e}"))?,
    )
    .map_err(|e| format!("unsupported-manifest: manifest is not valid TOML: {e}"))?;

    let found = locate(&manifest, package)?;
    let lock_version = lock_version(&lock_bytes)?;

    let excluded = excluded_by_original_range(&found.range, release);
    let pinned = format!("={release}");
    let migration = supplied_migration(request, files, bundle_root, manifest_rel, lock_rel.as_str())?;
    let mut allowed_changed = vec![manifest_rel.to_string(), lock_rel.clone()];
    if let Some(Value::Obj(entries)) = migration.get("patch") {
        for (target, _) in entries {
            allowed_changed.push(target.clone());
        }
    }
    let preconditions = vec![
        (manifest_rel, commitment_of(files, manifest_rel)),
        (lock_rel.as_str(), commitment_of(files, &lock_rel)),
    ];
    let diagnostics = vec![diagnostic(
        "plan-ready",
        "info",
        &format!(
            "plan-ready: exact pin {package}@{pinned} recorded; validation remains pending"
        ),
    )];
    let plan = formats::obj(vec![
        ("version", formats::s("local-1")),
        ("kind", formats::s("update-plan")),
        ("consumer", request.get("consumer").cloned().unwrap_or(Value::Null)),
        ("package", formats::s(package)),
        ("release", formats::s(release)),
        ("request_digest", formats::s(&formats::sha256_digest(formats::canonical(request).as_bytes()))),
        ("original_range", formats::s(found.range.as_str())),
        (
            "edit",
            formats::obj(vec![
                ("file", formats::s(&manifest_rel)),
                ("table", formats::s(found.table)),
                ("package", formats::s(package)),
                ("from", formats::s(found.range.as_str())),
                ("to", formats::s(pinned.as_str())),
            ]),
        ),
        (
            "why",
            formats::s(&if excluded {
                format!(
                    "requested release {release} is outside the original range `{}`; the pin narrows the declared constraint to the exact release",
                    found.range
                )
            } else {
                format!(
                    "requested release {release} is pinned exactly; the declared constraint narrows to `={release}`"
                )
            }),
        ),
        ("excluded_by_original_range", Value::Bool(excluded)),
        (
            "source_digest",
            request.get("source_digest").cloned().unwrap_or(Value::Null),
        ),
        ("lock_version", formats::s(&lock_version)),
        ("preconditions", formats::obj(preconditions)),
        (
            "contracts",
            request.get("contracts").cloned().unwrap_or(Value::Null),
        ),
        (
            "allowed_changed_paths",
            formats::arr(allowed_changed.iter().map(|p| formats::s(p)).collect()),
        ),
        (
            "migration",
            migration,
        ),
        (
            "pending_checks",
            formats::arr(
                [
                    "baseline-build",
                    "baseline-test",
                    "cargo-resolution",
                    "closure-inspection",
                    "contract-checks",
                    "protected-obligations",
                ]
                .iter()
                .map(|c| formats::s(c))
                .collect(),
            ),
        ),
        ("assurance", formats::s("Unknown")),
        ("disposition", formats::s("plan-ready")),
        ("diagnostics", formats::arr(diagnostics)),
    ]);
    Ok(PlanOutcome { plan })
}

/// Validate the optional supplied migration patch (beads wild-nic.4).
/// A migration is a caller-committed map of bundle-relative target paths to
/// source paths (or null for a deletion); its `migration_digest` must bind
/// the canonical {target: source-digest | null} map. Every source and
/// target must be digest-committed in the request, confined to the bundle,
/// and distinct from the manifest/lock files the edit owns. The plan echoes
/// the binding; it claims nothing about the migration's outcome.
fn supplied_migration(
    request: &Value,
    files: &[(String, Value)],
    bundle_root: &str,
    manifest_rel: &str,
    lock_rel: &str,
) -> Result<Value, String> {
    let patch = match request.get("migration_patch") {
        None | Some(Value::Null) => {
            if let Some(Value::Str(_)) = request.get("migration_digest") {
                return Err(
                    "input-mismatch: request carries a migration digest but no migration patch"
                        .to_string(),
                );
            }
            return Ok(Value::Null);
        }
        Some(patch @ Value::Obj(_)) => patch,
        Some(_) => {
            return Err(
                "input-mismatch: migration_patch must be a map of target paths to source paths or null"
                    .to_string(),
            )
        }
    };
    let files_entries = files;
    let mut bound: Vec<(String, Value)> = Vec::new();
    let Value::Obj(entries) = patch else {
        return Ok(Value::Null);
    };
    for (target, source) in entries {
        if target.as_str() == manifest_rel || target.as_str() == lock_rel {
            return Err(format!(
                "input-mismatch: migration target `{target}` is owned by the proposed manifest edit"
            ));
        }
        let target_path = confined(bundle_root, target, "migration target")?;
        let target_bytes = std::fs::read(&target_path)
            .map_err(|e| format!("input-mismatch: migration target `{target}` unreadable: {e}"))?;
        verify_commitment(files_entries, target, &target_bytes)?;
        let source_digest = match source {
            Value::Null => {
                bound.push((target.clone(), Value::Null));
                continue;
            }
            Value::Str(rel) => {
                let source_path = confined(bundle_root, rel, "migration source")?;
                let bytes = std::fs::read(&source_path).map_err(|e| {
                    format!("input-mismatch: migration source `{rel}` unreadable: {e}")
                })?;
                verify_commitment(files_entries, rel, &bytes)?;
                let digest = formats::sha256_digest(&bytes);
                bound.push((target.clone(), formats::s(&digest)));
                digest
            }
            _ => {
                return Err(format!(
                    "input-mismatch: migration target `{target}` must name a source path or null"
                ))
            }
        };
        let _ = source_digest;
    }
    let digest = formats::sha256_digest(formats::canonical(&Value::Obj(bound)).as_bytes());
    match request.get("migration_digest") {
        Some(Value::Str(expected)) if *expected == digest => {}
        Some(Value::Str(expected)) => {
            return Err(format!(
                "input-mismatch: supplied migration digest does not bind the committed patch contents (expected {expected}, computed {digest})"
            ));
        }
        _ => {
            return Err(
                "input-mismatch: request carries a migration patch but no migration digest"
                    .to_string(),
            )
        }
    }
    Ok(formats::obj(vec![
        ("digest", formats::s(&digest)),
        ("patch", patch.clone()),
    ]))
}

/// Refuse rather than guess: exactly one dependency declaration must name
/// the package in a supported table with a version range of its own.
fn locate(manifest: &Toml, package: &str) -> Result<Found, String> {
    let mut hits: Vec<(&'static str, String)> = Vec::new();
    for table in DEP_TABLES {
        let Some(spec) = manifest
            .get(table)
            .and_then(|t| t.get(package))
        else {
            continue;
        };
        match spec {
            Toml::String(version) => hits.push((table, version.clone())),
            Toml::Table(t) => {
                if t.get("workspace").and_then(Toml::as_bool) == Some(true) {
                    return Err(format!(
                        "inherited-range: `{package}` in [{table}] inherits its range from the workspace; no identified owner is available to edit"
                    ));
                }
                if let Some(v) = t.get("version").and_then(Toml::as_str) {
                    hits.push((table, v.to_string()));
                } else {
                    return Err(format!(
                        "unsupported-manifest: `{package}` in [{table}] declares no version range (path/git/provenance-only specs are outside this adapter)"
                    ));
                }
            }
            _ => {
                return Err(format!(
                    "unsupported-manifest: `{package}` in [{table}] has an unsupported spec type"
                ))
            }
        }
    }
    match hits.len() {
        0 => Err(format!(
            "unknown-package: `{package}` is not declared in any supported dependency table of the named manifest"
        )),
        1 => {
            let (table, range) = hits.remove(0);
            Ok(Found { table, range })
        }
        _ => Err(format!(
            "ambiguous-package: `{package}` is declared in {} dependency tables; which declaration to rewrite cannot be guessed",
            hits.len()
        )),
    }
}

fn lock_version(lock_bytes: &[u8]) -> Result<String, String> {
    let text = std::str::from_utf8(lock_bytes)
        .map_err(|e| format!("input-mismatch: lockfile is not UTF-8: {e}"))?;
    let lock: Toml = toml::from_str(text)
        .map_err(|e| format!("unsupported-lock: lockfile is not valid TOML: {e}"))?;
    match lock.get("version") {
        Some(Toml::Integer(v)) if SUPPORTED_LOCK_VERSIONS.contains(&v.to_string().as_str()) => {
            Ok(v.to_string())
        }
        Some(Toml::String(v)) if SUPPORTED_LOCK_VERSIONS.contains(&v.as_str()) => Ok(v.clone()),
        _ => Err(
            "unsupported-lock: Cargo.lock version is missing or outside the supported set {3, 4}"
                .to_string(),
        ),
    }
}

/// Conservative caret-style check: a bare or `^`-prefixed range pins its
/// leading major; a release on a different major is outside the range.
fn excluded_by_original_range(range: &str, release: &str) -> bool {
    let major = |text: &str| -> Option<u64> {
        let stripped = text.trim_start_matches(['^', 'v', '=']);
        let digits: String = stripped.chars().take_while(|c| c.is_ascii_digit()).collect();
        digits.parse().ok()
    };
    match (major(range), major(release)) {
        (Some(r), Some(x)) => r != x,
        _ => false,
    }
}

fn lock_path_of(manifest_rel: &str) -> Result<String, String> {
    let parent = std::path::Path::new(manifest_rel)
        .parent()
        .ok_or_else(|| "input-mismatch: manifest path has no parent".to_string())?;
    let joined = parent.join("Cargo.lock");
    let text = joined.to_string_lossy().replace('\\', "/");
    Ok(text)
}

/// Refuse paths that escape the bundle (absolute, dot, dot-dot components).
pub(crate) fn confined(bundle_root: &str, rel: &str, what: &str) -> Result<std::path::PathBuf, String> {
    if rel.starts_with('/') || rel.contains('\\') {
        return Err(format!("input-mismatch: {what} path `{rel}` must be bundle-relative"));
    }
    let mut cleaned = std::path::PathBuf::from(bundle_root);
    for part in rel.split('/') {
        if part == "." || part == ".." || part.is_empty() {
            return Err(format!("input-mismatch: {what} path `{rel}` escapes the bundle"));
        }
        cleaned.push(part);
    }
    Ok(cleaned)
}

fn commitment_of(files: &[(String, Value)], rel: &str) -> Value {
    files
        .iter()
        .find(|(k, _)| k == rel)
        .map(|(_, v)| v.clone())
        .unwrap_or(Value::Null)
}

fn verify_commitment(
    files: &[(String, Value)],
    rel: &str,
    bytes: &[u8],
) -> Result<(), String> {
    let Some(Value::Str(expected)) = files.iter().find(|(k, _)| k == rel).map(|(_, v)| v) else {
        return Err(format!(
            "input-mismatch: `{rel}` has no committed digest in the request"
        ));
    };
    let actual = formats::sha256_digest(bytes);
    if *expected != actual {
        return Err(format!(
            "base-changed: base commitment mismatch for `{rel}`: the request no longer describes the supplied bytes"
        ));
    }
    Ok(())
}

pub(crate) fn diagnostic(code: &str, severity: &str, reason: &str) -> Value {
    formats::obj(vec![
        ("code", formats::s(code)),
        ("severity", formats::s(severity)),
        ("source", Value::Null),
        ("slots", formats::arr(Vec::new())),
        ("reason", formats::s(reason)),
    ])
}
