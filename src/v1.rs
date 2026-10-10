// Purpose: v1 wire-document canonical reader, semantic schema validation for
//   `contract` documents, and the conservative subtype/accretion checkers
//   (beads wild-3rr bounded slice).
// Responsibilities: Read a v1 wire document with the strict grammar already
//   provided by wild::formats (duplicate keys, floats, BOM, leading zeros,
//   out-of-exact-range integers are refused), enforce `schema_version: "1"`
//   and a supported kind, semantically validate `contract` documents against
//   docs/wild-formats-v1.md (slot/tombstone name uniqueness, polarity and
//   facet enums, required outputs, integer interval ordering, defaults that
//   inhabit their declared type, law-id uniqueness, sorted set arrays),
//   and implement the v1 subtype table and the accretion rules as a
//   three-valued conservative verdict (Holds / Breaks / Unknown).
// Rationale: The format document states that a conforming reader validates
//   both the structural schema and the semantic rules, and that unknown
//   versions, kinds, and failed semantic checks are refused with a
//   diagnostic rather than silently accepted. This slice covers the
//   contract kind; remaining wire kinds keep their kind-unsupported
//   refusal so no partial document can receive a complete assurance
//   claim. `subtype` returns Unknown whenever the conservative rules
//   cannot establish inclusion, never a guess.

use crate::formats::{self, Value};

pub const KINDS: [&str; 20] = [
    "contract",
    "manifest",
    "assembly",
    "lock",
    "sidecar",
    "law_result",
    "observation",
    "attestation",
    "policy",
    "certificate",
    "adapter",
    "envelope",
    "live_snapshot",
    "lease",
    "baseline",
    "extractor_report",
    "publication",
    "log_entry",
    "registry_proof",
    "bundle",
];

const FACETS: [&str; 8] = [
    "api",
    "abi",
    "layout",
    "serialization",
    "behavior",
    "dialect",
    "environment",
    "license",
];

/// Conservative three-valued subtype verdict.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Verdict {
    Holds,
    Breaks,
    Unknown,
}

/// Read failure classification: malformed input and unknown versions are
/// caller errors; an unknown kind is a refusal of the named kind.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum ReadError {
    Malformed(String),
    MissingField(&'static str),
    UnknownVersion(String),
    UnknownKind(String),
}

/// Read a canonical v1 wire document. Malformed JSON, unknown schema
/// versions, and unknown kinds are input errors / refusals, never partial
/// successes.
pub fn read_document(text: &str) -> Result<Value, ReadError> {
    let value = formats::parse(text).map_err(ReadError::Malformed)?;
    let version = value
        .str_field("schema_version")
        .map_err(|_| ReadError::MissingField("schema_version"))?;
    if version != "1" {
        return Err(ReadError::UnknownVersion(version.to_string()));
    }
    let kind = value
        .str_field("kind")
        .map_err(|_| ReadError::MissingField("kind"))?;
    if !KINDS.contains(&kind) {
        return Err(ReadError::UnknownKind(kind.to_string()));
    }
    Ok(value)
}

/// Validate a `contract` document's semantic rules. Returns the sorted list
/// of stable diagnostic codes on failure.
pub fn validate_contract(value: &Value) -> Result<(), Vec<String>> {
    let mut codes: Vec<String> = Vec::new();
    let mut push = |c: &str| {
        if !codes.iter().any(|existing| existing == c) {
            codes.push(c.to_string());
        }
    };
    let slots = value.get("slots").and_then(Value::as_arr).unwrap_or(&[]);
    let tombstones = value.get("tombstones").and_then(Value::as_arr).unwrap_or(&[]);
    let laws = value.get("laws").and_then(Value::as_arr).unwrap_or(&[]);
    let relations = value.get("relations").and_then(Value::as_arr).unwrap_or(&[]);
    let sunsets = value.get("sunsets").and_then(Value::as_arr).unwrap_or(&[]);

    // Slot names are unique across slots and tombstones.
    let mut names: Vec<&str> = Vec::new();
    for slot in slots.iter().chain(tombstones.iter()) {
        if let Ok(name) = slot.str_field("name") {
            if names.contains(&name) {
                push("slot-name-duplicate");
            }
            names.push(name);
        }
    }
    // Set ordering: slots and tombstones by name, laws by id, relations by
    // id, sunsets by date then slot name. Repeated set keys are rejected.
    if !sorted_by_key(slots, |s| s.str_field("name").unwrap_or_default().to_string())
        || !sorted_by_key(tombstones, |s| s.str_field("name").unwrap_or_default().to_string())
        || !sorted_by_key(laws, |l| l.str_field("id").unwrap_or_default().to_string())
        || !sorted_by_key(relations, |r| r.str_field("id").unwrap_or_default().to_string())
        || !sorted_by_key(sunsets, |s| {
            format!(
                "{}|{}",
                s.str_field("at").unwrap_or_default(),
                s.str_field("slot").unwrap_or_default()
            )
        })
    {
        push("set-order");
    }
    for slot in slots {
        validate_slot(slot, false, &mut push);
    }
    for tombstone in tombstones {
        validate_slot(tombstone, true, &mut push);
    }
    let mut law_ids: Vec<&str> = Vec::new();
    for law in laws {
        if let Ok(id) = law.str_field("id") {
            if law_ids.contains(&id) {
                push("law-id-duplicate");
            }
            law_ids.push(id);
        }
        if let Ok(digest) = law.str_field("suite_digest") {
            if !is_digest(digest) {
                push("digest-syntax");
            }
        }
    }
    if codes.is_empty() {
        Ok(())
    } else {
        codes.sort();
        Err(codes)
    }
}

fn sorted_by_key(items: &[Value], key: impl Fn(&Value) -> String) -> bool {
    let mut keys = Vec::new();
    for item in items {
        let k = key(item);
        if keys.last() == Some(&k) {
            return false;
        }
        keys.push(k);
    }
    keys.windows(2).all(|w| w[0] <= w[1])
}

fn is_digest(text: &str) -> bool {
    formats::is_digest(text)
}

fn is_id(text: &str) -> bool {
    let mut chars = text.chars();
    let first_ok = matches!(
        chars.next(),
        Some('A'..='Z') | Some('a'..='z') | Some('_')
    );
    first_ok
        && text.len() <= 256
        && text
            .chars()
            .all(|c| matches!(c, 'A'..='Z' | 'a'..='z' | '0'..='9' | '_' | '.' | ':' | '/' | '-'))
}

fn validate_slot(slot: &Value, tombstone: bool, push: &mut impl FnMut(&str)) {
    let name = slot.str_field("name").unwrap_or_default();
    if !is_id(name) {
        push("id-syntax");
    }
    if !is_id(slot.str_field("meaning").unwrap_or_default()) {
        push("id-syntax");
    }
    let polarity = slot.str_field("polarity").unwrap_or_default();
    if polarity != "in" && polarity != "out" {
        push("polarity-unknown");
    }
    let required = slot.get("required").and_then(Value::as_bool);
    if tombstone {
        // Tombstones are former input slots: they retain their last
        // accepted meaning and type as inputs.
        if polarity != "in" {
            push("tombstone-polarity");
        }
        if required == Some(true) {
            push("tombstone-required");
        }
    } else {
        // Outputs must be required.
        if polarity == "out" && required != Some(true) {
            push("output-required");
        }
    }
    let facet = slot.str_field("facet").unwrap_or_default();
    if !FACETS.contains(&facet) {
        push("facet-unknown");
    }
    let mut path = String::new();
    if let Err(code) = validate_type(&slot_type(slot), &mut path) {
        push(&code);
    }
    if let Err(code) = validate_default(slot.get("default"), &slot_type(slot)) {
        push(&code);
    }
}

fn slot_type(slot: &Value) -> Value {
    slot.get("type").cloned().unwrap_or(Value::Null)
}

/// Validate a type value's structural semantics. Returns a diagnostic code
/// on the first violation found.
fn validate_type(ty: &Value, path: &mut String) -> Result<(), String> {
    let shape = ty.str_field("shape").unwrap_or_default();
    match shape {
        "scalar" => {
            let name = ty.str_field("name").unwrap_or_default();
            if !matches!(name, "unit" | "boolean" | "string" | "bytes" | "integer") {
                return Err("scalar-unknown".to_string());
            }
            if name == "integer" {
                let min = ty.get("min").and_then(Value::as_int);
                let max = ty.get("max").and_then(Value::as_int);
                match (min, max) {
                    (Some(min), Some(max)) => {
                        if min > max {
                            return Err("integer-interval".to_string());
                        }
                    }
                    _ => return Err("integer-interval".to_string()),
                }
            }
            Ok(())
        }
        "record" => {
            let fields = ty.get("fields").cloned().unwrap_or(Value::Null);
            let Value::Obj(entries) = &fields else {
                return Err("type-shape".to_string());
            };
            let mut names: Vec<&String> = entries.iter().map(|(k, _)| k).collect();
            names.sort();
            if names.windows(2).any(|w| w[0] == w[1]) {
                return Err("field-name-duplicate".to_string());
            }
            for (_, field) in entries {
                let field_type = field.get("type").cloned().unwrap_or(Value::Null);
                validate_type(&field_type, path)?;
            }
            Ok(())
        }
        "sum" => {
            let variants = ty.get("variants").cloned().unwrap_or(Value::Null);
            let Value::Obj(entries) = &variants else {
                return Err("type-shape".to_string());
            };
            for (_, variant) in entries {
                validate_type(variant, path)?;
            }
            Ok(())
        }
        "sequence" => {
            interval(ty)?;
            let items = ty.get("items").cloned().unwrap_or(Value::Null);
            validate_type(&items, path)
        }
        "map" => {
            interval(ty)?;
            validate_type(&ty.get("keys").cloned().unwrap_or(Value::Null), path)?;
            validate_type(&ty.get("values").cloned().unwrap_or(Value::Null), path)
        }
        "function" => {
            let arguments = ty.get("arguments").and_then(Value::as_arr).unwrap_or(&[]);
            for argument in arguments {
                validate_type(argument, path)?;
            }
            validate_type(&ty.get("result").cloned().unwrap_or(Value::Null), path)
        }
        "opaque" => {
            let fingerprint = ty.str_field("fingerprint").unwrap_or_default();
            if !is_digest(&fingerprint) {
                return Err("digest-syntax".to_string());
            }
            Ok(())
        }
        _ => Err("type-shape".to_string()),
    }
}

fn interval(ty: &Value) -> Result<(), String> {
    let min = ty.get("min").and_then(Value::as_int);
    let max = ty.get("max").and_then(Value::as_int);
    match (min, max) {
        (Some(min), Some(max)) if min >= 0 && min <= max => Ok(()),
        _ => Err("cardinality-interval".to_string()),
    }
}

/// A default value must inhabit its declared type.
fn validate_default(def: Option<&Value>, ty: &Value) -> Result<(), String> {
    let Some(def) = def else {
        return Err("default-missing".to_string());
    };
    let present = def.get("present").and_then(Value::as_bool);
    match present {
        Some(false) => Ok(()),
        Some(true) => {
            let value = def.get("value").cloned().unwrap_or(Value::Null);
            if inhabits(&value, ty) {
                Ok(())
            } else {
                Err("default-type-mismatch".to_string())
            }
        }
        None => Err("default-missing".to_string()),
    }
}

fn inhabits(value: &Value, ty: &Value) -> bool {
    match ty.str_field("shape").unwrap_or_default() {
        "scalar" => {
            let name = ty.str_field("name").unwrap_or_default();
            match name {
                "unit" => matches!(value, Value::Null),
                "boolean" => matches!(value, Value::Bool(_)),
                "string" => matches!(value, Value::Str(_)),
                "bytes" => match value {
                    Value::Obj(entries) => {
                        entries.len() == 1
                            && entries[0].0 == "base64"
                            && matches!(&entries[0].1, Value::Str(b64) if is_canonical_base64(b64))
                    }
                    _ => false,
                },
                "integer" => match value {
                    Value::Int(int) => match (ty.get("min").and_then(Value::as_int), ty.get("max").and_then(Value::as_int)) {
                        (Some(min), Some(max)) => *int >= min && *int <= max,
                        _ => false,
                    },
                    _ => false,
                },
                _ => false,
            }
        }
        "record" => match value {
            Value::Obj(entries) => {
                let fields = ty.get("fields").cloned().unwrap_or(Value::Null);
                let Value::Obj(field_entries) = &fields else {
                    return false;
                };
                entries.iter().all(|(name, field_value)| {
                    field_entries
                        .iter()
                        .find(|(field_name, _)| field_name == name)
                        .map(|(_, field)| {
                            inhabits(field_value, &field.get("type").cloned().unwrap_or(Value::Null))
                        })
                        .unwrap_or(false)
                })
            }
            _ => false,
        },
        "sum" => match value {
            Value::Obj(entries) if entries.len() == 1 => {
                let variants = ty.get("variants").cloned().unwrap_or(Value::Null);
                let Value::Obj(variant_entries) = &variants else {
                    return false;
                };
                let (label, payload) = &entries[0];
                match variant_entries.iter().find(|(name, _)| name == label) {
                    Some((_, variant_ty)) => inhabits(payload, variant_ty),
                    None => {
                        // Open sums accept unknown labels as opaque payloads.
                        ty.get("open")
                            .and_then(Value::as_bool)
                            .unwrap_or(false)
                            && matches!(payload, Value::Obj(_) | Value::Str(_) | Value::Arr(_) | Value::Int(_) | Value::Bool(_) | Value::Null)
                    }
                }
            }
            _ => false,
        },
        "sequence" => match value {
            Value::Arr(items) => {
                let min = ty.get("min").and_then(Value::as_int).unwrap_or(0);
                let max = ty.get("max").and_then(Value::as_int).unwrap_or(i64::MAX);
                items.len() as i64 >= min
                    && items.len() as i64 <= max
                    && items
                        .iter()
                        .all(|item| inhabits(item, &ty.get("items").cloned().unwrap_or(Value::Null)))
            }
            _ => false,
        },
        "map" => match value {
            Value::Obj(entries) => {
                let min = ty.get("min").and_then(Value::as_int).unwrap_or(0);
                let max = ty.get("max").and_then(Value::as_int).unwrap_or(i64::MAX);
                (entries.len() as i64).ge(&min)
                    && (entries.len() as i64).le(&max)
                    && entries.iter().all(|(_key, item)| {
                        // v1 map keys are JSON strings; only a string key
                        // domain can admit JSON object keys.
                        let keys_ty = ty.get("keys").cloned().unwrap_or(Value::Null);
                        keys_ty.str_field("shape").unwrap_or_default() == "scalar"
                            && keys_ty.str_field("name").unwrap_or_default() == "string"
                            && inhabits(item, &ty.get("values").cloned().unwrap_or(Value::Null))
                    })
            }
            _ => false,
        },
        // Functions are not data; they cannot be defaults.
        "function" => false,
        "opaque" => false,
        _ => false,
    }
}

fn is_canonical_base64(text: &str) -> bool {
    let chars: Vec<char> = text.chars().collect();
    if chars.len() % 4 != 0 || chars.is_empty() {
        return false;
    }
    let mut padding = 0usize;
    for (index, c) in chars.iter().enumerate() {
        match c {
            'A'..='Z' | 'a'..='z' | '0'..='9' | '+' | '/' => {
                if padding > 0 {
                    return false;
                }
            }
            '=' => {
                padding += 1;
                if index < chars.len() - 2 {
                    return false;
                }
            }
            _ => return false,
        }
    }
    matches!(padding, 0 | 1 | 2)
}

// --- subtype checker -------------------------------------------------------

/// The v1 conservative subtype table. `Ok(Verdict::Holds)` proves inclusion;
/// `Ok(Verdict::Breaks)` proves exclusion; `Ok(Verdict::Unknown)` means the
/// conservative rules cannot establish inclusion and must not guess.
pub fn subtype(a: &Value, b: &Value) -> Verdict {
    let a_shape = a.str_field("shape").unwrap_or_default();
    let b_shape = b.str_field("shape").unwrap_or_default();
    if a_shape != b_shape {
        return Verdict::Breaks;
    }
    match a_shape {
        "scalar" => scalar_subtype(a, b),
        "record" => record_subtype(a, b),
        "sum" => sum_subtype(a, b),
        "sequence" => {
            let item = subtype(
                &a.get("items").cloned().unwrap_or(Value::Null),
                &b.get("items").cloned().unwrap_or(Value::Null),
            );
            intervals_contained(a, b).and(item)
        }
        "map" => {
            // Key types are identical.
            if !type_identical(
                &a.get("keys").cloned().unwrap_or(Value::Null),
                &b.get("keys").cloned().unwrap_or(Value::Null),
            ) {
                return Verdict::Breaks;
            }
            let values = subtype(
                &a.get("values").cloned().unwrap_or(Value::Null),
                &b.get("values").cloned().unwrap_or(Value::Null),
            );
            intervals_contained(a, b).and(values)
        }
        "function" => {
            let a_args = a.get("arguments").and_then(Value::as_arr).unwrap_or(&[]);
            let b_args = b.get("arguments").and_then(Value::as_arr).unwrap_or(&[]);
            if a_args.len() != b_args.len() {
                return Verdict::Breaks;
            }
            // B's argument types are subtypes of A's (contravariance); A's
            // result is a subtype of B's (covariance).
            let mut verdict = subtype(
                &a.get("result").cloned().unwrap_or(Value::Null),
                &b.get("result").cloned().unwrap_or(Value::Null),
            );
            for (a_arg, b_arg) in a_args.iter().zip(b_args.iter()) {
                verdict = subtype(b_arg, a_arg).and(verdict);
            }
            verdict
        }
        "opaque" => {
            if type_identical(a, b) {
                Verdict::Holds
            } else {
                Verdict::Unknown
            }
        }
        _ => Verdict::Unknown,
    }
}

impl Verdict {
    fn and(self, other: Verdict) -> Verdict {
        use Verdict::*;
        match (self, other) {
            (Breaks, _) | (_, Breaks) => Breaks,
            (Unknown, _) | (_, Unknown) => Unknown,
            (Holds, Holds) => Holds,
        }
    }
}

fn scalar_subtype(a: &Value, b: &Value) -> Verdict {
    let a_name = a.str_field("name").unwrap_or_default();
    let b_name = b.str_field("name").unwrap_or_default();
    if a_name != b_name {
        return Verdict::Breaks;
    }
    if a_name == "integer" {
        let a_min = a.get("min").and_then(Value::as_int);
        let a_max = a.get("max").and_then(Value::as_int);
        let b_min = b.get("min").and_then(Value::as_int);
        let b_max = b.get("max").and_then(Value::as_int);
        return match (a_min, a_max, b_min, b_max) {
            (Some(a_min), Some(a_max), Some(b_min), Some(b_max)) => {
                if a_min >= b_min && a_max <= b_max {
                    Verdict::Holds
                } else {
                    Verdict::Breaks
                }
            }
            _ => Verdict::Unknown,
        };
    }
    if type_identical(a, b) {
        Verdict::Holds
    } else {
        Verdict::Unknown
    }
}

fn type_identical(a: &Value, b: &Value) -> bool {
    formats::canonical(a) == formats::canonical(b)
}

fn intervals_contained(a: &Value, b: &Value) -> Verdict {
    let a_min = a.get("min").and_then(Value::as_int);
    let a_max = a.get("max").and_then(Value::as_int);
    let b_min = b.get("min").and_then(Value::as_int);
    let b_max = b.get("max").and_then(Value::as_int);
    match (a_min, a_max, b_min, b_max) {
        (Some(a_min), Some(a_max), Some(b_min), Some(b_max)) => {
            if a_min >= b_min && a_max <= b_max {
                Verdict::Holds
            } else {
                Verdict::Breaks
            }
        }
        _ => Verdict::Unknown,
    }
}

fn is_open(ty: &Value) -> bool {
    ty.get("open").and_then(Value::as_bool).unwrap_or(false)
}

fn record_subtype(a: &Value, b: &Value) -> Verdict {
    // An open A requires an open B.
    if is_open(a) && !is_open(b) {
        return Verdict::Breaks;
    }
    let a_fields = a.get("fields").cloned().unwrap_or(Value::Null);
    let b_fields = b.get("fields").cloned().unwrap_or(Value::Null);
    let (Value::Obj(a_entries), Value::Obj(b_entries)) = (&a_fields, &b_fields) else {
        return Verdict::Unknown;
    };
    let mut verdict = Verdict::Holds;
    for (b_name, b_field) in b_entries.iter() {
        let b_required = b_field.get("required").and_then(Value::as_bool).unwrap_or(false);
        match a_entries.iter().find(|(a_name, _)| a_name == b_name) {
            Some((_, a_field)) => {
                let a_required = a_field
                    .get("required")
                    .and_then(Value::as_bool)
                    .unwrap_or(false);
                // Every required B field is required in A.
                if b_required && !a_required {
                    return Verdict::Breaks;
                }
                verdict = subtype(
                    &a_field.get("type").cloned().unwrap_or(Value::Null),
                    &b_field.get("type").cloned().unwrap_or(Value::Null),
                )
                .and(verdict);
            }
            None => {
                if b_required {
                    // A required B field missing from A: A cannot always
                    // provide it.
                    return Verdict::Breaks;
                }
                // Optional B field absent from A.
                if is_open(a) {
                    // An open A could emit that field with an incompatible
                    // unknown value.
                    return Verdict::Unknown;
                }
            }
        }
    }
    for (a_name, a_field) in a_entries.iter() {
        let a_required = a_field
            .get("required")
            .and_then(Value::as_bool)
            .unwrap_or(false);
        if a_required {
            match b_entries.iter().find(|(b_name, _)| b_name == a_name) {
                Some((_, b_field)) => {
                    verdict = subtype(
                        &a_field.get("type").cloned().unwrap_or(Value::Null),
                        &b_field.get("type").cloned().unwrap_or(Value::Null),
                    )
                    .and(verdict);
                }
                None => {
                    // Extra A fields require B to be open.
                    if !is_open(b) {
                        return Verdict::Breaks;
                    }
                }
            }
        }
        // Optional A fields: if B has a typed field with the same name it
        // was checked above; otherwise A may emit the extra optional field,
        // which an open B accepts and a closed B cannot interpret.
        if !a_required && !b_entries.iter().any(|(b_name, _)| b_name == a_name) && !is_open(b) {
            verdict = Verdict::Unknown.and(verdict);
        }
    }
    verdict
}

fn sum_subtype(a: &Value, b: &Value) -> Verdict {
    // Open A requires open B.
    if is_open(a) && !is_open(b) {
        return Verdict::Breaks;
    }
    let a_variants = a.get("variants").cloned().unwrap_or(Value::Null);
    let b_variants = b.get("variants").cloned().unwrap_or(Value::Null);
    let (Value::Obj(a_entries), Value::Obj(b_entries)) = (&a_variants, &b_variants) else {
        return Verdict::Unknown;
    };
    let mut verdict = Verdict::Holds;
    for (a_name, a_variant) in a_entries.iter() {
        match b_entries.iter().find(|(b_name, _)| b_name == a_name) {
            Some((_, b_variant)) => {
                verdict = subtype(a_variant, b_variant).and(verdict);
            }
            None => {
                // Every named A variant exists in B with a subtype payload
                // unless B is open (unknown variants are retained as opaque
                // payloads).
                if !is_open(b) {
                    return Verdict::Breaks;
                }
            }
        }
    }
    verdict
}

// --- accretion checker -----------------------------------------------------

/// The v1 accretion rules: every old output remains with a subtype output,
/// retained inputs widen, removed inputs leave tombstones, tombstones are
/// never fabricated, defaults are identical, old laws and relations remain,
/// and new required inputs or relations break. Each rule helper returns the
/// combined verdict for its rule or `Err(())` for a definite break.
pub fn accretes(old: &Value, new: &Value) -> Result<Verdict, Vec<String>> {
    validate_contract(old)?;
    validate_contract(new)?;
    fn view<'a>(doc: &'a Value, key: &str) -> &'a [Value] {
        doc.get(key).and_then(Value::as_arr).unwrap_or(&[])
    }
    let (old_slots, new_slots) = (view(old, "slots"), view(new, "slots"));
    let (old_tombstones, new_tombstones) =
        (view(old, "tombstones"), view(new, "tombstones"));
    let verdict = (|| -> Result<Verdict, ()> {
        Ok(Verdict::Holds
            .and(remaining_outputs(old_slots, new_slots)?)
            .and(retained_inputs(old_slots, new_slots, new_tombstones)?)
            .and(tombstone_history(old_slots, old_tombstones, new_slots, new_tombstones)?)
            .and(new_inputs_forbidden(old_slots, old_tombstones, new_slots)?)
            .and(unchanged_input_defaults(old_slots, new_slots))
            .and(unchanged_records("laws", old, new)?)
            .and(unchanged_records("relations", old, new)?)
            .and(new_relations_forbidden(old, new)))
    })()
    .unwrap_or(Verdict::Breaks);
    Ok(verdict)
}

fn slot_identity_changed(old_slot: &Value, new_slot: &Value) -> bool {
    new_slot.str_field("facet").unwrap_or_default() != old_slot.str_field("facet").unwrap_or_default()
        || new_slot.str_field("polarity").unwrap_or_default()
            != old_slot.str_field("polarity").unwrap_or_default()
        || new_slot.str_field("meaning").unwrap_or_default()
            != old_slot.str_field("meaning").unwrap_or_default()
}

/// Every old output remains under the same name, facet, polarity, and
/// meaning, with a subtype output; removed outputs always break.
fn remaining_outputs(old_slots: &[Value], new_slots: &[Value]) -> Result<Verdict, ()> {
    let mut verdict = Verdict::Holds;
    for old_slot in old_slots.iter().filter(|s| s.str_field("polarity").unwrap_or_default() == "out") {
        let name = old_slot.str_field("name").unwrap_or_default();
        let Some(new_slot) = new_slots.iter().find(|s| s.str_field("name").unwrap_or_default() == name) else {
            return Err(());
        };
        if slot_identity_changed(old_slot, new_slot) {
            return Err(());
        }
        verdict = subtype(&slot_type(new_slot), &slot_type(old_slot)).and(verdict);
    }
    Ok(verdict)
}

/// Retained inputs widen: required may become optional, optional may not
/// become required; a removed input must leave a tombstone.
fn retained_inputs(
    old_slots: &[Value],
    new_slots: &[Value],
    new_tombstones: &[Value],
) -> Result<Verdict, ()> {
    let mut verdict = Verdict::Holds;
    for old_slot in old_slots.iter().filter(|s| s.str_field("polarity").unwrap_or_default() == "in") {
        let name = old_slot.str_field("name").unwrap_or_default();
        let old_required = old_slot.get("required").and_then(Value::as_bool).unwrap_or(false);
        let Some(new_slot) = new_slots.iter().find(|s| s.str_field("name").unwrap_or_default() == name) else {
            // Removed input: it must leave a tombstone retaining its last
            // accepted meaning and type.
            let Some(tombstone) = new_tombstones
                .iter()
                .find(|t| t.str_field("name").unwrap_or_default() == name)
            else {
                return Err(());
            };
            if tombstone.str_field("meaning").unwrap_or_default()
                != old_slot.str_field("meaning").unwrap_or_default()
            {
                return Err(());
            }
            verdict = subtype(&slot_type(tombstone), &slot_type(old_slot)).and(verdict);
            continue;
        };
        let new_required = new_slot.get("required").and_then(Value::as_bool).unwrap_or(false);
        // A reintroduced required input is a new requirement and breaks
        // accretion.
        if new_required && !old_required || slot_identity_changed(old_slot, new_slot) {
            return Err(());
        }
        verdict = subtype(&slot_type(old_slot), &slot_type(new_slot)).and(verdict);
    }
    Ok(verdict)
}

/// Existing tombstones remain or reactivate as non-required inputs whose
/// type accepts the tombstoned domain; tombstones cannot be fabricated
/// without history.
fn tombstone_history(
    old_slots: &[Value],
    old_tombstones: &[Value],
    new_slots: &[Value],
    new_tombstones: &[Value],
) -> Result<Verdict, ()> {
    let mut verdict = Verdict::Holds;
    for old_tombstone in old_tombstones {
        let name = old_tombstone.str_field("name").unwrap_or_default();
        if let Some(new_t) = new_tombstones
            .iter()
            .find(|t| t.str_field("name").unwrap_or_default() == name)
        {
            // Existing tombstones remain unchanged.
            if new_t.str_field("meaning").unwrap_or_default()
                != old_tombstone.str_field("meaning").unwrap_or_default()
                || formats::canonical(&slot_type(new_t))
                    != formats::canonical(&slot_type(old_tombstone))
            {
                return Err(());
            }
            continue;
        }
        // Reactivation as a non-required input whose type accepts the
        // tombstoned domain.
        let reactivated = new_slots.iter().find(|s| {
            s.str_field("name").unwrap_or_default() == name
                && s.str_field("polarity").unwrap_or_default() == "in"
                && s.get("required").and_then(Value::as_bool) == Some(false)
        });
        let Some(slot) = reactivated else {
            // An old tombstone must remain or reactivate.
            return Err(());
        };
        if slot.str_field("meaning").unwrap_or_default()
            != old_tombstone.str_field("meaning").unwrap_or_default()
        {
            return Err(());
        }
        verdict = subtype(&slot_type(old_tombstone), &slot_type(slot)).and(verdict);
    }
    for new_tombstone in new_tombstones {
        let name = new_tombstone.str_field("name").unwrap_or_default();
        let has_history = old_tombstones
            .iter()
            .any(|t| t.str_field("name").unwrap_or_default() == name)
            || old_slots.iter().any(|s| {
                s.str_field("name").unwrap_or_default() == name
                    && s.str_field("polarity").unwrap_or_default() == "in"
            });
        if !has_history {
            return Err(());
        }
    }
    Ok(verdict)
}

/// New inputs absent from old slots/tombstones: a new required input is
/// forbidden; a new optional input is permitted.
fn new_inputs_forbidden(
    old_slots: &[Value],
    old_tombstones: &[Value],
    new_slots: &[Value],
) -> Result<Verdict, ()> {
    for new_slot in new_slots.iter().filter(|s| s.str_field("polarity").unwrap_or_default() == "in") {
        let name = new_slot.str_field("name").unwrap_or_default();
        let known = old_slots
            .iter()
            .any(|s| s.str_field("name").unwrap_or_default() == name)
            || old_tombstones
                .iter()
                .any(|t| t.str_field("name").unwrap_or_default() == name);
        if !known {
            let required = new_slot.get("required").and_then(Value::as_bool).unwrap_or(false);
            if required {
                return Err(());
            }
        }
    }
    Ok(Verdict::Holds)
}

/// Provided defaults are identical; changed input defaults are
/// conservatively a break because omission can change behavior.
fn unchanged_input_defaults(old_slots: &[Value], new_slots: &[Value]) -> Verdict {
    for old_slot in old_slots {
        let name = old_slot.str_field("name").unwrap_or_default();
        let Some(new_slot) = new_slots
            .iter()
            .find(|s| s.str_field("name").unwrap_or_default() == name)
        else {
            continue;
        };
        if formats::canonical(&old_slot.get("default").cloned().unwrap_or(Value::Null))
            != formats::canonical(&new_slot.get("default").cloned().unwrap_or(Value::Null))
        {
            return Verdict::Breaks;
        }
    }
    Verdict::Holds
}

/// Every old law or relation record remains unchanged; new records of that
/// kind are checked by their own rule.
fn unchanged_records(key: &str, old: &Value, new: &Value) -> Result<Verdict, ()> {
    fn view2<'a>(doc: &'a Value, key: &str) -> &'a [Value] {
        doc.get(key).and_then(Value::as_arr).unwrap_or(&[])
    }
    for old_record in view2(old, key) {
        let id = old_record.str_field("id").unwrap_or_default();
        let Some(new_record) = view2(new, key)
            .iter()
            .find(|r| r.str_field("id").unwrap_or_default() == id)
        else {
            return Err(());
        };
        if formats::canonical(old_record) != formats::canonical(new_record) {
            return Err(());
        }
    }
    Ok(Verdict::Holds)
}

/// New required relations are a break; v1 relations are all required.
fn new_relations_forbidden(old: &Value, new: &Value) -> Verdict {
    let old_relations = old.get("relations").and_then(Value::as_arr).unwrap_or(&[]);
    let new_relations = new.get("relations").and_then(Value::as_arr).unwrap_or(&[]);
    if !new_relations.is_empty() && old_relations.is_empty() {
        return Verdict::Breaks;
    }
    Verdict::Holds
}
