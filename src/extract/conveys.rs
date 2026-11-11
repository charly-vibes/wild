// Purpose: The declared-path clause validation and scoping for the wild
//   extractor (beads wild-hyk, change add-conveys-clause; wild-adc,
//   change add-on-absent-fallible).
// Responsibilities: Validate an optional declared-path clause — a sorted,
//   duplicate-free array of input path identifiers in the v1 id grammar —
//   shared by extraction and check requests (`conveys`, `on_absent`), and
//   resolve which declared path covers a demand target so unknown input
//   slots at declared paths record a scoped claim instead of the demand
//   refusal.
// Rationale: A pass-through component (proxy, pipe, middleware) routes
//   input it never interprets, and a consumer may declare absence at a
//   slot a handled value outcome; the declared clauses narrow what is
//   interpreted or refused-for-absence, never what is validated — neither
//   claim exempts scoped_substitution, so newly introduced required
//   inputs still refuse.

use crate::formats::Value;

/// Validate an optional `conveys` clause (beads wild-hyk).
pub(crate) fn validate_conveys(value: Option<&Value>) -> Result<Vec<String>, String> {
    validate_path_clause(value, "conveys")
}

/// Validate an optional `on_absent` clause (beads wild-adc).
pub(crate) fn validate_on_absent(value: Option<&Value>) -> Result<Vec<String>, String> {
    validate_path_clause(value, "on_absent")
}

/// Validate an optional declared-path clause: a sorted, duplicate-free
/// array of input path identifiers. Declared paths forward unknown input
/// slots (conveys) or make their absence a handled value outcome
/// (on_absent: fallible) instead of a demand refusal; the grammar and set
/// ordering match the v1 contract format so the clause round-trips between
/// a contract document and the requests that carry its declared paths.
fn validate_path_clause(value: Option<&Value>, field: &str) -> Result<Vec<String>, String> {
    let Some(value) = value else {
        return Ok(Vec::new());
    };
    let items = match value {
        Value::Arr(items) => items,
        _ => {
            return Err(format!("`{field}` must be an array of input path strings"))
        }
    };
    let mut paths: Vec<String> = Vec::new();
    for item in items {
        let path = item
            .as_str()
            .ok_or_else(|| format!("`{field}` entries must be input path strings"))?;
        if !crate::v1::id_syntax(path) {
            return Err(format!("invalid {field} input path `{path}`"));
        }
        if let Some(previous) = paths.last() {
            if previous == path {
                return Err(format!("duplicate {field} input path `{path}`"));
            }
            if previous.as_str() > path {
                return Err(format!("{field} input paths must be sorted"));
            }
        }
        paths.push(path.to_string());
    }
    Ok(paths)
}

/// The declared conveys path covering `target`, if any: the target equals
/// the declared path or sits underneath it in the `::` path namespace.
pub(crate) fn conveyed_scope(conveys: &[String], target: &str) -> Option<String> {
    conveys
        .iter()
        .find(|p| target == p.as_str() || target.starts_with(&format!("{p}::")))
        .cloned()
}
