// Purpose: Authored-obligation enforcement for the wild local checker
//   (beads wild-mh5.3, wild-mh5.4).
// Responsibilities: Own the trusted obligations domain — load and strictly
//   validate the external obligations document and transition record,
//   evaluate accepted and proposed obligations against the trusted base and
//   the candidate (structural predicates bind and accrete; retained law
//   suites execute through the sandboxed law runner), parse the five
//   law-invocation inputs (harnesses, fixtures, budgets, environment,
//   evaluation_time) as a complete set, load the base-bound harness
//   document, and build the invocation-commitment record with real supplied
//   bindings and enforced sandbox capabilities once laws execute.
// Rationale: Obligation enforcement is a responsibility of its own (the
//   check module was carrying both request validation and obligation
//   semantics past the pretender file-size ratchet). The decided semantics
//   stay those of the mh5.3/mh5.4 interactive reviews: the candidate never
//   supplies accepted context, unauthorized weakening is a definite
//   counterexample with obligation-change diagnostics, executed laws are
//   method-labelled evidence whose captured failure modes stay inconclusive,
//   and a policy requiring law evidence over only a proposed obligation
//   yields Unknown, never an error.

use crate::check::{contract_slots, is_subtype};
use crate::extract::{ExtractionOutcome, LOCAL_VERSION};
use crate::formats::{self, Value};
use crate::harness::LawOutcome;

const OBLIGATIONS_REF_FIELDS: &[&str] = &["digest", "path"];

pub(crate) const OBLIGATION_FIELDS: &[&str] = &[
    "id",
    "scope",
    "origin",
    "state",
    "authority",
    "predicate",
];
pub(crate) const AUTHORITY_FIELDS: &[&str] = &["name", "digest"];
pub(crate) const TRANSITION_FIELDS: &[&str] = &[
    "old_digest",
    "new_digest",
    "reason",
    "affected_consumers",
    "authority",
];

/// One validated obligation record from the trusted obligations document.
pub(crate) struct Obligation {
    pub(crate) id: String,
    pub(crate) scope: String,
    pub(crate) origin: String,
    pub(crate) state: String,
    pub(crate) kind: &'static str,
    pub(crate) predicate_digest: String,
    /// Structural predicate's inline contract record (digest-bound).
    contract: Option<Value>,
    /// Law predicate's executable suite content digest.
    suite_digest: Option<String>,
}

/// A validated externally authorized old-to-new obligation transition.
pub(crate) struct Transition {
    old_digest: String,
    new_digest: String,
    reason: String,
    affected_consumers: Vec<String>,
    authority_digest: String,
}

impl Transition {
    pub(crate) fn to_value(&self) -> Value {
        formats::obj(vec![
            ("old_digest", formats::s(&self.old_digest)),
            ("new_digest", formats::s(&self.new_digest)),
            ("reason", formats::s(&self.reason)),
            (
                "affected_consumers",
                formats::arr(
                    self.affected_consumers
                        .iter()
                        .map(|c| formats::s(c))
                        .collect(),
                ),
            ),
            ("authority_digest", formats::s(&self.authority_digest)),
        ])
    }
}

/// The obligations field is either absent/null (no authored obligations yet)
/// or a strict reference {digest, path} naming a trusted external document.
/// The candidate never supplies or selects this context.
pub(crate) fn validate_obligations_ref(request: &Value) -> Result<(), String> {
    match request.get("obligations") {
        None | Some(Value::Null) => Ok(()),
        Some(Value::Obj(entries)) => {
            for (key, _) in entries {
                if !OBLIGATIONS_REF_FIELDS.contains(&key.as_str()) {
                    return Err(format!("unknown obligations field `{key}`"));
                }
            }
            let obligations = request.get("obligations").expect("checked above");
            let digest = obligations.str_field("digest")?;
            if !formats::is_digest(digest) {
                return Err(format!("invalid obligations digest `{digest}`"));
            }
            if obligations.get("path").and_then(Value::as_str).is_none() {
                return Err("missing obligations field `path`".to_string());
            }
            Ok(())
        }
        Some(_) => Err("`obligations` must be null or a {digest, path} reference".to_string()),
    }
}

/// Shape-validate the optional trusted transition record; semantic binding
/// (old/new digests against the loaded obligations) happens after the
/// obligations document is loaded.
pub(crate) fn validate_transition_shape(request: &Value) -> Result<(), String> {
    let transition = match request.get("transition") {
        None => return Ok(()),
        Some(t) => t,
    };
    let entries = match transition {
        Value::Obj(entries) => entries,
        _ => return Err("`transition` must be an object".to_string()),
    };
    for (key, _) in entries {
        if !TRANSITION_FIELDS.contains(&key.as_str()) {
            return Err(format!("unknown transition field `{key}`"));
        }
    }
    for field in ["old_digest", "new_digest"] {
        let digest = transition.str_field(field)?;
        if !formats::is_digest(digest) {
            return Err(format!("invalid transition `{field}` `{digest}`"));
        }
    }
    transition.str_field("reason")?;
    let consumers = transition
        .get("affected_consumers")
        .and_then(Value::as_arr)
        .ok_or("transition `affected_consumers` must be an array of strings")?;
    if consumers.iter().any(|c| c.as_str().is_none()) {
        return Err("transition `affected_consumers` must be an array of strings".to_string());
    }
    let authority = transition.get("authority").ok_or("missing transition field `authority`")?;
    let auth_entries = match authority {
        Value::Obj(entries) => entries,
        _ => return Err("transition `authority` must be an object".to_string()),
    };
    for (key, _) in auth_entries {
        if !AUTHORITY_FIELDS.contains(&key.as_str()) {
            return Err(format!("unknown transition authority field `{key}`"));
        }
    }
    let auth_digest = authority.str_field("digest")?;
    if !formats::is_digest(auth_digest) {
        return Err(format!("invalid transition authority digest `{auth_digest}`"));
    }
    authority.str_field("name")?;
    Ok(())
}

/// Load and fully validate the trusted obligations document: digest-verify
/// the bytes, then strictly shape each record (dup ids, unknown fields, and
/// unknown labels refuse as error-class input).
pub(crate) fn load_obligations(digest: &str, path: &str) -> Result<Vec<Obligation>, String> {
    let bytes = std::fs::read(path)
        .map_err(|e| format!("input-mismatch: obligations document unreadable at `{path}`: {e}"))?;
    let actual = formats::sha256_digest(&bytes);
    if actual != digest {
        return Err(format!(
            "input-mismatch: obligations document digest mismatch: reference names `{digest}` but the document hashes to `{actual}`"
        ));
    }
    let text = std::str::from_utf8(&bytes)
        .map_err(|e| format!("input-mismatch: obligations document is not UTF-8: {e}"))?;
    let doc = formats::parse(text)
        .map_err(|e| format!("input-mismatch: malformed obligations document: {e}"))?;
    if doc.str_field("version")? != LOCAL_VERSION {
        return Err(format!(
            "input-mismatch: unsupported obligations version `{}`; expected {LOCAL_VERSION}",
            doc.str_field("version")?
        ));
    }
    if doc.str_field("kind")? != "obligations" {
        return Err(format!(
            "input-mismatch: unsupported obligations kind `{}`",
            doc.str_field("kind")?
        ));
    }
    if let Value::Obj(entries) = &doc {
        for (key, _) in entries {
            if !matches!(key.as_str(), "version" | "kind" | "obligations") {
                return Err(format!("input-mismatch: unknown obligations document field `{key}`"));
            }
        }
    }
    let records = doc
        .get("obligations")
        .and_then(Value::as_arr)
        .ok_or("input-mismatch: obligations document has no obligations array")?;
    let mut out: Vec<Obligation> = Vec::new();
    for record in records {
        out.push(validate_obligation_record(record)?);
    }
    let mut seen: Vec<&str> = Vec::new();
    for o in &out {
        if seen.contains(&o.id.as_str()) {
            return Err(format!(
                "input-mismatch: duplicate obligation id `{}` in the obligations document",
                o.id
            ));
        }
        seen.push(&o.id);
    }
    Ok(out)
}

/// Strictly validate one obligation record.
fn validate_obligation_record(record: &Value) -> Result<Obligation, String> {
    let entries = match record {
        Value::Obj(entries) => entries,
        _ => return Err("input-mismatch: obligation record must be an object".to_string()),
    };
    for (key, _) in entries {
        if !OBLIGATION_FIELDS.contains(&key.as_str()) {
            return Err(format!("input-mismatch: unknown obligation field `{key}`"));
        }
    }
    let id = record.str_field("id")?.to_string();
    if id.is_empty() {
        return Err("input-mismatch: obligation id must not be empty".to_string());
    }
    let scope = record.str_field("scope")?.to_string();
    let origin = record.str_field("origin")?.to_string();
    if !matches!(origin.as_str(), "human" | "agent") {
        return Err(format!(
            "input-mismatch: unknown obligation origin `{origin}`; expected human or agent"
        ));
    }
    let state = record.str_field("state")?.to_string();
    if !matches!(state.as_str(), "accepted" | "proposed") {
        return Err(format!(
            "input-mismatch: unknown obligation state `{state}`; expected accepted or proposed"
        ));
    }
    let authority = record.get("authority").ok_or("input-mismatch: obligation has no authority")?;
    let auth_entries = match authority {
        Value::Obj(entries) => entries,
        _ => return Err("input-mismatch: obligation authority must be an object".to_string()),
    };
    for (key, _) in auth_entries {
        if !AUTHORITY_FIELDS.contains(&key.as_str()) {
            return Err(format!("input-mismatch: unknown obligation authority field `{key}`"));
        }
    }
    let auth_digest = authority.str_field("digest")?;
    if !formats::is_digest(auth_digest) {
        return Err(format!(
            "input-mismatch: invalid obligation authority digest `{auth_digest}`"
        ));
    }
    authority.str_field("name")?;
    let predicate = record.get("predicate").ok_or("input-mismatch: obligation has no predicate")?;
    let pred_entries = match predicate {
        Value::Obj(entries) => entries,
        _ => return Err("input-mismatch: obligation predicate must be an object".to_string()),
    };
    let kind = predicate.str_field("kind")?.to_string();
    match kind.as_str() {
        "structural" => {
            for (key, _) in pred_entries {
                if !matches!(key.as_str(), "kind" | "digest" | "contract") {
                    return Err(format!("input-mismatch: unknown structural predicate field `{key}`"));
                }
            }
            let digest = predicate.str_field("digest")?;
            if !formats::is_digest(digest) {
                return Err(format!("input-mismatch: invalid structural predicate digest `{digest}`"));
            }
            let contract = predicate
                .get("contract")
                .ok_or("input-mismatch: structural predicate has no contract record")?;
            if !matches!(contract, Value::Obj(_)) {
                return Err("input-mismatch: structural predicate contract must be an object".to_string());
            }
            let actual = formats::sha256_digest(formats::canonical(contract).as_bytes());
            if actual != digest {
                return Err(format!(
                    "input-mismatch: structural predicate digest mismatch: names `{digest}` but the contract record hashes to `{actual}`"
                ));
            }
            Ok(Obligation {
                id,
                scope,
                origin,
                state,
                kind: "structural",
                predicate_digest: digest.to_string(),
                contract: Some(contract.clone()),
                suite_digest: None,
            })
        }
        "law" => {
            for (key, _) in pred_entries {
                if !matches!(key.as_str(), "kind" | "suite_digest") {
                    return Err(format!("input-mismatch: unknown law predicate field `{key}`"));
                }
            }
            let suite_digest = predicate.str_field("suite_digest")?;
            if !formats::is_digest(suite_digest) {
                return Err(format!(
                    "input-mismatch: invalid law suite digest `{suite_digest}`"
                ));
            }
            Ok(Obligation {
                id,
                scope,
                origin,
                state,
                kind: "law",
                predicate_digest: suite_digest.to_string(),
                contract: None,
                suite_digest: Some(suite_digest.to_string()),
            })
        }
        other => Err(format!(
            "input-mismatch: unknown obligation predicate kind `{other}`; expected structural or law"
        )),
    }
}

/// Bind the transition to the loaded obligations: the replacement digest
/// must name exactly one accepted obligation, and the superseded digest must
/// differ from it and not still be accepted. Mismatches are trusted-side
/// configuration errors (error class).
pub(crate) fn finalize_transition(
    request: &Value,
    obligations: &[Obligation],
) -> Result<Option<Transition>, String> {
    let transition = match request.get("transition") {
        None | Some(Value::Null) => return Ok(None),
        Some(t) => t,
    };
    if obligations.is_empty() {
        return Err("input-mismatch: transition supplied without an obligations document".to_string());
    }
    let old_digest = transition.str_field("old_digest")?.to_string();
    let new_digest = transition.str_field("new_digest")?.to_string();
    if old_digest == new_digest {
        return Err("input-mismatch: transition old and new digests must differ".to_string());
    }
    let accepted: Vec<&Obligation> = obligations
        .iter()
        .filter(|o| o.state == "accepted")
        .collect();
    let matches: Vec<&Obligation> = accepted
        .iter()
        .filter(|o| o.predicate_digest == new_digest)
        .map(|o| *o)
        .collect();
    if matches.len() != 1 {
        return Err(format!(
            "input-mismatch: transition new digest `{new_digest}` does not name exactly one accepted obligation"
        ));
    }
    if accepted.iter().any(|o| o.predicate_digest == old_digest) {
        return Err(format!(
            "input-mismatch: transition old digest `{old_digest}` is still an accepted obligation's predicate"
        ));
    }
    Ok(Some(Transition {
        old_digest,
        new_digest,
        reason: transition.str_field("reason")?.to_string(),
        affected_consumers: transition
            .get("affected_consumers")
            .and_then(Value::as_arr)
            .expect("shape-validated")
            .iter()
            .map(|c| c.as_str().expect("shape-validated").to_string())
            .collect(),
        authority_digest: transition
            .get("authority")
            .expect("shape-validated")
            .str_field("digest")?
            .to_string(),
    }))
}

/// Build a full five-field diagnostic record for an obligation finding.
pub(crate) fn obligation_diagnostic(code: &str, severity: &str, reason: String) -> Value {
    formats::obj(vec![
        ("code", formats::s(code)),
        ("severity", formats::s(severity)),
        ("source", Value::Null),
        ("slots", formats::arr(Vec::new())),
        ("reason", formats::s(&reason)),
    ])
}

pub(crate) fn obligation_change(id: &str, change: &str) -> Value {
    formats::obj(vec![
        ("id", formats::s(id)),
        ("change", formats::s(change)),
    ])
}

/// Law-invocation inputs resolved and shape-validated from the check
/// request. All five are supplied as a complete set or not at all; they are
/// optional because checks without law obligations never execute suites.
pub(crate) struct LawInputsRaw {
    harnesses: Vec<(String, String)>,
    fixtures: Vec<(String, String)>,
    wall_ms: i64,
    seed: i64,
    evaluation_time: String,
}

/// Everything the retained-law execution path needs: the trusted base root
/// (supplies suite/harness/fixture bytes and the run's working directory),
/// the candidate side under test, the runner-derived commitment digests the
/// suite must echo, and the invocation inputs.
pub(crate) struct LawContext {
    base_root: String,
    cand_root: String,
    base_files: Vec<(String, String)>,
    cand_contract_digest: String,
    cand_commitment: String,
    inputs: LawInputsRaw,
}

/// A policy that requires law evidence cannot be satisfied by a proposed
/// obligation: the evidence requirement is unmet (Unknown contribution,
/// never an error) and the proposed obligation is still not enforced.
/// Returns the per-obligation finding reasons and the updated unknown flag.
pub(crate) fn law_required_findings(
    request: &Value,
    obligations: &[Obligation],
    consumer: &str,
    mut obl_unknown: bool,
) -> (Vec<String>, bool) {
    let mut reasons: Vec<String> = Vec::new();
    let requires_law = request
        .get("policy")
        .and_then(|p| p.get("law"))
        .and_then(Value::as_str)
        == Some("required");
    if requires_law {
        for o in obligations
            .iter()
            .filter(|o| o.kind == "law" && o.state == "proposed" && o.scope == consumer)
        {
            obl_unknown = true;
            reasons.push(format!(
                "policy requires law evidence but obligation `{}` is only proposed; it is not enforced and no accepted evidence exists",
                o.id
            ));
        }
    }
    (reasons, obl_unknown)
}

/// Assemble the retained-law execution context from the checked sides and
/// the parsed invocation inputs (the caller owns the commitment digests).
pub(crate) fn build_law_context(
    base_root: &str,
    cand_root: &str,
    base_files: Vec<(String, String)>,
    cand_contract_digest: String,
    cand_commitment: String,
    inputs: &LawInputsRaw,
) -> LawContext {
    LawContext {
        base_root: base_root.to_string(),
        cand_root: cand_root.to_string(),
        base_files,
        cand_contract_digest,
        cand_commitment,
        inputs: LawInputsRaw {
            harnesses: inputs.harnesses.clone(),
            fixtures: inputs.fixtures.clone(),
            wall_ms: inputs.wall_ms,
            seed: inputs.seed,
            evaluation_time: inputs.evaluation_time.clone(),
        },
    }
}

/// Bundle-relative path safety: no empty, absolute, dot, or dot-dot
/// components (mirrors the extraction reader's confinement rules).
fn is_safe_rel(rel: &str) -> bool {
    !rel.is_empty()
        && !rel.starts_with('/')
        && !rel.split('/').any(|c| c.is_empty() || c == "." || c == "..")
}

/// Shape-validate the optional law-invocation inputs (harnesses, fixtures,
/// budgets, environment, evaluation_time). Supplied as a complete set keyed
/// on `harnesses`; otherwise all four companions must be absent or null.
pub(crate) fn parse_law_inputs(request: &Value) -> Result<Option<LawInputsRaw>, String> {
    let supplied = |field: &str| {
        request
            .get(field)
            .map(|v| !matches!(v, Value::Null))
            .unwrap_or(false)
    };
    if !supplied("harnesses") {
        for field in ["fixtures", "budgets", "environment", "evaluation_time"] {
            if supplied(field) {
                return Err(format!(
                    "input-mismatch: `{field}` without `harnesses`: law invocation inputs are supplied as a complete set"
                ));
            }
        }
        return Ok(None);
    }
    let parse_file_map = |field: &str, max: Option<usize>| -> Result<Vec<(String, String)>, String> {
        let entries = match request.get(field) {
            Some(Value::Obj(entries)) => entries,
            _ => return Err(format!("input-mismatch: `{field}` must be an object of rel-path to digest")),
        };
        let mut out: Vec<(String, String)> = Vec::new();
        for (rel, digest) in entries {
            if !is_safe_rel(rel) {
                return Err(format!("input-mismatch: `{field}` path `{rel}` escapes the supplied bundle"));
            }
            let digest = digest
                .as_str()
                .ok_or_else(|| format!("input-mismatch: `{field}` digest for `{rel}` must be a string"))?;
            if !formats::is_digest(digest) {
                return Err(format!("input-mismatch: invalid `{field}` digest for `{rel}`"));
            }
            out.push((rel.clone(), digest.to_string()));
        }
        out.sort();
        if let Some(max) = max {
            if out.len() > max {
                return Err(format!(
                    "input-mismatch: `{field}` must name at most {max} artifact(s) in this slice"
                ));
            }
        }
        Ok(out)
    };
    let harnesses = parse_file_map("harnesses", Some(1))?[..].to_vec();
    if harnesses.is_empty() {
        return Err(
            "input-mismatch: `harnesses` must name the base-bound law harness when supplied"
                .to_string(),
        );
    }
    let fixtures = parse_file_map("fixtures", None)?;
    let budgets = match request.get("budgets") {
        Some(Value::Obj(entries)) => {
            if entries.len() != 1 || entries[0].0 != "wall_ms" {
                return Err(
                    "input-mismatch: `budgets` must carry exactly one field `wall_ms` in this slice"
                        .to_string(),
                );
            }
            let wall_ms = entries[0]
                .1
                .as_int()
                .ok_or("input-mismatch: `budgets.wall_ms` must be an integer")?;
            if !(1..=3_600_000).contains(&wall_ms) {
                return Err(format!(
                    "input-mismatch: `budgets.wall_ms` {wall_ms} is outside 1..=3600000"
                ));
            }
            wall_ms
        }
        _ => return Err("input-mismatch: `budgets` must be an object with `wall_ms`".to_string()),
    };
    let seed = match request.get("environment") {
        Some(Value::Obj(entries)) => {
            if entries.len() != 1 || entries[0].0 != "seed" {
                return Err(
                    "input-mismatch: `environment` must carry exactly one field `seed` in this slice"
                        .to_string(),
                );
            }
            entries[0]
                .1
                .as_int()
                .filter(|s| *s >= 0)
                .ok_or("input-mismatch: `environment.seed` must be a non-negative integer")?
        }
        _ => return Err("input-mismatch: `environment` must be an object with `seed`".to_string()),
    };
    let evaluation_time = request
        .str_field("evaluation_time")
        .map_err(|_| "input-mismatch: `evaluation_time` must be a string".to_string())?
        .to_string();
    let valid = evaluation_time.len() == 20
        && evaluation_time.ends_with('Z')
        && evaluation_time.as_bytes()[10] == b'T'
        && evaluation_time
            .bytes()
            .enumerate()
            .all(|(i, b)| matches!(i, 4 | 7 | 10 | 13 | 16 | 19) || b.is_ascii_digit());
    if !valid {
        return Err(format!(
            "input-mismatch: `evaluation_time` `{evaluation_time}` is not a UTC RFC3339 timestamp with second precision and Z suffix"
        ));
    }
    Ok(Some(LawInputsRaw {
        harnesses,
        fixtures,
        wall_ms: budgets,
        seed,
        evaluation_time,
    }))
}

/// Load the base-bound harness document: digest-verify against the base
/// bundle, then strictly shape it (local-1, kind law-harness, name only).
fn load_harness(base_root: &str, rel: &str, digest: &str) -> Result<String, String> {
    let path = std::path::Path::new(base_root).join(rel);
    let bytes = std::fs::read(&path)
        .map_err(|e| format!("input-mismatch: harness document unreadable at `{}`: {e}", path.display()))?;
    let actual = formats::sha256_digest(&bytes);
    if actual != digest {
        return Err(format!(
            "input-mismatch: harness digest mismatch: reference names `{digest}` but the document hashes to `{actual}`"
        ));
    }
    let text = std::str::from_utf8(&bytes)
        .map_err(|_| "input-mismatch: harness document is not UTF-8".to_string())?;
    let doc = formats::parse(text)
        .map_err(|e| format!("input-mismatch: malformed harness document: {e}"))?;
    if let Value::Obj(entries) = &doc {
        for (key, _) in entries {
            if !matches!(key.as_str(), "version" | "kind" | "name") {
                return Err(format!("input-mismatch: unknown harness document field `{key}`"));
            }
        }
    }
    if doc.str_field("version")? != LOCAL_VERSION {
        return Err(format!(
            "input-mismatch: unsupported harness version `{}`; expected {LOCAL_VERSION}",
            doc.str_field("version")?
        ));
    }
    if doc.str_field("kind")? != "law-harness" {
        return Err(format!(
            "input-mismatch: unsupported harness kind `{}`; expected law-harness",
            doc.str_field("kind")?
        ));
    }
    Ok(doc.str_field("name")?.to_string())
}

/// Execute one retained law obligation through the sandboxed runner.
/// Without invocation inputs the retained suite carries no execution
/// evidence (law-retained-inconclusive unknown); with inputs, every
/// invocation binding is verified against the trusted base before the
/// runner runs, and operational runner failures propagate as errors.
fn run_retained_law(
    law: Option<&LawContext>,
    id: &str,
    suite_digest: &str,
) -> Result<LawOutcome, String> {
    let Some(law) = law else {
        return Ok(LawOutcome {
            verdict: "law-retained-inconclusive",
            method: None,
            status: None,
            witness: None,
            reason: Some(
                "no law invocation inputs supplied; the retained suite was not executed"
                    .to_string(),
            ),
            result_digest: None,
            contract_digest: None,
            artifact_digest: None,
            harness_digest: None,
            runs: 0,
        });
    };
    let bound = |rel: &str, digest: &str, what: &str| {
        if !law
            .base_files
            .iter()
            .any(|(b_rel, b_digest)| b_rel == rel && b_digest == digest)
        {
            return Err(format!(
                "input-mismatch: {what} `{rel}` does not bind the trusted base: digest `{digest}` is absent from the base bundle"
            ));
        }
        Ok(())
    };
    let (harness_rel, harness_digest) = &law.inputs.harnesses[0];
    bound(harness_rel, harness_digest, "harness")?;
    for (rel, digest) in &law.inputs.fixtures {
        bound(rel, digest, "fixture")?;
    }
    let _harness_name = load_harness(&law.base_root, harness_rel, harness_digest)?;
    let suite_rel = law
        .base_files
        .iter()
        .filter(|(_, d)| d == suite_digest)
        .map(|(rel, _)| rel.clone())
        .min()
        .ok_or_else(|| {
            format!("input-mismatch: law obligation `{id}` suite digest `{suite_digest}` absent from the base bundle")
        })?;
    let suite_path = std::path::Path::new(&law.base_root).join(&suite_rel);
    let inputs = crate::harness::LawInputs {
        harness_rel: harness_rel.clone(),
        harness_digest: harness_digest.clone(),
        fixture_files: law.inputs.fixtures.clone(),
        wall_ms: law.inputs.wall_ms,
        seed: law.inputs.seed,
        evaluation_time: law.inputs.evaluation_time.clone(),
    };
    let mut outcome = crate::harness::run_law(
        &suite_path,
        suite_digest,
        &law.cand_contract_digest,
        &law.cand_root,
        &law.cand_commitment,
        &law.base_root,
        &inputs,
    )?;
    // runner-derived bindings carried into the law evidence record
    if outcome.result_digest.is_some() {
        outcome.contract_digest = Some(law.cand_contract_digest.clone());
        outcome.artifact_digest = Some(law.cand_commitment.clone());
        outcome.harness_digest = Some(harness_digest.clone());
    }
    Ok(outcome)
}

/// Build one `law_methods` evidence entry from a law outcome.
fn law_method_entry(id: &str, suite_digest: &str, outcome: &LawOutcome) -> Value {
    let text = |v: &Option<String>| v.clone().map(|t| formats::s(&t)).unwrap_or(Value::Null);
    formats::obj(vec![
        ("obligation_id", formats::s(id)),
        ("suite_digest", formats::s(suite_digest)),
        ("method", text(&outcome.method)),
        ("status", text(&outcome.status)),
        ("witness", text(&outcome.witness)),
        ("reason", text(&outcome.reason)),
        ("result_digest", text(&outcome.result_digest)),
        ("contract", text(&outcome.contract_digest)),
        ("implementation_artifact", text(&outcome.artifact_digest)),
        ("harness", text(&outcome.harness_digest)),
        ("runs", formats::i(outcome.runs as i64)),
    ])
}

/// Evaluate accepted and proposed obligations against the candidate;
/// returns the obligation entries, reported changes, slots covered by an
/// accepted replacement, law evidence entries, and the definite/unknown
/// flags. Binding failures of the obligations document itself (stale docs
/// that no longer describe the trusted base) are error-class refusals.
#[allow(clippy::type_complexity, clippy::too_many_arguments)]
pub(crate) fn evaluate_obligations(
    obligations: &[Obligation],
    transition: Option<&Transition>,
    consumer: &str,
    base: &ExtractionOutcome,
    candidate: &ExtractionOutcome,
    base_digests: &[String],
    cand_digests: &[String],
    law: Option<&LawContext>,
) -> Result<(Vec<Value>, Vec<Value>, Vec<String>, Vec<Value>, bool, bool), String> {
    let base_slots = contract_slots(&base.contract)?;
    let cand_slots = contract_slots(&candidate.contract)?;
    let mut entries: Vec<Value> = Vec::new();
    let mut changes: Vec<Value> = Vec::new();
    let mut covered: Vec<String> = Vec::new();
    let mut methods: Vec<Value> = Vec::new();
    let mut definite = false;
    let mut unknown = false;
    for o in obligations {
        let (binding, verdict): (&str, &str) = if o.state == "proposed" {
            // proposed obligations are reported, never enforced
            ("none", "proposed")
        } else if o.scope != consumer {
            ("none", "out-of-scope")
        } else {
            let candidate_bound = transition
                .map(|t| t.new_digest == o.predicate_digest)
                .unwrap_or(false);
            match o.kind {
                "structural" => {
                    let contract = o.contract.as_ref().expect("validated structural");
                    let obl_slots = contract_slots(contract)?;
                    if candidate_bound {
                        // the accepted replacement binds the candidate: the
                        // candidate contract must carry every bound slot with
                        // the exact accepted type
                        let all_match = obl_slots.iter().all(|s| {
                            cand_slots
                                .iter()
                                .find(|c| c.name == s.name)
                                .map(|c| formats::canonical(&c.ty) == formats::canonical(&s.ty))
                                .unwrap_or(false)
                        });
                        if all_match {
                            covered.extend(obl_slots.iter().map(|s| s.name.clone()));
                            ("candidate", "transition-accepted")
                        } else {
                            definite = true;
                            changes.push(obligation_change(
                                &o.id,
                                "proposed-weakening",
                            ));
                            ("candidate", "weakened")
                        }
                    } else {
                        // the obligation was authored against the trusted
                        // base: exact-type binding is a document precondition
                        for s in &obl_slots {
                            let bound = base_slots
                                .iter()
                                .find(|b| b.name == s.name)
                                .map(|b| formats::canonical(&b.ty) == formats::canonical(&s.ty))
                                .unwrap_or(false);
                            if !bound {
                                return Err(format!(
                                    "input-mismatch: obligation `{}` does not bind the trusted base: slot `{}` is missing or typed differently in the base contract",
                                    o.id, s.name
                                ));
                            }
                        }
                        // candidate side: accretion against the accepted types
                        let all_accrete = obl_slots.iter().all(|s| {
                            cand_slots
                                .iter()
                                .find(|c| c.name == s.name)
                                .map(|c| is_subtype(&c.ty, &s.ty))
                                .unwrap_or(false)
                        });
                        if all_accrete {
                            ("base", "pass")
                        } else {
                            definite = true;
                            changes.push(obligation_change(
                                &o.id,
                                "proposed-weakening",
                            ));
                            ("base", "weakened")
                        }
                    }
                }
                "law" => {
                    let suite_digest = o.suite_digest.as_ref().expect("validated law");
                    if !base_digests.iter().any(|d| d == suite_digest) {
                        return Err(format!(
                            "input-mismatch: law obligation `{}` does not bind the trusted base: suite digest `{}` is absent from the base bundle",
                            o.id, suite_digest
                        ));
                    }
                    if cand_digests.iter().any(|d| d == suite_digest) {
                        // retained: execute the bound suite against the
                        // candidate when invocation inputs exist; without
                        // them (or with unrunnable bytes) there is no
                        // execution evidence and the result stays unknown
                        let outcome = run_retained_law(law, &o.id, suite_digest)?;
                        if outcome.verdict == "law-counterexample" {
                            definite = true;
                        } else if outcome.verdict != "law-pass" {
                            unknown = true;
                        }
                        methods.push(law_method_entry(&o.id, suite_digest, &outcome));
                        ("base", outcome.verdict)
                    } else {
                        // the candidate dropped the accepted suite bytes
                        definite = true;
                        changes.push(obligation_change(&o.id, "proposed-deletion"));
                        ("base", "law-deleted")
                    }
                }
                other => unreachable!("validated obligation kind {other}"),
            }
        };
        entries.push(formats::obj(vec![
            ("id", formats::s(&o.id)),
            ("scope", formats::s(&o.scope)),
            ("origin", formats::s(&o.origin)),
            ("state", formats::s(&o.state)),
            ("kind", formats::s(o.kind)),
            ("predicate_digest", formats::s(&o.predicate_digest)),
            ("binding", formats::s(binding)),
            ("verdict", formats::s(verdict)),
        ]));
    }
    Ok((entries, changes, covered, methods, definite, unknown))
}


/// Build the invocation commitment record: enforcement is always local
/// (never independent CI enforcement). Without law execution the
/// harness/fixture/budget/evaluation-time fields stay explicit nulls; with
/// executed laws they carry the real supplied bindings plus the enforced
/// sandbox capabilities (decided in the mh5.4 review: nulls become real
/// digests once law execution runs).
pub(crate) fn invocation_commitment_value(
    request: &Value,
    checker_digest: &str,
    base_facts_digest: &str,
    candidate_facts_digest: &str,
    law_inputs: Option<&LawInputsRaw>,
) -> Value {
    let file_map = |entries: &[(String, String)]| {
        formats::obj(
            entries
                .iter()
                .map(|(rel, digest)| (rel.as_str(), formats::s(digest)))
                .collect(),
        )
    };
    let (harnesses, fixtures, budgets, environment, evaluation_time, sandbox) =
        match law_inputs {
            None => (
                Value::Null,
                Value::Null,
                Value::Null,
                Value::Null,
                Value::Null,
                Value::Null,
            ),
            Some(inputs) => {
                let caps = crate::harness::sandbox_caps();
                let sandbox = formats::obj(vec![
                    ("enforced", Value::Bool(caps.enforced)),
                    (
                        "landlock_abi",
                        caps.landlock_abi.map(formats::i).unwrap_or(Value::Null),
                    ),
                    ("network", formats::s("denied")),
                    ("writes", formats::s("denied")),
                    (
                        "reads",
                        formats::s("supplied bundles and the system runtime"),
                    ),
                    (
                        "rlimits",
                        formats::arr(
                            ["fsize=0", "nofile=64", "nproc=128", "as=512MiB", "cpu=wall-derived"]
                                .iter()
                                .map(|r| formats::s(r))
                                .collect(),
                        ),
                    ),
                    ("wall_ms", formats::i(inputs.wall_ms)),
                    ("environment", formats::s("fixed")),
                ]);
                (
                    file_map(&inputs.harnesses),
                    file_map(&inputs.fixtures),
                    formats::obj(vec![("wall_ms", formats::i(inputs.wall_ms))]),
                    formats::obj(vec![("seed", formats::i(inputs.seed))]),
                    formats::s(&inputs.evaluation_time),
                    sandbox,
                )
            }
        };
    formats::obj(vec![
        ("enforcement", formats::s("local")),
        (
            "obligations_digest",
            request
                .get("obligations")
                .and_then(|o| o.str_field("digest").ok())
                .map(formats::s)
                .unwrap_or(Value::Null),
        ),
        ("checker_digest", formats::s(checker_digest)),
        (
            "policy",
            request.get("policy").cloned().unwrap_or(Value::Null),
        ),
        ("base_facts_digest", formats::s(base_facts_digest)),
        (
            "candidate_facts_digest",
            formats::s(candidate_facts_digest),
        ),
        ("harnesses", harnesses),
        ("fixtures", fixtures),
        ("budgets", budgets),
        ("environment", environment),
        ("evaluation_time", evaluation_time),
        ("sandbox", sandbox),
    ])
}

