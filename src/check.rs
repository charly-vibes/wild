// Purpose: Scoped structural checking for the wild extractor (beads
//   wild-mh5.2, wild-mh5.3, wild-mh5.4).
// Responsibilities: Validate local-1 check requests (strict field whitelist,
//   fixed policy literal, trusted obligations reference, optional trusted
//   transition record, checker identity, law-invocation inputs, bundle
//   confinement on both sides), reuse the rust-cargo-local-1 extraction over
//   the committed base and candidate bundles, judge the named consumer's
//   demanded provider slots under v1 accretion subtyping (new output is a
//   subtype of the old; opaque inventories are unknown, never broken),
//   enforce accepted obligations from a trusted external document against
//   the candidate — structural predicates must accrete and retained law
//   suites are executed against the actual candidate artifact through the
//   sandboxed law runner (harness.rs) whenever the five law-invocation
//   inputs (harnesses, fixtures, budgets, environment, evaluation_time) are
//   supplied — and assemble the check-report record with per-slot verdicts,
//   obligation verdicts, per-side extraction summaries, method-labelled law
//   evidence, and stable diagnostics.
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
//   becomes bare compatibility. Law execution (wild-mh5.4, decided in the
//   interactive review D1-D10): the runner executes the digest-bound suite
//   twice under enforced isolation (Landlock denies network and writes,
//   rlimits and a wall deadline bound the suite) and echo-validates the
//   suite's v1 law_result stdout against runner-derived digests; malformed
//   or mismatching stdout, wall timeout, crash, nondeterminism, and
//   proof/exhaustive methods all yield inconclusive evidence (never sampled
//   pass), a witnessed sampled counterexample is a definite Reject, a
//   twice-repeated sampled pass contributes a pass, and suite bytes that
//   cannot be run as a program or an unsupplied invocation carry no
//   execution evidence (law-retained-inconclusive unknown). A policy that
//   requires law evidence while the only matching obligation is proposed
//   yields Unknown, never an error. The report labels enforcement as local
//   (never independent CI enforcement), records the enforced sandbox
//   capabilities, and fills the harness/fixture/budget/evaluation-time
//   commitment fields with the real supplied values once laws execute.

use crate::extract::{self, ExtractionOutcome, LOCAL_VERSION, PROFILE};
use crate::obligations::{
    build_law_context,
    evaluate_obligations,
    finalize_transition,
    invocation_commitment_value,
    load_obligations,
    obligation_diagnostic,
    parse_law_inputs,
    validate_obligations_ref,
    validate_transition_shape,
    law_required_findings,
    Obligation,
};
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
    "harnesses",
    "fixtures",
    "budgets",
    "environment",
    "evaluation_time",
];

const POLICY_LITERAL_FIELDS: &[&str] = &["structural", "law"];

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

pub(crate) struct SlotInfo {
    pub(crate) name: String,
    pub(crate) ty: Value,
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
pub(crate) fn contract_slots(contract: &Value) -> Result<Vec<SlotInfo>, String> {
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
pub(crate) fn is_subtype(a: &Value, b: &Value) -> bool {
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

/// Assemble the check diagnostics: extraction diagnostics from both sides,
/// unauthorized obligation changes, and the law-evidence inconclusive
/// aggregate plus per-obligation policy findings.
fn assemble_diagnostics(
    base: &ExtractionOutcome,
    candidate: &ExtractionOutcome,
    obl_changes: &[Value],
    law_methods: &[Value],
    law_required_reasons: Vec<String>,
    obl_unknown: bool,
) -> Vec<Value> {
    let mut diagnostics: Vec<Value> = Vec::new();
    diagnostics.extend(base.diagnostics.iter().cloned());
    diagnostics.extend(candidate.diagnostics.iter().cloned());
    for change in obl_changes {
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
        let reasons: Vec<String> = law_methods
            .iter()
            .filter(|m| {
                let status = m.get("status").and_then(Value::as_str).unwrap_or("");
                status != "pass" && status != "counterexample"
            })
            .map(|m| {
                format!(
                    "`{}`: {}",
                    m.str_field("obligation_id").unwrap_or_default(),
                    m.str_field("reason").unwrap_or("no diagnostic reason")
                )
            })
            .collect();
        if !reasons.is_empty() {
            diagnostics.push(obligation_diagnostic(
                "law-inconclusive",
                "warning",
                format!("law evidence is inconclusive: {}", reasons.join("; ")),
            ));
        }
    }
    for reason in law_required_reasons {
        diagnostics.push(obligation_diagnostic("law-inconclusive", "warning", reason));
    }
    diagnostics
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

    // Runner-derived commitment digests the executed law results must echo:
    // the boundary contract digest comes from the candidate extraction and
    // the implementation-artifact digest is the candidate bundle commitment
    // (sha256 over the canonical per-file digest map — path-independent).
    let cand_files_value = formats::obj(
        cand_files
            .iter()
            .map(|(rel, digest)| (rel.as_str(), formats::s(digest)))
            .collect(),
    );
    let cand_commitment = formats::sha256_digest(formats::canonical(&cand_files_value).as_bytes());

    let law_inputs = parse_law_inputs(request)?;
    let law = law_inputs.as_ref().map(|inputs| {
        build_law_context(
            &base_root,
            &cand_root,
            base_files.clone(),
            formats::sha256_digest(&cand_contract_bytes),
            cand_commitment.clone(),
            inputs,
        )
    });

    let (obl_entries, obl_changes, covered, law_methods, obl_definite, obl_unknown) =
        evaluate_obligations(
            &obligations,
            transition.as_ref(),
            &consumer,
            &base,
            &candidate,
            &base_files.iter().map(|(_, d)| d.clone()).collect::<Vec<_>>(),
            &cand_files.iter().map(|(_, d)| d.clone()).collect::<Vec<_>>(),
            law.as_ref(),
        )?;
    // A policy that requires law evidence cannot be satisfied by a proposed
    // obligation: the evidence requirement is unmet (Unknown), never an
    // error, and the proposed obligation is still not enforced.
    let (law_required_reasons, obl_unknown) = law_required_findings(
        request,
        &obligations,
        &consumer,
        obl_unknown,
    );

    let diagnostics = assemble_diagnostics(
        &base,
        &candidate,
        &obl_changes,
        &law_methods,
        law_required_reasons,
        obl_unknown,
    );

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
        ("law_methods", formats::arr(law_methods)),
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
            invocation_commitment_value(
                request,
                &checker_digest,
                &formats::sha256_digest(&base_contract_bytes),
                &formats::sha256_digest(&cand_contract_bytes),
                law_inputs.as_ref(),
            ),
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
