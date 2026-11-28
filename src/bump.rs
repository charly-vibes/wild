// Purpose: Maintainer-side declared-bump derivation (change
//   add-declared-bump-derivation, bd wild-zh6).
// Responsibilities: Classify the spec-corpus delta between a base release
//   (git ref) and a candidate tree at the openspec requirement level; map
//   the aggregated delta to exactly one bump class (ADDED-only -> minor
//   "accretes"; any MODIFIED/REMOVED/RENAMED -> major "revokes"; empty or
//   row-only delta -> patch; missing/non-computable base -> Unknown with a
//   named diagnostic and no fabricated class); apply the upward-only
//   override (raising records the reason, lowering is refused with
//   `bump_class_lowering_refused` and the proposed class stands); render
//   the local-1 `declared-bump-record` artifact the adopt audit compares
//   against computed verdicts.
// Rationale: The classifier proposes, the adopt layer audits, and the human
//   can only bump upward (CORR-001). The derivation is advisory (v1 gates
//   nothing, shadow_never_blocks), reads only the corpus delta, and never
//   guesses through abstention — a missing base yields Unknown, following
//   the never-fabricated house style (missing-base-contract precedent).
//   Renames are detected structurally: a requirement id removed at the
//   base and an id added in the candidate whose normalized body text is
//   identical pair into one RENAMED delta row.

use std::collections::BTreeMap;
use std::path::{Path, PathBuf};
use std::process::Command;

use crate::formats::{self, Value};

pub const CORPUS_DIR: &str = "openspec/specs";
pub const DIAG_MISSING_BASE: &str = "missing_base_corpus";
pub const DIAG_LOWERING_REFUSED: &str = "bump_class_lowering_refused";

/// Rank used by the upward-only override: patch < minor < major.
fn rank(bump_class: &str) -> u8 {
    match bump_class {
        "patch" => 0,
        "minor" => 1,
        "major" => 2,
        _ => 0,
    }
}

/// The requirement-level delta kinds the classifier reads. The class is the
/// derived bump value; the claim is the recorded artifact.
#[derive(Debug, Default, PartialEq)]
pub struct Delta {
    pub added: Vec<String>,
    pub modified: Vec<String>,
    pub removed: Vec<String>,
    /// (old id, new id) pairs with identical bodies — revokes old, accretes new.
    pub renamed: Vec<(String, String)>,
}

impl Delta {
    pub fn is_empty(&self) -> bool {
        self.added.is_empty()
            && self.modified.is_empty()
            && self.removed.is_empty()
            && self.renamed.is_empty()
    }
}

/// A requirement block: its id (the text after `### Requirement: `) and the
/// normalized body used for rename pairing and modification detection.
#[derive(Debug, Clone, PartialEq)]
pub struct Requirement {
    pub id: String,
    pub body: String,
}

/// Parse the requirement-level sections of one specodelic corpus file.
/// Specodelic-only rows (Constraints/Properties tables) are ignored here by
/// construction: they ride the release without changing the class.
pub fn parse_requirements(text: &str) -> Vec<Requirement> {
    let mut out = Vec::new();
    let mut current: Option<Requirement> = None;
    for line in text.lines() {
        if let Some(rest) = line.strip_prefix("### Requirement: ") {
            if let Some(done) = current.take() {
                out.push(done);
            }
            current = Some(Requirement {
                id: rest.trim().to_string(),
                body: String::new(),
            });
        } else if let Some(req) = current.as_mut() {
            let starts_new_block = line.starts_with("## ") || line.starts_with("### ");
            if starts_new_block {
                if let Some(done) = current.take() {
                    out.push(done);
                }
            } else {
                req.body.push_str(line.trim());
                req.body.push('\n');
            }
        }
    }
    if let Some(done) = current.take() {
        out.push(done);
    }
    out
}

fn normalize(body: &str) -> String {
    body.split_whitespace().collect::<Vec<_>>().join(" ")
}

/// Aggregate the whole corpus delta into one delta, then classify once.
/// Renames pair removed base ids with added candidate ids carrying the same
/// normalized body; left-over removals/additions keep their own kind.
pub fn derive_delta(
    base: &BTreeMap<String, Vec<Requirement>>,
    candidate: &BTreeMap<String, Vec<Requirement>>,
) -> Delta {
    let mut delta = Delta::default();
    let mut base_all: BTreeMap<String, String> = BTreeMap::new();
    for reqs in base.values() {
        for req in reqs {
            base_all.insert(req.id.clone(), normalize(&req.body));
        }
    }
    let mut cand_all: BTreeMap<String, String> = BTreeMap::new();
    for reqs in candidate.values() {
        for req in reqs {
            cand_all.insert(req.id.clone(), normalize(&req.body));
        }
    }

    let mut added: Vec<String> = Vec::new();
    for (id, body) in &cand_all {
        match base_all.get(id) {
            None => added.push(id.clone()),
            Some(old) if old != body => delta.modified.push(id.clone()),
            Some(_) => {}
        }
    }
    let mut removed: Vec<String> = Vec::new();
    for id in base_all.keys() {
        if !cand_all.contains_key(id) {
            removed.push(id.clone());
        }
    }
    // rename pairing: identical bodies, ids differ
    removed.retain(|old_id| {
        let old_body = base_all.get(old_id).cloned().unwrap_or_default();
        if let Some(new_id) = added
            .iter()
            .find(|id| cand_all.get(*id).map(|b| *b == old_body).unwrap_or(false))
            .cloned()
        {
            delta.renamed.push((old_id.clone(), new_id.clone()));
            added.retain(|id| id != &new_id);
            false
        } else {
            true
        }
    });
    delta.added = added;
    delta.removed = removed;
    delta
}

/// The total mapping (task 4.1): every well-formed delta shape maps to
/// exactly one class — None is the abstention outcome, never a guess.
pub fn classify(delta: &Delta) -> Option<(&'static str, &'static str)> {
    if delta.is_empty() {
        return Some(("patch", ""));
    }
    if !delta.modified.is_empty() || !delta.removed.is_empty() || !delta.renamed.is_empty() {
        return Some(("major", "revokes"));
    }
    if !delta.added.is_empty() {
        return Some(("minor", "accretes"));
    }
    None
}

fn corpus_files(tree: &Path) -> Result<Vec<PathBuf>, String> {
    let corpus = tree.join(CORPUS_DIR);
    let mut files = Vec::new();
    let entries = std::fs::read_dir(&corpus)
        .map_err(|e| format!("candidate corpus unreadable at {}: {e}", corpus.display()))?;
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            if let Ok(inner) = std::fs::read_dir(&path) {
                for f in inner.flatten() {
                    if f.path()
                        .file_name()
                        .map(|n| n == "spec.md")
                        .unwrap_or(false)
                    {
                        files.push(f.path());
                    }
                }
            }
        } else if path.file_name().map(|n| n == "spec.md").unwrap_or(false) {
            files.push(path);
        }
    }
    files.sort();
    Ok(files)
}

fn git(repo: &Path, args: &[&str]) -> Result<String, String> {
    let out = Command::new("git")
        .arg("-C")
        .arg(repo)
        .args(args)
        .output()
        .map_err(|e| format!("git spawn failed: {e}"))?;
    if !out.status.success() {
        return Err(format!(
            "git {} failed: {}",
            args.first().unwrap_or(&""),
            String::from_utf8_lossy(&out.stderr).trim()
        ));
    }
    Ok(String::from_utf8_lossy(&out.stdout).to_string())
}

/// Read the base corpus straight from git so no checkout is needed; a
/// missing ref, a failed read, or a corpus absent at the base is a
/// non-computable base (Unknown), never a fabricated delta.
fn base_corpus(tree: &Path, base: &str) -> Result<BTreeMap<String, Vec<Requirement>>, String> {
    git(tree, &["cat-file", "-e", &format!("{base}^{{commit}}")])?;
    let listing = git(
        tree,
        &["ls-tree", "-r", "--name-only", "-z", base, CORPUS_DIR],
    )?;
    let mut out = BTreeMap::new();
    for name in listing
        .trim_matches('\0')
        .split('\0')
        .filter(|s| !s.is_empty())
    {
        let text = git(tree, &["show", &format!("{base}:{name}")])?;
        let rel = name.trim_start_matches(CORPUS_DIR).trim_start_matches('/');
        out.insert(rel.to_string(), parse_requirements(&text));
    }
    if out.is_empty() {
        return Err(format!("no corpus files at base `{base}`"));
    }
    Ok(out)
}

fn candidate_corpus(tree: &Path) -> Result<BTreeMap<String, Vec<Requirement>>, String> {
    let mut out = BTreeMap::new();
    for path in corpus_files(tree)? {
        let rel = path
            .strip_prefix(tree.join(CORPUS_DIR))
            .map_err(|e| format!("corpus path error: {e}"))?
            .to_string_lossy()
            .to_string();
        let text = std::fs::read_to_string(&path)
            .map_err(|e| format!("cannot read {}: {e}", path.display()))?;
        out.insert(rel, parse_requirements(&text));
    }
    if out.is_empty() {
        return Err("no candidate corpus files".to_string());
    }
    Ok(out)
}

/// The confirmed claim after the upward-only override rule.
pub fn apply_override(
    proposed: &str,
    proposed_reason: &str,
    confirm: Option<&str>,
    reason: Option<&str>,
) -> (String, String, bool, Vec<Value>) {
    let mut diagnostics = Vec::new();
    let Some(confirm) = confirm else {
        return (
            proposed.to_string(),
            proposed_reason.to_string(),
            false,
            diagnostics,
        );
    };
    if reason.is_none() {
        return (
            proposed.to_string(),
            proposed_reason.to_string(),
            false,
            diagnostics,
        );
    }
    if rank(confirm) < rank(proposed) {
        diagnostics.push(diagnostic(
            DIAG_LOWERING_REFUSED,
            format!(
                "override to `{confirm}` would lower the proposed class `{proposed}`; \
                 upward-only override keeps the proposed class"
            ),
            "info",
        ));
        return (
            proposed.to_string(),
            proposed_reason.to_string(),
            false,
            diagnostics,
        );
    }
    (
        confirm.to_string(),
        reason.unwrap().to_string(),
        true,
        diagnostics,
    )
}

fn diagnostic(code: &str, reason: String, severity: &str) -> Value {
    formats::obj(vec![
        ("code", formats::s(code)),
        ("severity", formats::s(severity)),
        ("source", Value::Null),
        ("slots", formats::arr(Vec::new())),
        ("reason", formats::s(&reason)),
    ])
}

fn s_opt(v: Option<&str>) -> Value {
    match v {
        Some(s) => formats::s(s),
        None => Value::Null,
    }
}

/// Render the local-1 declared-bump-record artifact.
#[allow(clippy::too_many_arguments)]
pub fn record(
    base: Option<&str>,
    release: Option<&str>,
    delta: Option<&Delta>,
    proposed: Option<&str>,
    confirmed: Option<&str>,
    reason: Option<&str>,
    overridden: bool,
    diagnostics: &[Value],
) -> Value {
    let delta_value = match delta {
        Some(d) => formats::obj(vec![
            (
                "added",
                formats::arr(d.added.iter().map(|s| formats::s(s)).collect()),
            ),
            (
                "modified",
                formats::arr(d.modified.iter().map(|s| formats::s(s)).collect()),
            ),
            (
                "removed",
                formats::arr(d.removed.iter().map(|s| formats::s(s)).collect()),
            ),
            (
                "renamed",
                formats::arr(
                    d.renamed
                        .iter()
                        .map(|(a, b)| formats::arr(vec![formats::s(a), formats::s(b)]))
                        .collect(),
                ),
            ),
        ]),
        None => Value::Null,
    };
    formats::obj(vec![
        ("version", formats::s("local-1")),
        ("kind", formats::s("declared-bump-record")),
        ("base", s_opt(base)),
        ("release", s_opt(release)),
        ("delta", delta_value),
        ("proposed", s_opt(proposed)),
        ("confirmed", s_opt(confirmed)),
        ("reason", s_opt(reason)),
        ("overridden", Value::Bool(overridden)),
        ("diagnostics", formats::arr(diagnostics.to_vec())),
    ])
}

/// Run the derivation for the CLI. Returns the v1 envelope payload fields
/// plus the record; the caller renders the envelope and exits 0 for every
/// computed outcome (advisory, shadow_never_blocks).
pub fn derive(
    tree: &Path,
    base: &str,
    release: Option<&str>,
    confirm: Option<&str>,
    reason: Option<&str>,
) -> Result<(Value, String), String> {
    let mut diagnostics: Vec<Value> = Vec::new();
    let candidate = candidate_corpus(tree)?;
    let base_map = match base_corpus(tree, base) {
        Ok(b) => b,
        Err(e) => {
            diagnostics.push(diagnostic(
                DIAG_MISSING_BASE,
                format!("no computable base corpus at `{base}`: {e}"),
                "warning",
            ));
            let rec = record(
                Some(base),
                release,
                None,
                None,
                None,
                None,
                false,
                &diagnostics,
            );
            return Ok((rec, "Unknown".to_string()));
        }
    };
    let delta = derive_delta(&base_map, &candidate);
    let (proposed, proposed_reason) =
        classify(&delta).expect("classify is total over well-formed deltas");
    let (confirmed, reason_text, overridden, mut override_diag) =
        apply_override(proposed, proposed_reason, confirm, reason);
    diagnostics.append(&mut override_diag);
    let reason_value = if reason_text.is_empty() {
        None
    } else {
        Some(reason_text)
    };
    let rec = record(
        Some(base),
        release,
        Some(&delta),
        Some(proposed),
        Some(&confirmed),
        reason_value.as_deref(),
        overridden,
        &diagnostics,
    );
    let assurance = if confirmed == "Unknown" {
        "Unknown"
    } else {
        "PassDeclared"
    };
    Ok((rec, assurance.to_string()))
}

#[cfg(test)]
mod tests {
    use super::*;

    fn req(id: &str, body: &str) -> Requirement {
        Requirement {
            id: id.to_string(),
            body: body.to_string(),
        }
    }

    fn corpus(entries: &[(&str, &[Requirement])]) -> BTreeMap<String, Vec<Requirement>> {
        entries
            .iter()
            .map(|(k, v)| (k.to_string(), v.to_vec()))
            .collect()
    }

    #[test]
    fn added_only_is_minor_accretes() {
        let base = corpus(&[("a.md", &[req("Alpha", "keep alpha")])]);
        let cand = corpus(&[(
            "a.md",
            &[req("Alpha", "keep alpha"), req("Beta", "keep beta")],
        )]);
        let delta = derive_delta(&base, &cand);
        assert_eq!(delta.added, vec!["Beta"]);
        assert_eq!(classify(&delta), Some(("minor", "accretes")));
    }

    #[test]
    fn modified_is_major_revokes() {
        let base = corpus(&[("a.md", &[req("Alpha", "keep alpha")])]);
        let cand = corpus(&[("a.md", &[req("Alpha", "refuse removed")])]);
        let delta = derive_delta(&base, &cand);
        assert_eq!(delta.modified, vec!["Alpha"]);
        assert_eq!(classify(&delta), Some(("major", "revokes")));
    }

    #[test]
    fn removed_is_major_revokes() {
        let base = corpus(&[("a.md", &[req("A", "b"), req("B", "c")])]);
        let cand = corpus(&[("a.md", &[req("A", "b")])]);
        let delta = derive_delta(&base, &cand);
        assert_eq!(delta.removed, vec!["B"]);
        assert_eq!(classify(&delta), Some(("major", "revokes")));
    }

    #[test]
    fn rename_is_major_revoke_accrete() {
        let base = corpus(&[("a.md", &[req("Alpha", "same body")])]);
        let cand = corpus(&[("a.md", &[req("Gamma", "same body")])]);
        let delta = derive_delta(&base, &cand);
        assert_eq!(
            delta.renamed,
            vec![("Alpha".to_string(), "Gamma".to_string())]
        );
        assert!(delta.added.is_empty() && delta.removed.is_empty());
        assert_eq!(classify(&delta), Some(("major", "revokes")));
    }

    #[test]
    fn empty_delta_is_patch() {
        let base = corpus(&[("a.md", &[req("A", "b")])]);
        let delta = derive_delta(&base, &base);
        assert_eq!(classify(&delta), Some(("patch", "")));
    }

    #[test]
    fn classification_is_total_over_shapes() {
        // property (task 4.1): every well-formed shape maps to exactly one class
        for added in 0..3 {
            for revoked in 0..3 {
                let delta = Delta {
                    added: vec!["x".to_string(); added],
                    modified: vec!["m".to_string(); revoked],
                    removed: Vec::new(),
                    renamed: Vec::new(),
                };
                let expected = if revoked > 0 {
                    ("major", "revokes")
                } else if added > 0 {
                    ("minor", "accretes")
                } else {
                    ("patch", "")
                };
                assert_eq!(classify(&delta), Some(expected));
            }
        }
    }

    #[test]
    fn override_lowering_is_refused_and_proposal_stands() {
        let (confirmed, reason, overridden, diag) =
            apply_override("major", "revokes", Some("minor"), Some("harmless"));
        assert_eq!(confirmed, "major");
        assert_eq!(reason, "revokes");
        assert!(!overridden);
        assert!(format!("{diag:?}").contains(DIAG_LOWERING_REFUSED));
    }

    #[test]
    fn override_raise_records_reason() {
        let (confirmed, reason, overridden, _) =
            apply_override("minor", "accretes", Some("major"), Some("caution"));
        assert_eq!(confirmed, "major");
        assert_eq!(reason, "caution");
        assert!(overridden);
    }
}
