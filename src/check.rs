// Purpose: Scoped structural checking for the wild extractor (beads
//   wild-mh5.2, wild-mh5.3).
// Responsibilities: Validate local-1 check requests (strict field whitelist,
//   fixed policy literal, trusted obligations reference, optional trusted
//   transition record, checker identity, bundle confinement on both sides),
//   reuse the rust-cargo-local-1 extraction over the committed base and
//   candidate bundles, judge the named consumer's demanded provider slots
//   under v1 accretion subtyping (new output is a subtype of the old; opaque
//   inventories are unknown, never broken), enforce accepted obligations from
//   a trusted external document against the candidate, and assemble the
//   check-report record with per-slot verdicts, obligation verdicts, per-side
//   extraction summaries, empty law methods, and stable diagnostics.
// Rationale: The slices' named semantics — decided in interactive review and
//   evaluated with typed advisory judgments — are a whole-crate boundary
//   (every resolved base demand plus every candidate-side unresolved demand
//   blocks acceptance; per-slot narrowing is deferred), extracted fact
//   records published under the requested report location as part of the
//   report contract, and a schema-validated fixed policy literal.
//   Protected-context semantics (wild-mh5.3, TypeSafe-decided): the
//   check-request binds a trusted external obligations document by {digest,
//   path} — the candidate never supplies or selects accepted context. Each
//   accepted obligation is evaluated against the candidate: structural
//   predicates must accrete, law suite bytes must be retained (a retained
//   law without execution evidence stays law-inconclusive unknown; a deleted
//   law is a definite weakening). An optional trusted transition record
//   authorizes an old-to-new obligation change and yields the
//   accepted-intentional-change disposition, never backward-compatibility
//   success. A definite structural counterexample (demanded slot removed or
//   a visible signature break) takes precedence over unrelated gaps, with
//   both reported; unknown evidence never becomes a break and a break never
//   becomes bare compatibility. The report labels enforcement as local
//   (never independent CI enforcement) and carries explicit nulls for
//   harness/fixture/budget/evaluation-time commitments deferred to later
//   slices.

use crate::extract::{self, ExtractionOutcome, LOCAL_VERSION, PROFILE};
use crate::formats::{self, Value};

const CHECK_REQUEST_FIELDS: &[&str] = &[
    "version",
    "kind",
    "profile",
    "consumer",
    "base",
    "candidate",
    "target",
    "toolchain",
    "features",
    "policy",
    "obligations",
    "checker",
    "transition",
];

const POLICY_LITERAL_FIELDS: &[&str] = &["structural"];

const OBLIGATIONS_REF_FIELDS: &[&str] = &["digest", "path"];
const OBLIGATION_FIELDS: &[&str] = &[
    "id",
    "scope",
    "origin",
    "state",
    "authority",
    "predicate",
];
const AUTHORITY_FIELDS: &[&str] = &["name", "digest"];
const TRANSITION_FIELDS: &[&str] = &[
    "old_digest",
    "new_digest",
    "reason",
    "affected_consumers",
    "authority",
];

/// One validated obligation record from the trusted obligations document.
struct Obligation {
    id: String,
    scope: String,
    origin: String,
    state: String,
    kind: &'static str,
    predicate_digest: String,
    /// Structural predicate's inline contract record (digest-bound).
    contract: Option<Value>,
    /// Law predicate's executable suite content digest.
    suite_digest: Option<String>,
}

/// A validated externally authorized old-to-new obligation transition.
struct Transition {
    old_digest: String,
    new_digest: String,
    reason: String,
    affected_consumers: Vec<String>,
    authority_digest: String,
}

impl Transition {
    fn to_value(&self) -> Value {
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

pub struct CheckOutcome {
    pub report: Value,
    pub decision: &'static str,
    pub assurance: &'static str,
    pub exit_code: i32,
    pub diagnostics: Vec<Value>,
    pub demanded: Vec<String>,
    pub coverage: (i64, i64),
    /// Extracted fact records for both sides, as (relative path, canonical
    /// bytes) under the requested report location's facts/ subdirectories:
    /// `base/contract.json`, `base/demand.json`, `base/provenance.json`, and
    /// the same for `candidate/`. These are part of the declared report
    /// contract so verdicts stay independently inspectable.
    pub facts: Vec<(String, String)>,
}

struct SlotInfo {
    name: String,
    ty: Value,
}

/// Validate the check request envelope shape; return the parsed sides and
/// checker identity. Every refusal is an error-class input.
fn validate_check_request(
    request: &Value,
) -> Result<(String, (String, Vec<(String, String)>), (String, Vec<(String, String)>), String), String>
{
    if request.str_field("version")? != LOCAL_VERSION {
        return Err(format!(
            "unsupported protocol version `{}`; expected {LOCAL_VERSION}",
            request.str_field("version")?
        ));
    }
    if request.str_field("kind")? != "check-request" {
        return Err(format!(
            "unsupported record kind `{}` for check",
            request.str_field("kind")?
        ));
    }
    if request.str_field("profile")? != PROFILE {
        return Err(format!(
            "unsupported profile `{}`; expected {PROFILE}",
            request.str_field("profile")?
        ));
    }
    if let Value::Obj(entries) = request {
        for (key, _) in entries {
            if !CHECK_REQUEST_FIELDS.contains(&key.as_str()) {
                return Err(format!("unknown request field `{key}`"));
            }
        }
    }
    let consumer = request.str_field("consumer")?.to_string();
    let base = validate_side(request, "base")?;
    let candidate = validate_side(request, "candidate")?;
    validate_build_context(request)?;
    validate_policy(request)?;
    validate_obligations_ref(request)?;
    validate_transition_shape(request)?;
    let checker = request.get("checker").ok_or("missing field `checker`")?;
    if let Value::Obj(entries) = checker {
        for (key, _) in entries {
            if !matches!(key.as_str(), "name" | "digest") {
                return Err(format!("unknown checker field `{key}`"));
            }
        }
        let digest = checker.str_field("digest")?;
        if !formats::is_digest(digest) {
            return Err(format!("invalid checker digest `{digest}`"));
        }
        checker.str_field("name")?;
    } else {
        return Err("`checker` must be an object".to_string());
    }
    Ok((
        consumer,
        base,
        candidate,
        checker.str_field("digest")?.to_string(),
    ))
}

/// Strictly validate one committed bundle side: only bundle_root and files,
/// with digests and confinement enforced exactly as extraction does.
fn validate_side(request: &Value, side: &str) -> Result<(String, Vec<(String, String)>), String> {
    let side_value = request.get(side).ok_or_else(|| format!("missing field `{side}`"))?;
    let entries = match side_value {
        Value::Obj(entries) => entries,
        _ => return Err(format!("`{side}` must be an object")),
    };
    for (key, _) in entries {
        if !matches!(key.as_str(), "bundle_root" | "files") {
            return Err(format!("unknown `{side}` field `{key}`"));
        }
    }
    let bundle_root = side_value.str_field("bundle_root")?.to_string();
    let files_obj = side_value.get("files").ok_or_else(|| format!("missing `{side}` field `files`"))?;
    let files = match files_obj {
        Value::Obj(file_entries) => {
            let mut out = Vec::new();
            for (rel, digest_value) in file_entries {
                let digest = digest_value
                    .as_str()
                    .ok_or("file digests must be strings")?;
                if !formats::is_digest(digest) {
                    return Err(format!("invalid digest for `{rel}`"));
                }
                out.push((rel.clone(), digest.to_string()));
            }
            out
        }
        _ => return Err(format!("`{side}` field `files` must be an object")),
    };
    Ok((bundle_root, files))
}

/// target/toolchain/features must be present and well-typed; the synthetic
/// extraction requests re-validate them against the extraction rules.
fn validate_build_context(request: &Value) -> Result<(), String> {
    for field in ["target", "toolchain"] {
        if request.get(field).and_then(Value::as_str).is_none() {
            return Err(format!("missing string field `{field}`"));
        }
    }
    let features = request
        .get("features")
        .and_then(Value::as_arr)
        .ok_or("missing array field `features`")?;
    if features.iter().any(|f| f.as_str().is_none()) {
        return Err("features must be an array of strings".to_string());
    }
    Ok(())
}

/// The policy field is a schema-validated fixed literal in this slice:
/// accretion is the only structural rule the checker implements. Pinning is
/// implicit in the request document until the trusted-invocation slice.
fn validate_policy(request: &Value) -> Result<(), String> {
    let policy = request.get("policy").ok_or("missing field `policy`")?;
    let entries = match policy {
        Value::Obj(entries) => entries,
        _ => return Err("`policy` must be an object".to_string()),
    };
    for (key, _) in entries {
        if !POLICY_LITERAL_FIELDS.contains(&key.as_str()) {
            return Err(format!("unknown policy field `{key}`"));
        }
    }
    if policy.str_field("structural")? != "accretion" {
        return Err(format!(
            "unsupported structural policy `{}`; this slice implements accretion only",
            policy.str_field("structural")?
        ));
    }
    Ok(())
}

/// The obligations field is either absent/null (no authored obligations yet)
/// or a strict reference {digest, path} naming a trusted external document.
/// The candidate never supplies or selects this context.
fn validate_obligations_ref(request: &Value) -> Result<(), String> {
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
fn validate_transition_shape(request: &Value) -> Result<(), String> {
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
fn load_obligations(digest: &str, path: &str) -> Result<Vec<Obligation>, String> {
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
fn finalize_transition(
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
fn obligation_diagnostic(code: &str, severity: &str, reason: String) -> Value {
    formats::obj(vec![
        ("code", formats::s(code)),
        ("severity", formats::s(severity)),
        ("source", Value::Null),
        ("slots", formats::arr(Vec::new())),
        ("reason", formats::s(&reason)),
    ])
}

fn obligation_change(id: &str, change: &str) -> Value {
    formats::obj(vec![
        ("id", formats::s(id)),
        ("change", formats::s(change)),
    ])
}

/// Evaluate the loaded obligations against the trusted base and the
/// candidate. Returns (report entries, obligation changes, slot names whose
/// breaks a passing transition supersedes, definite-failure flag,
/// unknown-evidence flag). Binding failures of the obligations document
/// itself (stale docs that no longer describe the trusted base) are
/// error-class refusals.
#[allow(clippy::type_complexity)]
fn evaluate_obligations(
    obligations: &[Obligation],
    transition: Option<&Transition>,
    consumer: &str,
    base: &ExtractionOutcome,
    candidate: &ExtractionOutcome,
    base_digests: &[String],
    cand_digests: &[String],
) -> Result<(Vec<Value>, Vec<Value>, Vec<String>, bool, bool), String> {
    let base_slots = contract_slots(&base.contract)?;
    let cand_slots = contract_slots(&candidate.contract)?;
    let mut entries: Vec<Value> = Vec::new();
    let mut changes: Vec<Value> = Vec::new();
    let mut covered: Vec<String> = Vec::new();
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
                        // retained law, no execution evidence: stays unknown
                        unknown = true;
                        ("base", "law-retained-inconclusive")
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
    Ok((entries, changes, covered, definite, unknown))
}

/// Build the synthetic extraction request for one committed side so the
/// extraction path re-validates digests, confinement, and build context.
fn synthetic_extraction_request(
    request: &Value,
    _side: &str,
    bundle_root: &str,
    files: &[(String, String)],
) -> Value {
    let mut file_pairs: Vec<(String, Value)> = Vec::new();
    for (rel, digest) in files {
        file_pairs.push((rel.clone(), formats::s(digest)));
    }
    formats::obj(vec![
        ("version", formats::s(LOCAL_VERSION)),
        ("kind", formats::s("extraction-request")),
        ("profile", formats::s(PROFILE)),
        ("bundle_root", formats::s(bundle_root)),
        (
            "files",
            Value::Obj(file_pairs.into_iter().map(|(k, v)| (k, v)).collect()),
        ),
        (
            "target",
            formats::s(request.str_field("target").unwrap_or_default()),
        ),
        (
            "toolchain",
            formats::s(request.str_field("toolchain").unwrap_or_default()),
        ),
        (
            "features",
            request
                .get("features")
                .cloned()
                .unwrap_or(formats::arr(Vec::new())),
        ),
        (
            "extractor",
            request
                .get("checker")
                .cloned()
                .unwrap_or(formats::obj(vec![("name", formats::s("wild"))])),
        ),
    ])
}

/// Extract the visible slot inventory from one side's contract record.
fn contract_slots(contract: &Value) -> Result<Vec<SlotInfo>, String> {
    let slots = contract
        .get("slots")
        .and_then(Value::as_arr)
        .ok_or("contract record has no slots array")?;
    let mut out = Vec::new();
    for slot in slots {
        let name = slot.str_field("name")?.to_string();
        let ty = slot
            .get("type")
            .cloned()
            .ok_or_else(|| format!("slot `{name}` has no type"))?;
        out.push(SlotInfo { name, ty });
    }
    Ok(out)
}

/// v1 value-set subtyping over the extractor's type vocabulary: identical
/// scalar spelling with interval containment, function contravariance in
/// arguments and covariance in results, and opaque types comparable only by
/// identical fingerprint.
fn is_subtype(a: &Value, b: &Value) -> bool {
    if !matches!(a, Value::Obj(_)) || !matches!(b, Value::Obj(_)) {
        return false;
    }
    let shape_a = a.str_field("shape").unwrap_or_default();
    let shape_b = b.str_field("shape").unwrap_or_default();
    if shape_a != shape_b {
        return false;
    }
    match shape_a {
        "scalar" => {
            if a.str_field("name").unwrap_or_default() != b.str_field("name").unwrap_or_default() {
                return false;
            }
            match (a.get("min"), a.get("max"), b.get("min"), b.get("max")) {
                (Some(am), Some(ax), Some(bm), Some(bx)) => {
                    am.as_int().unwrap_or_default() >= bm.as_int().unwrap_or_default()
                        && ax.as_int().unwrap_or_default() <= bx.as_int().unwrap_or_default()
                }
                (None, None, None, None) => true,
                _ => false,
            }
        }
        "function" => {
            let (Some(args_a), Some(args_b)) = (
                a.get("arguments").and_then(Value::as_arr),
                b.get("arguments").and_then(Value::as_arr),
            ) else {
                return false;
            };
            if args_a.len() != args_b.len() {
                return false;
            }
            args_b
                .iter()
                .zip(args_a.iter())
                .all(|(ba, aa)| is_subtype(ba, aa))
                && is_subtype(
                    a.get("result").unwrap_or(&Value::Null),
                    b.get("result").unwrap_or(&Value::Null),
                )
        }
        "opaque" => {
            a.str_field("fingerprint").unwrap_or_default()
                == b.str_field("fingerprint").unwrap_or_default()
        }
        _ => false,
    }
}

fn is_visible(ty: &Value) -> bool {
    matches!(
        ty.str_field("shape").unwrap_or_default(),
        "scalar" | "function"
    )
}

/// Demanded slot verdicts for the named consumer's base demand set.
fn judge_slots(
    consumer: &str,
    base: &ExtractionOutcome,
    candidate: &ExtractionOutcome,
) -> Result<(Vec<Value>, Vec<String>, i64, i64, bool), String> {
    let base_slots = contract_slots(&base.contract)?;
    let cand_slots = contract_slots(&candidate.contract)?;

    let base_demand = base
        .demand
        .get("entries")
        .and_then(Value::as_arr)
        .ok_or("base demand record has no entries array")?;
    let mut demanded_calls: Vec<String> = Vec::new();
    for entry in base_demand {
        if entry.str_field("consumer")? == consumer {
            let called = entry.str_field("called")?.to_string();
            if !demanded_calls.contains(&called) {
                demanded_calls.push(called);
            }
        }
    }
    demanded_calls.sort();

    let mut verdicts = Vec::new();
    let mut demanded_names = Vec::new();
    let mut passed: i64 = 0;
    let mut definite_break = false;
    let mut type_unknown = false;
    for called in &demanded_calls {
        let base_ty = base_slots
            .iter()
            .find(|s| &s.name == called)
            .map(|s| s.ty.clone());
        let cand_ty = cand_slots
            .iter()
            .find(|s| &s.name == called)
            .map(|s| s.ty.clone());
        demanded_names.push(called.clone());
        let (verdict, reason, base_type_field, cand_type_field);
        match (&base_ty, &cand_ty) {
            (Some(bt), Some(ct)) => {
                if !is_visible(ct) || !is_visible(bt) {
                    verdict = "unknown";
                    reason = "demanded slot inventory is opaque on at least one side; the type relationship cannot be established".to_string();
                    type_unknown = true;
                    base_type_field = Some(bt.clone());
                    cand_type_field = Some(ct.clone());
                } else if is_subtype(ct, bt) {
                    verdict = "pass";
                    reason = "demanded slot retained with an accreting output type".to_string();
                    passed += 1;
                    base_type_field = Some(bt.clone());
                    cand_type_field = Some(ct.clone());
                } else {
                    verdict = "broken";
                    reason = "demanded slot type does not accrete from base to candidate under v1 subtyping".to_string();
                    definite_break = true;
                    base_type_field = Some(bt.clone());
                    cand_type_field = Some(ct.clone());
                }
            }
            (Some(_), None) => {
                verdict = "removed";
                reason = "demanded slot is absent from the candidate contract inventory".to_string();
                definite_break = true;
                base_type_field = base_ty.clone();
                cand_type_field = None;
            }
            (None, Some(ct)) => {
                verdict = "unknown";
                reason = "demanded slot is absent from the base contract inventory".to_string();
                type_unknown = true;
                base_type_field = None;
                cand_type_field = Some(ct.clone());
            }
            (None, None) => {
                verdict = "unknown";
                reason = "demanded slot is absent from both contract inventories".to_string();
                type_unknown = true;
                base_type_field = None;
                cand_type_field = None;
            }
        }
        let mut fields: Vec<(&str, Value)> = Vec::new();
        fields.push(("called", formats::s(called)));
        fields.push(("verdict", formats::s(verdict)));
        fields.push(("reason", formats::s(&reason)));
        fields.push((
            "base_type",
            base_type_field.unwrap_or(Value::Null),
        ));
        fields.push((
            "candidate_type",
            cand_type_field.unwrap_or(Value::Null),
        ));
        verdicts.push(formats::obj(fields));
    }
    Ok((
        verdicts,
        demanded_names,
        passed,
        demanded_calls.len() as i64,
        definite_break || type_unknown,
    ))
}

fn side_summary(
    bundle_root: &str,
    outcome: &ExtractionOutcome,
    contract_bytes: &[u8],
) -> Value {
    formats::obj(vec![
        ("bundle_root", formats::s(bundle_root)),
        (
            "complete_inventory",
            Value::Bool(outcome.complete_inventory),
        ),
        (
            "diagnostics",
            formats::arr(outcome.diagnostics.clone()),
        ),
        (
            "facts_digest",
            formats::s(&formats::sha256_digest(contract_bytes)),
        ),
        (
            "demand_count",
            formats::i(
                outcome
                    .demand
                    .get("entries")
                    .and_then(Value::as_arr)
                    .map(|e| e.len() as i64)
                    .unwrap_or(0),
            ),
        ),
    ])
}

/// Check one validated request; `Err` classifies as error (exit 2).
pub fn check(request: &Value) -> Result<CheckOutcome, String> {
    let (consumer, (base_root, base_files), (cand_root, cand_files), checker_digest) =
        validate_check_request(request)?;
    let obligations: Vec<Obligation> = match request.get("obligations") {
        None | Some(Value::Null) => Vec::new(),
        Some(Value::Obj(_)) => {
            let digest = request
                .get("obligations")
                .and_then(|o| o.str_field("digest").ok())
                .unwrap_or_default()
                .to_string();
            let path = request
                .get("obligations")
                .and_then(|o| o.get("path").and_then(Value::as_str))
                .unwrap_or_default()
                .to_string();
            load_obligations(&digest, &path)?
        }
        Some(_) => return Err("`obligations` must be null or a {digest, path} reference".to_string()),
    };
    let transition = finalize_transition(request, &obligations)?;
    let base_request = synthetic_extraction_request(request, "base", &base_root, &base_files);
    let cand_request =
        synthetic_extraction_request(request, "candidate", &cand_root, &cand_files);
    let base = extract::extract(&base_request)?;
    let candidate = extract::extract(&cand_request)?;

    let (verdicts, demanded_names, passed, total, _has_break_or_unknown) =
        judge_slots(&consumer, &base, &candidate)?;

    let base_contract_bytes = formats::canonical(&base.contract).into_bytes();
    let cand_contract_bytes = formats::canonical(&candidate.contract).into_bytes();

    let (obl_entries, obl_changes, covered, obl_definite, obl_unknown) =
        evaluate_obligations(
            &obligations,
            transition.as_ref(),
            &consumer,
            &base,
            &candidate,
            &base_files.iter().map(|(_, d)| d.clone()).collect::<Vec<_>>(),
            &cand_files.iter().map(|(_, d)| d.clone()).collect::<Vec<_>>(),
        )?;

    let mut diagnostics: Vec<Value> = Vec::new();
    diagnostics.extend(base.diagnostics.iter().cloned());
    diagnostics.extend(candidate.diagnostics.iter().cloned());
    for change in &obl_changes {
        diagnostics.push(obligation_diagnostic(
            "obligation-change",
            "error",
            format!(
                "unauthorized obligation change: `{}` reported as {}",
                change.str_field("id").unwrap_or_default(),
                change.str_field("change").unwrap_or_default()
            ),
        ));
    }
    if obl_unknown {
        diagnostics.push(obligation_diagnostic(
            "law-inconclusive",
            "warning",
            "a retained law has no execution evidence in this slice; its result stays inconclusive until genuinely checked".to_string(),
        ));
    }

    // The scoped claim rests on declaration visibility: a side whose
    // inventory is incomplete (unsupported constructs, unsupplied or
    // external dep demand) cannot ground a compatibility claim, so any gap
    // on either side withholds acceptance — gaps are explicit and
    // uncuring. A definite structural counterexample still takes
    // precedence over unrelated gaps, with both reported; unknown evidence
    // never becomes a break and a break never becomes bare compatibility.
    // Accepted obligations are enforced against the candidate regardless of
    // any candidate-sourced weakening: a passing authorized transition
    // supersedes the per-slot break on exactly the slots its accepted
    // replacement obligation binds; everything else stays definite.
    let has_side_gap = !base.complete_inventory || !candidate.complete_inventory;
    let any_removed_or_broken = verdicts.iter().any(|v| {
        let verdict = v.str_field("verdict").unwrap_or_default();
        (verdict == "removed" || verdict == "broken")
            && !v
                .str_field("called")
                .map(|called| covered.iter().any(|c| c == called))
                .unwrap_or(false)
    });
    let any_type_unknown = verdicts
        .iter()
        .any(|v| v.str_field("verdict").unwrap_or_default() == "unknown");
    let (decision, assurance): (&'static str, &'static str) =
        if obl_definite || any_removed_or_broken {
            ("refuse", "Reject")
        } else if has_side_gap || any_type_unknown || obl_unknown {
            ("refuse", "Unknown")
        } else {
            ("accept", "PassDeclared")
        };
    let transition_applied = transition.is_some()
        && obl_entries
            .iter()
            .any(|e| e.str_field("verdict").unwrap_or_default() == "transition-accepted");
    let disposition = if transition_applied && decision == "accept" {
        "accepted-intentional-change"
    } else {
        "compatible"
    };
    let exit_code = if decision == "accept" { 0 } else { 1 };

    let report = formats::obj(vec![
        ("version", formats::s(LOCAL_VERSION)),
        ("kind", formats::s("check-report")),
        ("profile", formats::s(PROFILE)),
        ("consumer", formats::s(&consumer)),
        (
            "policy",
            request.get("policy").cloned().unwrap_or(Value::Null),
        ),
        ("law_methods", formats::arr(Vec::new())),
        (
            "base",
            side_summary(&base_root, &base, &base_contract_bytes),
        ),
        (
            "candidate",
            side_summary(&cand_root, &candidate, &cand_contract_bytes),
        ),
        ("demanded_slots", formats::arr(verdicts)),
        ("obligations", formats::arr(obl_entries)),
        ("obligation_changes", formats::arr(obl_changes)),
        (
            "transition",
            transition.as_ref().map(|t| t.to_value()).unwrap_or(Value::Null),
        ),
        (
            "invocation_commitment",
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
                ("checker_digest", formats::s(&checker_digest)),
                (
                    "policy",
                    request.get("policy").cloned().unwrap_or(Value::Null),
                ),
                (
                    "base_facts_digest",
                    formats::s(&formats::sha256_digest(&base_contract_bytes)),
                ),
                (
                    "candidate_facts_digest",
                    formats::s(&formats::sha256_digest(&cand_contract_bytes)),
                ),
                ("harnesses", Value::Null),
                ("fixtures", Value::Null),
                ("budgets", Value::Null),
                ("evaluation_time", Value::Null),
            ]),
        ),
        ("disposition", formats::s(disposition)),
        ("decision", formats::s(decision)),
        ("assurance", formats::s(assurance)),
        ("diagnostics", formats::arr(diagnostics.clone())),
    ]);

    let mut facts: Vec<(String, String)> = Vec::new();
    for (side, outcome) in [("base", &base), ("candidate", &candidate)] {
        facts.push((
            format!("{side}/contract.json"),
            formats::canonical(&outcome.contract),
        ));
        facts.push((
            format!("{side}/demand.json"),
            formats::canonical(&outcome.demand),
        ));
        facts.push((
            format!("{side}/provenance.json"),
            formats::canonical(&outcome.provenance),
        ));
    }

    Ok(CheckOutcome {
        report,
        decision,
        assurance,
        exit_code,
        diagnostics,
        demanded: demanded_names,
        coverage: (passed, total),
        facts,
    })
}
