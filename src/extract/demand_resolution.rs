// Purpose: Demand-resolution stamping for the rust-cargo-local-1
//   extractor (beads wild-adc, change add-on-absent-fallible).
// Responsibilities: Cross-check every demand entry against the supplied
//   provider slots — unresolved demand is a completeness gap unless the
//   entry sits under a declared `on_absent` path, where it is stamped as a
//   scoped fallible-absence outcome instead — and resolve consumer demand
//   entries to required in-slots carrying the declared absence policy.
// Rationale: Merely scanning identifier strings never establishes
//   resolution; the absent-handling stamp lives here so the clause is
//   contract-level while the slot stays required, never silently resolved
//   and never exempt from validation.

use std::collections::{BTreeMap, BTreeSet};

use super::{conveyed_scope, Diagnostic, SlotRecord};
use crate::formats::{self, Value};

/// Cross-check every demand entry against the supplied provider slots.
/// Merely scanning identifier strings never establishes resolution: a
/// demand whose target is absent from the provider's declared inventory
/// (removed, renamed, private, or unsupported-signature slot) is a
/// completeness gap, never a silently resolved in-slot — unless the entry
/// sits under a declared `on_absent` path (wild-adc), where the unresolved
/// demand is stamped as a scoped fallible-absence outcome and the slot
/// stays required.
pub(super) fn check_demand_resolution(
    all_slots: &[SlotRecord],
    all_demand: &mut [Value],
    on_absent: &[String],
    diagnostics: &mut Vec<Diagnostic>,
    complete: &mut bool,
) {
    let meanings: BTreeSet<&str> = all_slots.iter().map(|s| s.meaning.as_str()).collect();
    for entry in all_demand.iter_mut() {
        // a conveyed entry is claimed, not refused: its scoped claim already
        // records the forwarded path (wild-hyk), so it never marks the
        // inventory incomplete
        if entry.get("conveyed").and_then(Value::as_bool) == Some(true) {
            continue;
        }
        // an absent entry is a declared fallible-absence outcome, not a
        // gap (wild-adc): the outside world lacking the fact is a value
        // outcome the consumer handles, never an inventory hole
        if entry.get("absent").and_then(Value::as_bool) == Some(true) {
            continue;
        }
        let called = entry.str_field("called").unwrap_or_default();
        let provider_slot = entry.str_field("provider_slot").unwrap_or_default();
        if !meanings.contains(provider_slot) {
            // a demanded slot absent from the supplied inventory under a
            // declared on_absent path is a handled value outcome (wild-adc):
            // stamp the scoped fallible-absence outcome instead of refusing
            if let Some(scope) = conveyed_scope(on_absent, called) {
                if let Value::Obj(fields) = entry {
                    if !fields.iter().any(|(k, _)| k == "on_absent") {
                        fields.push(("on_absent".to_string(), formats::s("fallible")));
                    }
                    if !fields.iter().any(|(k, _)| k == "scope") {
                        fields.push(("scope".to_string(), formats::s(&scope)));
                    }
                    fields.push(("absent".to_string(), Value::Bool(true)));
                }
                continue;
            }
            diagnostics.push(Diagnostic {
                code: "incomplete-demand",
                severity: "error",
                source: None,
                reason: format!(
                    "demand `{called}` does not resolve to a supplied provider slot; the consumer cannot be checked complete"
                ),
            });
            *complete = false;
        }
    }
}

/// Resolve consumer demand entries to provider slots as in-slots.
pub(super) fn resolve_in_slots(
    all_slots: &[SlotRecord],
    all_demand: &[Value],
) -> Result<Vec<SlotRecord>, String> {
    let by_meaning: BTreeMap<&str, &SlotRecord> =
        all_slots.iter().map(|s| (s.meaning.as_str(), s)).collect();
    let mut in_slots: Vec<SlotRecord> = Vec::new();
    for entry in all_demand {
        let consumer = entry.str_field("consumer")?;
        let provider_slot = entry.str_field("provider_slot")?;
        let slot_name = format!(
            "{consumer}::demand::{}",
            by_meaning
                .get(provider_slot)
                .map(|s| s.name.as_str())
                .unwrap_or(provider_slot)
        );
        if in_slots.iter().any(|s| s.name == slot_name) {
            continue;
        }
        // The declared absence policy rides on the demand entry (wild-adc):
        // the contract slot carries it so the clause is contract-level.
        let on_absent = match entry.get("on_absent").and_then(Value::as_str) {
            Some(value) => Some(value.to_string()),
            None => None,
        };
        let ty = match by_meaning.get(provider_slot) {
            Some(record) => record.ty.clone(),
            None => formats::obj(vec![
                ("shape", formats::s("opaque")),
                (
                    "fingerprint",
                    formats::s(&formats::sha256_digest(provider_slot.as_bytes())),
                ),
            ]),
        };
        in_slots.push(SlotRecord {
            name: slot_name,
            meaning: provider_slot.to_string(),
            ty,
            on_absent,
        });
    }
    Ok(in_slots)
}
