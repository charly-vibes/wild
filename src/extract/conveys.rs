// Purpose: The conveys clause validation and scoping for the wild
//   extractor (beads wild-hyk, change add-conveys-clause).
// Responsibilities: Validate an optional `conveys` declaration — a sorted,
//   duplicate-free array of input path identifiers in the v1 id grammar —
//   shared by extraction and check requests, and resolve which declared
//   path covers a demand target so unknown input slots at declared paths
//   record a scoped conveyance claim instead of the demand refusal.
// Rationale: A pass-through component (proxy, pipe, middleware) routes
//   input it never interprets; the declared clause narrows what is
//   interpreted, never what is validated — the claim never exempts
//   scoped_substitution, so newly introduced required inputs still refuse.

use crate::formats::Value;

/// Validate an optional `conveys` clause: a sorted, duplicate-free array of
/// input path identifiers (beads wild-hyk). Declared paths forward unknown
/// input slots instead of interpreting them; the grammar and set ordering
/// match the v1 contract format so the clause round-trips between a
/// contract document and the requests that carry its declared paths.
pub(crate) fn validate_conveys(value: Option<&Value>) -> Result<Vec<String>, String> {
    let Some(value) = value else {
        return Ok(Vec::new());
    };
    let items = match value {
        Value::Arr(items) => items,
        _ => return Err("`conveys` must be an array of input path strings".to_string()),
    };
    let mut paths: Vec<String> = Vec::new();
    for item in items {
        let path = item
            .as_str()
            .ok_or("`conveys` entries must be input path strings")?;
        if !crate::v1::id_syntax(path) {
            return Err(format!("invalid conveys input path `{path}`"));
        }
        if let Some(previous) = paths.last() {
            if previous == path {
                return Err(format!("duplicate conveys input path `{path}`"));
            }
            if previous.as_str() > path {
                return Err("conveys input paths must be sorted".to_string());
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
