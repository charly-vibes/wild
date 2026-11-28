// Purpose: Agent issue reporting for wild (beads wild-8g8, fleet lane of the
//   genesis add-fleet-adoption-plan, ticket genesis-svt).
// Responsibilities: Provide a `feedback` subcommand that validates an issue
//   kind, derives a title/body from piped stdin or the last recorded error
//   (`--from-last-error`), redacts home paths and secret values, appends an
//   environment bundle, and either prints a dry-run preview or writes the
//   report to a local file, mirroring the `genesis::feedback` contract
//   (FeedbackArgs semantics, valid kinds, redaction rules, LocalFile
//   outcome) in wild style.
// Rationale: The adoption row is additive: a new `feedback` subcommand with
//   no existing behavior changes. wild's design forbids network access and
//   adds no serde/regex dependencies (see src/genesis.rs for the same
//   pattern adopted for the envelope), so the report is always filed to a
//   local report file — the genesis fallback ladder's no-network outcome —
//   and redaction is implemented with plain string logic. The scratch
//   record format (`$XDG_CACHE_HOME/wild/errors.jsonl`) is shared with
//   genesis so a future scratch writer stays interoperable.

use crate::formats::{self, Value};
use std::io::{IsTerminal, Read};
use std::path::PathBuf;

/// Valid issue kinds (genesis::feedback vocabulary, including `aix-gap`
/// for AIX-artifact failures per add-artifact-provenance §5).
pub const VALID_KINDS: &[&str] = &["bug", "feature", "question", "chore", "aix-gap"];

/// The wild feedback GitHub repository, in `owner/repo` form, used to
/// redact the repo string out of report bodies.
const FEEDBACK_REPO: &str = "charly-vibes/wild";

/// Arguments for the feedback handler, mirroring
/// `genesis::feedback::FeedbackArgs`.
#[derive(Debug, Clone)]
pub struct FeedbackArgs {
    /// Kind of feedback: one of [`VALID_KINDS`].
    pub kind: String,
    /// User-supplied issue title. When set, overrides the derived title
    /// (keeping the `[{kind}] ` prefix).
    pub title: Option<String>,
    /// If true, print the issue body and the would-file command without
    /// writing a report.
    pub dry_run: bool,
    /// If true, read the last error from wild's scratch record to
    /// auto-populate the body.
    pub from_last_error: bool,
}

/// Result of a feedback request, mirroring the usable `GhResult` outcomes
/// of `genesis::feedback::handle_feedback` for a network-free tool.
#[derive(Debug, Clone)]
pub enum FeedbackOutcome {
    /// Report written to a local file (the genesis no-network fallback).
    ReportFile(PathBuf),
    /// Dry-run preview: title, labels, redacted body, and the `gh`
    /// command a human would run.
    DryRun {
        title: String,
        labels: Vec<String>,
        body: String,
        gh_command: String,
    },
}

/// Handle a feedback request — validate kind, build body, redact, and
/// file (dry-run preview or local report file).
///
/// Mirrors `genesis::feedback::handle_feedback`; the tool identity is
/// fixed to `wild` + the package version and the repo to
/// [`FEEDBACK_REPO`].
pub fn handle_feedback(
    args: &FeedbackArgs,
    project_root: &std::path::Path,
) -> Result<FeedbackOutcome, String> {
    handle_feedback_for(
        args,
        "wild",
        env!("CARGO_PKG_VERSION"),
        FEEDBACK_REPO,
        project_root,
    )
}

/// `handle_feedback` with an explicit tool identity (the genesis
/// handler's signature shape, kept for testability).
pub fn handle_feedback_for(
    args: &FeedbackArgs,
    tool_name: &str,
    tool_version: &str,
    repo: &str,
    _project_root: &std::path::Path,
) -> Result<FeedbackOutcome, String> {
    validate_kind(&args.kind)?;

    let (title, body_parts, command, exit_code) = issue_title_and_body(args, tool_name)?;
    let title = apply_title_override(&args.kind, &title, args.title.as_deref());
    let mut body_parts = body_parts;
    body_parts.push(context_bundle_section(
        tool_name,
        tool_version,
        command.as_deref(),
        exit_code,
    ));
    let body = redact_body(&body_parts.join("\n\n"), home_dir().as_deref(), repo);
    let labels = labels_for_kind(&args.kind);

    if args.dry_run {
        return Ok(FeedbackOutcome::DryRun {
            gh_command: format!(
                "gh issue create --repo {repo} --title \"{title}\" --label {}",
                labels.join(", ")
            ),
            title,
            labels,
            body,
        });
    }
    Ok(FeedbackOutcome::ReportFile(write_local_report(
        &title, &labels, &body,
    )))
}

/// Validate the issue kind with the genesis error messages.
fn validate_kind(kind: &str) -> Result<(), String> {
    if VALID_KINDS.contains(&kind) {
        return Ok(());
    }
    Err(format!(
        "unknown kind: '{kind}'. Valid kinds: {}",
        VALID_KINDS.join(", ")
    ))
}

/// The caller's home directory, when set and non-empty.
fn home_dir() -> Option<PathBuf> {
    std::env::var("HOME")
        .ok()
        .filter(|h| !h.is_empty())
        .map(PathBuf::from)
}

/// Derive the issue title and body sections from the content source:
/// the last scratch error (`--from-last-error`) or piped stdin.
/// Returns (title, body parts, scratch command, scratch exit code).
fn issue_title_and_body(
    args: &FeedbackArgs,
    tool_name: &str,
) -> Result<(String, Vec<String>, Option<String>, Option<i64>), String> {
    if args.from_last_error {
        title_and_body_from_error(&args.kind, tool_name)
    } else {
        title_and_body_from_stdin(&args.kind).map(|(t, b)| (t, b, None, None))
    }
}

/// Title/body from the last recorded error for `tool_name`, read from
/// the genesis-compatible scratch file
/// (`$XDG_CACHE_HOME|~/.cache`/`<tool>/errors.jsonl`).
fn title_and_body_from_error(
    kind: &str,
    tool_name: &str,
) -> Result<(String, Vec<String>, Option<String>, Option<i64>), String> {
    let path = scratch_path(tool_name);
    let text = std::fs::read_to_string(&path)
        .map_err(|_| format!("No recent error recorded for '{tool_name}'. Run a command that produces an error first."))?;
    let record = text
        .lines()
        .rev()
        .find(|l| !l.trim().is_empty())
        .and_then(|l| formats::parse(l).ok())
        .ok_or_else(|| {
            format!("No recent error recorded for '{tool_name}'. Run a command that produces an error first.")
        })?;
    let command: Option<String> = record
        .get("argv")
        .and_then(Value::as_arr)
        .map(|argv| {
            argv.iter()
                .filter_map(Value::as_str)
                .collect::<Vec<_>>()
                .join(" ")
        })
        .filter(|c| !c.is_empty());
    let exit_code = record.get("exit").and_then(Value::as_int);
    let cmd_str = command.clone().unwrap_or_default();
    let title = format!("[{kind}] auto-reported error: {cmd_str}");
    let mut body_parts = vec!["## Error\n\n".to_string()];
    body_parts.push(format!("**Command:** `{cmd_str}`\n\n"));
    if let Some(exit) = exit_code {
        body_parts.push(format!("**Exit code:** {exit}\n\n"));
    }
    if let Some(message) = record.get("message").and_then(Value::as_str) {
        body_parts.push(fenced_code_block(message));
    }
    if let Some(footer) = record.get("footer").and_then(Value::as_str) {
        body_parts.push(format!("**Suggestion:** {footer}\n\n"));
    }
    Ok((title, body_parts, command, exit_code))
}

/// Markdown fenced code block whose fence is one backtick longer than the
/// longest backtick run in the (4000-char capped) message, so a message
/// containing ``` cannot terminate the fence early (genesis rule).
fn fenced_code_block(message: &str) -> String {
    const MAX_MESSAGE_LEN: usize = 4000;
    let (message, truncated) = match message.char_indices().nth(MAX_MESSAGE_LEN) {
        Some((byte_idx, _)) => (&message[..byte_idx], true),
        None => (message, false),
    };
    let longest_run = message
        .split(|c| c != '`')
        .map(|run| run.len())
        .max()
        .unwrap_or(0);
    let fence = "`".repeat(longest_run.max(2) + 1);
    let mut out = format!("{fence}\n{message}\n{fence}\n\n");
    if truncated {
        out.push_str("\n[… message truncated — original exceeded 4000 chars …]\n\n");
    }
    out
}

/// Title/body from piped stdin (e.g. `echo "bug report" | wild feedback bug`).
fn title_and_body_from_stdin(kind: &str) -> Result<(String, Vec<String>), String> {
    let Some(input) = read_piped_stdin() else {
        return Err(
            "No issue content specified. Use --from-last-error or pipe content into stdin."
                .to_string(),
        );
    };
    let trimmed = input.trim();
    // Multi-line input promotes the first line to the title; single-line
    // input keeps the generic `[{kind}] feedback report` title (genesis rule).
    let (title, description) = match trimmed.split_once('\n').map(|(f, r)| (f.trim(), r.trim())) {
        Some((first, rest)) if !first.is_empty() => (format!("[{kind}] {first}"), rest.to_string()),
        _ => (format!("[{kind}] feedback report"), trimmed.to_string()),
    };
    let body = if description.is_empty() {
        Vec::new()
    } else {
        vec![format!("## Description\n\n{description}\n\n")]
    };
    Ok((title, body))
}

/// Piped stdin for a feedback report; `None` when the caller is on a TTY
/// or the pipe carries nothing.
fn read_piped_stdin() -> Option<String> {
    if std::io::stdin().is_terminal() {
        return None;
    }
    let mut input = String::new();
    std::io::stdin().read_to_string(&mut input).ok();
    (!input.trim().is_empty()).then_some(input)
}

/// Apply a user-supplied title override, keeping the `[{kind}] ` prefix.
fn apply_title_override(kind: &str, derived: &str, title: Option<&str>) -> String {
    match title {
        Some(t) => format!("[{kind}] {t}"),
        None => derived.to_string(),
    }
}

/// Labels for a given issue kind (genesis rule).
fn labels_for_kind(kind: &str) -> Vec<String> {
    let mut labels = vec!["agent-reported".to_string()];
    match kind {
        "bug" => {
            labels.push("bug".to_string());
            labels.push("has-repro".to_string());
        }
        "feature" => labels.push("enhancement".to_string()),
        "question" => labels.push("question".to_string()),
        "chore" => labels.push("chore".to_string()),
        _ => {}
    }
    labels
}

/// Gather the environment bundle and format it as the trailing body
/// section: tool/version, os/arch, and a repro hash over the tool
/// identity plus the reported command/exit (when the body came from the
/// scratch record).
fn context_bundle_section(
    tool_name: &str,
    tool_version: &str,
    command: Option<&str>,
    exit_code: Option<i64>,
) -> String {
    let mut out = String::from("## Environment\n\n");
    out.push_str(&format!("- tool: {tool_name} {tool_version}\n"));
    out.push_str(&format!(
        "- os/arch: {}/{}\n",
        std::env::consts::OS,
        std::env::consts::ARCH
    ));
    if let Some(command) = command {
        out.push_str(&format!("- command: {command}\n"));
    }
    if let Some(exit) = exit_code {
        out.push_str(&format!("- exit_code: {exit}\n"));
    }
    let repro = format!(
        "{tool_name}|{tool_version}|{}|{}",
        command.unwrap_or_default(),
        exit_code.map(|e| e.to_string()).unwrap_or_default()
    );
    out.push_str(&format!(
        "- repro_hash: `{}`\n",
        formats::sha256_digest(repro.as_bytes())
    ));
    out
}

/// Join body sections, then redact home paths and the target repo.
fn redact_body(body: &str, home: Option<&std::path::Path>, repo: &str) -> String {
    let body = redact_secret_values(body);
    let body = match home {
        Some(home) => body.replace(&home.display().to_string(), "~"),
        None => body.to_string(),
    };
    body.replace(repo, "repo")
}

/// Redact values that look like secrets, matching values not key
/// substrings (genesis rule 5): `key=value`, `key: value`, and
/// `--key value` forms for token/secret/password/apikey/pat/bearer keys.
fn redact_secret_values(input: &str) -> String {
    const SECRET_KEYS: &[&str] = &["token", "secret", "password", "apikey", "pat", "bearer"];
    let mut out = input.to_string();
    for key in SECRET_KEYS {
        for sep in ["=", ": ", " "] {
            let needle = format!("{key}{sep}");
            let mut start = 0;
            while let Some(pos) = out.to_lowercase()[start..].find(&needle) {
                let abs = start + pos;
                let value_start = abs + needle.len();
                let end = out[value_start..]
                    .find(|c: char| c.is_whitespace() || c == '"')
                    .map(|e| value_start + e)
                    .unwrap_or(out.len());
                let value = out[value_start..end].trim();
                if !value.is_empty() {
                    out.replace_range(value_start..end, "[redacted]");
                    start = value_start + "[redacted]".len();
                } else {
                    start = value_start.max(start + 1);
                }
                if start >= out.len() {
                    break;
                }
            }
        }
    }
    out
}

/// Reports directory: `$XDG_CACHE_HOME/wild/reports` when set and
/// non-empty, else `~/.cache/wild/reports`, else a temp-dir fallback —
/// the same resolution as the genesis reports dir, empty values falling
/// through so it is never relative to the cwd.
fn reports_dir() -> PathBuf {
    let tool = "wild";
    if let Some(cache) = std::env::var("XDG_CACHE_HOME")
        .ok()
        .filter(|v| !v.is_empty())
    {
        return PathBuf::from(cache).join(tool).join("reports");
    }
    if let Some(home) = std::env::var("HOME").ok().filter(|v| !v.is_empty()) {
        return PathBuf::from(home)
            .join(".cache")
            .join(tool)
            .join("reports");
    }
    std::env::temp_dir().join(tool).join("reports")
}

/// The scratch errors file for a tool: `$XDG_CACHE_HOME|~/.cache`/
/// `<tool>/errors.jsonl` (genesis scratch layout; temp-dir fallback).
fn scratch_path(tool_name: &str) -> PathBuf {
    let base = match std::env::var("XDG_CACHE_HOME")
        .ok()
        .filter(|v| !v.is_empty())
    {
        Some(cache) => PathBuf::from(cache),
        None => match std::env::var("HOME").ok().filter(|v| !v.is_empty()) {
            Some(home) => PathBuf::from(home).join(".cache"),
            None => std::env::temp_dir(),
        },
    };
    base.join(tool_name).join("errors.jsonl")
}

/// Whole seconds since the Unix epoch (best-effort; 0 on clock failure).
fn unix_timestamp_secs() -> u64 {
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
}

/// Write the issue body to a local report file, mirroring the genesis
/// local-fallback report format, and return the path.
fn write_local_report(title: &str, labels: &[String], body: &str) -> PathBuf {
    let dir = reports_dir();
    let _ = std::fs::create_dir_all(&dir);
    let path = dir.join(format!("report-{}.md", unix_timestamp_secs()));
    let content = format!(
        "# Issue Report\n\n**Title:** {title}\n\n**Repo:** {FEEDBACK_REPO}\n\n**Labels:** {}\n\n---\n\n{body}\n---\n\n*To retry: `gh issue create --repo {FEEDBACK_REPO} --title \"{title}\" --body-file -`*\n",
        labels.join(", ")
    );
    let _ = std::fs::write(&path, &content);
    path
}

#[cfg(test)]
mod tests {
    use super::*;

    fn run_with_stdin(input: Option<&str>, args: &FeedbackArgs) -> Result<(), String> {
        // stdin cannot be injected through the module's `read_piped_stdin`
        // (it reads the real stdin); the tests below exercise the CLI
        // through tests/runtime/test_feedback.py instead. Kept for the
        // kind validator only.
        let _ = input;
        validate_kind(&args.kind)
    }

    #[test]
    fn rejects_unknown_kind_with_valid_list() {
        let err = run_with_stdin(
            None,
            &FeedbackArgs {
                kind: "bugg".to_string(),
                title: None,
                dry_run: true,
                from_last_error: false,
            },
        )
        .unwrap_err();
        assert!(err.contains("unknown kind: 'bugg'"), "{err}");
        assert!(
            err.contains("Valid kinds: bug, feature, question, chore, aix-gap"),
            "{err}"
        );
    }

    #[test]
    fn accepts_every_valid_kind() {
        for kind in VALID_KINDS {
            assert!(run_with_stdin(
                None,
                &FeedbackArgs {
                    kind: (*kind).to_string(),
                    title: None,
                    dry_run: true,
                    from_last_error: false,
                }
            )
            .is_ok());
        }
    }

    #[test]
    fn title_override_keeps_kind_prefix() {
        assert_eq!(
            apply_title_override("bug", "[bug] feedback report", Some("crash on check")),
            "[bug] crash on check"
        );
    }

    #[test]
    fn multiline_stdin_promotes_first_line_to_title() {
        let (title, body) = title_and_body_from_stdin_parts("crash on check\nit fails badly");
        assert_eq!(title, "[bug] crash on check");
        assert!(body[0].contains("it fails badly"), "{:?}", body);
    }

    // Direct helper mirroring `title_and_body_from_stdin` without stdin.
    fn title_and_body_from_stdin_parts(input: &str) -> (String, Vec<String>) {
        let kind = "bug";
        let trimmed = input.trim();
        let (title, description) = match trimmed.split_once('\n').map(|(f, r)| (f.trim(), r.trim()))
        {
            Some((first, rest)) if !first.is_empty() => {
                (format!("[{kind}] {first}"), rest.to_string())
            }
            _ => (format!("[{kind}] feedback report"), trimmed.to_string()),
        };
        let body = if description.is_empty() {
            Vec::new()
        } else {
            vec![format!("## Description\n\n{description}\n\n")]
        };
        (title, body)
    }

    #[test]
    fn redacts_secret_values_and_home_paths() {
        let home = std::path::Path::new("/home/sasha");
        let body = "token=abc123 secret: top --password hunter2 at /home/sasha/wild";
        let redacted = redact_body(body, Some(home), FEEDBACK_REPO);
        assert!(!redacted.contains("abc123"), "{redacted}");
        assert!(!redacted.contains("hunter2"), "{redacted}");
        assert!(!redacted.contains("/home/sasha"), "{redacted}");
        assert!(redacted.contains("~/wild"), "{redacted:?}");
    }

    #[test]
    fn fenced_block_survives_backticks_in_message() {
        let block = fenced_code_block("```rust\nfn main() {}\n```");
        assert!(block.starts_with("````\n"), "{block}");
        assert!(block.ends_with("````\n\n"), "{block}");
    }
}
