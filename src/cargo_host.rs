// Purpose: Isolated evaluation of an authorized update plan (beads
//   wild-nic.2, change add-consumer-update-workflow).
// Responsibilities: Verify that an external invocation pin commits the exact
//   authority and plan digests before anything runs (candidate
//   self-authorization fails), re-verify the plan's base preconditions,
//   copy the consumer bundle into a disposable workspace that refuses
//   symlink escapes, apply only the proposed manifest edit, run real
//   `cargo update --offline --precise` against the bundle's own frozen
//   local-registry mirror under a fresh CARGO_HOME, inspect the selected
//   target (version + source artifact digest against the plan) and the
//   catalog's declared rust-version against the authorized toolchain, and
//   produce an `update-report` record carrying evaluated host evidence —
//   requested and actual identities on a wrong-target or environment
//   refusal, never a delivered-update claim.
// Rationale: The design's state transitions 3-5 make evaluation an applied
//   host-resolution check in isolation: trust is anchored in the externally
//   committed pin (the same out-of-band commitment mechanism local checking
//   uses), the host resolver stays authoritative, and this slice stops at
//   host evidence — baseline build/test, contract checks, and protected
//   obligations remain pending until U3 integrates them. Resource limits on
//   the Cargo child and a pinned rustup toolchain are enforced by the U3
//   sandbox slice; this slice already uses a fresh CARGO_HOME, offline mode,
//   a bounded wait, and never passes --ignore-rust-version.

use crate::formats::{self, Value};
use crate::update::{confined, diagnostic};
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

const CHILD_TIMEOUT: Duration = Duration::from_secs(600);

pub struct Evaluated {
    pub decision: &'static str,
    pub report: Value,
    pub cargo_stderr: Option<String>,
}

/// Evaluate an authorized plan in a disposable workspace.
pub fn evaluate(
    plan: &Value,
    authority: &Value,
    pin: &Value,
    output_dir: &Path,
) -> Result<Evaluated, String> {
    check_kind(plan, "update-plan")?;
    check_kind(authority, "update-authority")?;
    check_kind(pin, "update-authority-pin")?;

    let plan_digest = formats::sha256_digest(formats::canonical(plan).as_bytes());
    let authority_digest = formats::sha256_digest(formats::canonical(authority).as_bytes());

    // External authority: the pin commits the exact plan and authority
    // digests and the same invocation identity the authority declares. An
    // authority file supplied by candidate code carries no trusted pin.
    if pin.str_field("plan_digest")? != plan_digest {
        return Err("authority-untrusted: the trusted pin does not commit this plan digest"
            .to_string());
    }
    if pin.str_field("authority_digest")? != authority_digest {
        return Err(
            "authority-untrusted: the trusted pin does not commit this authority record"
                .to_string(),
        );
    }
    let invocation = authority.get("invocation").ok_or_else(|| {
        "authority-untrusted: authority carries no invocation identity".to_string()
    })?;
    if pin.get("invocation") != Some(invocation) {
        return Err(
            "authority-untrusted: pin and authority disagree on the invocation identity"
                .to_string(),
        );
    }
    if authority.str_field("plan_digest")? != plan_digest {
        return Err("authority-untrusted: the authority does not authorize this plan".to_string());
    }
    let allowed = authority
        .get("allowed_actions")
        .and_then(Value::as_arr)
        .ok_or_else(|| "authority-untrusted: authority carries no allowed actions".to_string())?;
    if !allowed.iter().any(|a| a.as_str() == Some("evaluate")) {
        return Err(
            "authority-untrusted: the authority does not authorize the evaluate action"
                .to_string(),
        );
    }

    // Stale base commitments refuse before any edit or project execution.
    let bundle_root = authority.str_field("bundle_root")?.to_string();
    verify_preconditions(plan, &bundle_root)?;

    // Disposable workspace; symlink escapes refuse with zero changes made.
    let workspace = make_workspace(&bundle_root)?;
    let result = resolve_and_inspect(plan, authority, &workspace, output_dir, &plan_digest, &authority_digest);
    // Dispose of the workspace on every path; only requested reports remain.
    let _ = std::fs::remove_dir_all(&workspace);
    result
}

fn check_kind(value: &Value, expected: &str) -> Result<(), String> {
    if value.str_field("version")? != "local-1" || value.str_field("kind")? != expected {
        return Err(format!("input-mismatch: expected a local-1 `{expected}` record"));
    }
    Ok(())
}

fn verify_preconditions(plan: &Value, bundle_root: &str) -> Result<(), String> {
    let preconditions = plan
        .get("preconditions")
        .and_then(Value::as_obj)
        .ok_or_else(|| "input-mismatch: plan carries no preconditions".to_string())?;
    for (rel, expected) in preconditions {
        let path = confined(bundle_root, rel, "precondition")?;
        let bytes = std::fs::read(&path)
            .map_err(|e| format!("input-mismatch: `{rel}` unreadable: {e}"))?;
        let Value::Str(expected) = expected else {
            return Err(format!("input-mismatch: precondition for `{rel}` is not a digest"));
        };
        if *expected != formats::sha256_digest(&bytes) {
            return Err(format!(
                "base-changed: base commitment mismatch for `{rel}`: the plan no longer describes the supplied bytes"
            ));
        }
    }
    Ok(())
}

/// Copy the whole bundle into a temp workspace, refusing symlinks (the
/// original worktree is only ever read).
fn make_workspace(bundle_root: &str) -> Result<PathBuf, String> {
    let nanos = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map_err(|e| format!("isolation-refused: no system clock: {e}"))?
        .as_nanos();
    let workspace = std::env::temp_dir().join(format!("wild-eval-{}-{nanos}", std::process::id()));
    copy_tree(Path::new(bundle_root), &workspace)?;
    Ok(workspace)
}

fn copy_tree(src: &Path, dest: &Path) -> Result<(), String> {
    std::fs::create_dir_all(dest).map_err(|e| {
        format!(
            "isolation-refused: cannot create workspace {}: {e}",
            dest.display()
        )
    })?;
    for entry in std::fs::read_dir(src)
        .map_err(|e| format!("isolation-refused: cannot read {}: {e}", src.display()))?
    {
        let entry = entry.map_err(|e| format!("isolation-refused: {e}"))?;
        let path = entry.path();
        let target = dest.join(entry.file_name());
        let meta =
            std::fs::symlink_metadata(&path).map_err(|e| format!("isolation-refused: {e}"))?;
        if meta.file_type().is_symlink() {
            return Err(format!(
                "isolation-refused: `{}` is a symlink; escapes are refused",
                path.display()
            ));
        }
        if meta.is_dir() {
            copy_tree(&path, &target)?;
        } else {
            std::fs::copy(&path, &target).map_err(|e| {
                format!("isolation-refused: cannot copy `{}`: {e}", path.display())
            })?;
        }
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn resolve_and_inspect(
    plan: &Value,
    authority: &Value,
    workspace: &Path,
    output_dir: &Path,
    plan_digest: &str,
    authority_digest: &str,
) -> Result<Evaluated, String> {
    let package = plan.str_field("package")?.to_string();
    let release = plan.str_field("release")?.to_string();
    let edit = plan
        .get("edit")
        .ok_or_else(|| "input-mismatch: plan carries no edit".to_string())?;

    // Apply only the proposed change, in the workspace copy.
    let manifest_rel = edit.str_field("file")?.to_string();
    let manifest_path = confined(
        workspace.to_string_lossy().as_ref(),
        &manifest_rel,
        "manifest",
    )?;
    let text = std::fs::read_to_string(&manifest_path)
        .map_err(|e| format!("input-mismatch: manifest unreadable: {e}"))?;
    let edited = apply_edit(
        &text,
        edit.str_field("table")?,
        edit.str_field("package")?,
        edit.str_field("from")?,
        edit.str_field("to")?,
    )?;
    std::fs::write(&manifest_path, &edited)
        .map_err(|e| format!("isolation-refused: cannot write workspace manifest: {e}"))?;

    // Real offline resolution with a fresh isolated Cargo home.
    let cargo_home = workspace.join(".wild-cargo-home");
    let output = run_cargo(workspace, &cargo_home, &package, &release)?;
    if !output.status.success() {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let report = report_record(
            plan_digest,
            authority_digest,
            &package,
            &release,
            None,
            None,
            None,
            "refused",
            vec![diagnostic(
                "host-resolution-failed",
                "error",
                &format!(
                    "cargo update --offline --precise {release} failed: {}",
                    stderr.lines().last().unwrap_or_default()
                ),
            )],
            plan.get("pending_checks").cloned().unwrap_or(Value::Null),
            plan.get("source_digest").cloned().unwrap_or(Value::Null),
            plan.get("lock_version").cloned().unwrap_or(Value::Null),
        );
        let _ = std::fs::create_dir_all(output_dir);
        let _ = std::fs::write(output_dir.join("cargo-stderr.log"), &stderr);
        return Ok(Evaluated {
            decision: "refuse",
            report,
            cargo_stderr: Some(stderr),
        });
    }

    inspect_resolution(
        plan, authority, workspace, plan_digest, authority_digest, &package, &release,
    )
}

/// Inspect the actual selected target in the resolved lock and the frozen
/// mirror, then classify the outcome as host evidence or a refusal.
fn inspect_resolution(
    plan: &Value,
    authority: &Value,
    workspace: &Path,
    plan_digest: &str,
    authority_digest: &str,
    package: &str,
    release: &str,
) -> Result<Evaluated, String> {
    let lock_text = std::fs::read_to_string(workspace.join("Cargo.lock"))
        .map_err(|e| format!("input-mismatch: resolved lock unreadable: {e}"))?;
    let lock: toml::Value = toml::from_str(&lock_text)
        .map_err(|e| format!("input-mismatch: resolved lock is not valid TOML: {e}"))?;
    let entry = lock
        .get("package")
        .and_then(toml::Value::as_array)
        .and_then(|pkgs| {
            pkgs.iter()
                .find(|p| p.get("name").and_then(toml::Value::as_str) == Some(package))
        });
    let actual_version = entry
        .and_then(|p| p.get("version"))
        .and_then(toml::Value::as_str)
        .unwrap_or("")
        .to_string();
    let lock_source = entry
        .and_then(|p| p.get("source"))
        .and_then(toml::Value::as_str)
        .map(str::to_string);

    // Digest of the actually selected artifact from the frozen mirror, and
    // the catalog's declared environment for that version.
    let mut actual_digest: Option<String> = None;
    let mut rust_version: Option<String> = None;
    if !actual_version.is_empty() {
        let mirror_rel = local_registry_of(workspace)?;
        actual_digest = Some(artifact_digest(
            workspace,
            &mirror_rel,
            &package,
            &actual_version,
        )?);
        rust_version = catalog_rust_version(workspace, &mirror_rel, &package, &actual_version)?;
    }

    let requested_digest = plan
        .get("source_digest")
        .and_then(Value::as_str)
        .map(str::to_string);
    let toolchain = authority
        .get("environment")
        .and_then(|e| e.get("toolchain"))
        .and_then(Value::as_str)
        .unwrap_or("")
        .to_string();

    let mut diagnostics: Vec<Value> = Vec::new();
    if actual_version.is_empty() {
        diagnostics.push(diagnostic(
            "wrong-target",
            "error",
            &format!(
                "cargo selected no `{package}` target at all; requested {package}@{release}"
            ),
        ));
    } else if actual_version != release {
        diagnostics.push(wrong_target_diagnostic(
            &package,
            &release,
            requested_digest.as_deref(),
            &actual_version,
            actual_digest.as_deref(),
        ));
    } else if let (Some(want), Some(got)) = (&requested_digest, &actual_digest) {
        if want != got {
            diagnostics.push(wrong_target_diagnostic(
                &package,
                &release,
                Some(want),
                &actual_version,
                Some(got),
            ));
        }
    }
    if let Some(rust) = &rust_version {
        if let Some(reason) = rust_version_conflict(rust, &toolchain) {
            diagnostics.push(diagnostic("environment-constraint", "error", &reason));
        }
    }

    if !diagnostics.is_empty() {
        let report = report_record(
            plan_digest,
            authority_digest,
            &package,
            &release,
            Some(&actual_version),
            actual_digest.as_deref(),
            lock_source.as_deref(),
            "refused",
            diagnostics,
            plan.get("pending_checks").cloned().unwrap_or(Value::Null),
            requested_digest_value(&requested_digest),
            plan.get("lock_version").cloned().unwrap_or(Value::Null),
        );
        return Ok(Evaluated {
            decision: "refuse",
            report,
            cargo_stderr: None,
        });
    }

    // Host evidence only: integrated checks remain pending.
    let pending: Vec<Value> = plan
        .get("pending_checks")
        .and_then(Value::as_arr)
        .map(|checks| checks.to_vec())
        .unwrap_or_default();
    let remaining: Vec<Value> = pending
        .iter()
        .filter(|c| {
            !matches!(
                c.as_str(),
                Some("cargo-resolution") | Some("closure-inspection")
            )
        })
        .cloned()
        .collect();
    let report = report_record(
        plan_digest,
        authority_digest,
        &package,
        &release,
        Some(&actual_version),
        actual_digest.as_deref(),
        lock_source.as_deref(),
        "host-evidence",
        Vec::new(),
        formats::arr(remaining),
        plan.get("source_digest").cloned().unwrap_or(Value::Null),
        plan.get("lock_version").cloned().unwrap_or(Value::Null),
    );
    Ok(Evaluated {
        decision: "accept",
        report,
        cargo_stderr: None,
    })
}

#[allow(clippy::too_many_arguments)]
fn report_record(
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
) -> Value {
    formats::obj(vec![
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
    ])
}

fn requested_digest_value(requested: &Option<String>) -> Value {
    match requested {
        Some(d) => formats::s(d),
        None => Value::Null,
    }
}

fn wrong_target_diagnostic(
    package: &str,
    release: &str,
    requested_digest: Option<&str>,
    actual_version: &str,
    actual_digest: Option<&str>,
) -> Value {
    diagnostic(
        "wrong-target",
        "error",
        &format!(
            "cargo selected a different artifact than authorized: requested {package}@{release} source {}; actual {package}@{actual_version} source {}",
            requested_digest.unwrap_or("unknown"),
            actual_digest.unwrap_or("unknown")
        ),
    )
}

/// Apply the proposed edit: replace the exact `package = "from"` line inside
/// the named table. Refuse if it no longer matches.
fn apply_edit(
    text: &str,
    table: &str,
    package: &str,
    from: &str,
    to: &str,
) -> Result<String, String> {
    let header = format!("[{table}]");
    let needle = format!("{package} = \"{from}\"");
    let replacement = format!("{package} = \"{to}\"");
    let mut current = String::new();
    let mut replaced = false;
    let mut out: Vec<String> = Vec::new();
    for line in text.lines() {
        let trimmed = line.trim();
        if trimmed.starts_with('[') && trimmed.ends_with(']') {
            current = trimmed.to_string();
        }
        if current == header && trimmed == needle {
            out.push(replacement.clone());
            replaced = true;
        } else {
            out.push(line.to_string());
        }
    }
    if !replaced {
        return Err(format!(
            "edit-mismatch: the proposed edit no longer applies: `{needle}` not found in {header}"
        ));
    }
    let mut edited = out.join("\n");
    if text.ends_with('\n') {
        edited.push('\n');
    }
    Ok(edited)
}

fn run_cargo(
    workspace: &Path,
    cargo_home: &Path,
    package: &str,
    release: &str,
) -> Result<std::process::Output, String> {
    let mut cmd = std::process::Command::new("cargo");
    cmd.args(["update", "--offline", "-p", package, "--precise", release])
        .current_dir(workspace)
        .env("CARGO_HOME", cargo_home)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped());
    // Strip ambient Cargo/Rust configuration so only the bundle's frozen
    // mirror governs resolution.
    for (key, _) in std::env::vars() {
        if key.starts_with("CARGO_") || key.starts_with("RUST") {
            cmd.env_remove(&key);
        }
    }
    let mut child = cmd
        .spawn()
        .map_err(|e| format!("host-resolution-failed: cannot start cargo: {e}"))?;
    let deadline = Instant::now() + CHILD_TIMEOUT;
    loop {
        match child.try_wait() {
            Ok(Some(_)) => break,
            Ok(None) => {
                if Instant::now() > deadline {
                    let _ = child.kill();
                    let _ = child.wait();
                    return Err(
                        "host-resolution-failed: cargo exceeded the bounded wait and was killed"
                            .to_string(),
                    );
                }
                std::thread::sleep(Duration::from_millis(50));
            }
            Err(e) => return Err(format!("host-resolution-failed: {e}")),
        }
    }
    child
        .wait_with_output()
        .map_err(|e| format!("host-resolution-failed: {e}"))
}

/// Read the local-registry mirror path from the bundle's own Cargo config.
fn local_registry_of(workspace: &Path) -> Result<String, String> {
    let config = workspace.join(".cargo").join("config.toml");
    let text = std::fs::read_to_string(&config).map_err(|_| {
        "isolation-refused: the bundle carries no .cargo/config.toml local-registry".to_string()
    })?;
    for line in text.lines() {
        let trimmed = line.trim();
        if let Some(rest) = trimmed.strip_prefix("local-registry") {
            if let Some(value) = rest.trim_start().strip_prefix('=').map(str::trim) {
                let value = value.trim_matches('"');
                if !value.is_empty() {
                    return Ok(value.to_string());
                }
            }
        }
    }
    Err(
        "isolation-refused: no local-registry source is configured for offline resolution"
            .to_string(),
    )
}

fn artifact_digest(
    workspace: &Path,
    mirror_rel: &str,
    package: &str,
    version: &str,
) -> Result<String, String> {
    // Mirrors use either the dl-template store layout or flat .crate files.
    let mirror = workspace.join(mirror_rel);
    let store = mirror
        .join(package)
        .join(version)
        .join(format!("{package}-{version}.crate"));
    let flat = mirror.join(format!("{package}-{version}.crate"));
    let path = if store.is_file() { store } else { flat };
    let bytes = std::fs::read(&path).map_err(|e| {
        format!(
            "missing-evidence: the selected artifact archive {} is unavailable: {e}",
            path.display()
        )
    })?;
    Ok(formats::sha256_digest(&bytes))
}

/// Sparse-index address of the catalog line file for a package name.
fn index_path(workspace: &Path, mirror_rel: &str, package: &str) -> PathBuf {
    let index = workspace.join(mirror_rel).join("index");
    match package.len() {
        0 | 1 => index.join("2").join(package),
        2 => index.join("3").join(package),
        3 => index.join(&package[0..2]).join(package),
        _ => index.join(&package[0..2]).join(&package[2..4]).join(package),
    }
}

/// The catalog line's declared rust-version for the selected version.
fn catalog_rust_version(
    workspace: &Path,
    mirror_rel: &str,
    package: &str,
    version: &str,
) -> Result<Option<String>, String> {
    let path = index_path(workspace, mirror_rel, package);
    let text = std::fs::read_to_string(&path).map_err(|e| {
        format!("missing-evidence: catalog index for `{package}` unavailable: {e}")
    })?;
    for line in text.lines() {
        if line.trim().is_empty() {
            continue;
        }
        let entry = formats::parse(line)
            .map_err(|e| format!("input-mismatch: catalog index line invalid: {e}"))?;
        if entry.str_field("vers")? == version {
            return Ok(entry
                .get("rust_version")
                .and_then(Value::as_str)
                .map(str::to_string));
        }
    }
    Ok(None)
}

/// Compare a catalog rust-version against the authorized toolchain.
fn rust_version_conflict(rust_version: &str, toolchain: &str) -> Option<String> {
    let (Some(r), Some(t)) = (parse_version(rust_version), parse_version(toolchain)) else {
        return None;
    };
    if r > t {
        Some(format!(
            "the selected target requires rustc {rust_version}, but the authorized toolchain is {toolchain}; the environment constraint refuses delivery independently of compatibility"
        ))
    } else {
        None
    }
}

fn parse_version(text: &str) -> Option<(u64, u64)> {
    let mut parts = text.split('.');
    let major = parts.next()?.parse().ok()?;
    let minor = parts.next().unwrap_or("0").parse().ok()?;
    Some((major, minor))
}
