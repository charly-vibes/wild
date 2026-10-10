#[warn(unused)]
use wild::v1::*;
use wild::formats::{self, Value};
use wild::v1::*;

fn scalar_int(min: i64, max: i64) -> Value {
    formats::obj(vec![
        ("shape", formats::s("scalar")),
        ("name", formats::s("integer")),
        ("min", formats::i(min)),
        ("max", formats::i(max)),
    ])
}

fn scalar_str() -> Value {
    formats::obj(vec![("shape", formats::s("scalar")), ("name", formats::s("string"))])
}

fn opaque(fp: &str) -> Value {
    formats::obj(vec![("shape", formats::s("opaque")), ("fingerprint", formats::s(fp))])
}

fn example_contract() -> Value {
    formats::obj(vec![
        ("schema_version", formats::s("1")),
        ("kind", formats::s("contract")),
        ("slots", formats::arr(Vec::new())),
        ("tombstones", formats::arr(Vec::new())),
        ("laws", formats::arr(Vec::new())),
        ("relations", formats::arr(Vec::new())),
        ("sunsets", formats::arr(Vec::new())),
    ])
}

fn set_key(contract: &mut Value, key: &str, value: Value) {
    let Value::Obj(entries) = contract else {
        return;
    };
    for (name, slot) in entries.iter_mut() {
        if name == key {
            *slot = value.clone();
        }
    }
}

fn with_key(key: &str, value: Value) -> Value {
    let mut contract = example_contract();
    set_key(&mut contract, key, value);
    contract
}

fn contract_with_slot(slot: Value) -> Value {
    let mut contract = example_contract();
    set_key(&mut contract, "slots", formats::arr(vec![slot.clone()]));
    contract
}

fn integer_slot(name: &str, polarity: &str, required: bool, ty: Value) -> Value {
    formats::obj(vec![
        ("name", formats::s(name)),
        ("meaning", formats::s("example.meaning")),
        ("polarity", formats::s(polarity)),
        ("facet", formats::s("api")),
        ("type", ty),
        ("required", Value::Bool(required)),
        (
            "default",
            formats::obj(vec![("present", Value::Bool(false))]),
        ),
    ])
}

#[test]
fn canonical_reader_examples_match_the_format_document() {
    assert_eq!(formats::canonical(&formats::parse(r#"{"b":2,"a":1}"#).unwrap()), r#"{"a":1,"b":2}"#);
    assert_eq!(
        formats::canonical(&formats::parse(r#"{ "text": "\u0061" }"#).unwrap()),
        r#"{"text":"a"}"#
    );
    assert_eq!(
        formats::canonical(&formats::parse(r#"{"text":"\n"}"#).unwrap()),
        r#"{"text":"\u000a"}"#
    );
    assert!(formats::parse(r#"{"a":1,"a":2}"#).is_err());
    assert!(formats::parse(r#"{"a":1.0}"#).is_err());
}

#[test]
fn empty_contract_is_valid() {
    let contract = example_contract();
    assert_eq!(validate_contract(&contract), Ok(()));
}

#[test]
fn integer_subtype_uses_interval_containment() {
    assert_eq!(subtype(&scalar_int(0, 10), &scalar_int(0, 20)), Verdict::Holds);
    assert_eq!(subtype(&scalar_int(0, 20), &scalar_int(0, 10)), Verdict::Breaks);
    assert_eq!(subtype(&scalar_str(), &scalar_int(0, 1)), Verdict::Breaks);
}

#[test]
fn opaque_mismatch_is_unknown_not_a_guess() {
    let a = opaque("sha256:1111111111111111111111111111111111111111111111111111111111111111");
    let b = opaque("sha256:2222222222222222222222222222222222222222222222222222222222222222");
    assert_eq!(subtype(&a, &b), Verdict::Unknown);
    assert_eq!(subtype(&a, &a), Verdict::Holds);
}

#[test]
fn extra_record_field_requires_open_target() {
    let closed = formats::obj(vec![
        ("shape", formats::s("record")),
        ("open", Value::Bool(false)),
        ("fields", formats::obj(Vec::new())),
    ]);
    let open_extra = formats::obj(vec![
        ("shape", formats::s("record")),
        ("open", Value::Bool(false)),
        (
            "fields",
            formats::obj(vec![(
                "x",
                formats::obj(vec![
                    ("type", scalar_str()),
                    ("required", Value::Bool(true)),
                ]),
            )]),
        ),
    ]);
    assert_eq!(subtype(&open_extra, &closed), Verdict::Breaks);
    let open_closed = formats::obj(vec![
        ("shape", formats::s("record")),
        ("open", Value::Bool(true)),
        ("fields", formats::obj(Vec::new())),
    ]);
    assert_eq!(subtype(&open_extra, &open_closed), Verdict::Holds);
}

#[test]
fn function_arguments_are_contravariant() {
    let wide_arg = formats::obj(vec![
        ("shape", formats::s("function")),
        ("arguments", formats::arr(vec![scalar_int(0, 10)])),
        ("result", scalar_int(0, 10)),
    ]);
    let narrow_arg = formats::obj(vec![
        ("shape", formats::s("function")),
        ("arguments", formats::arr(vec![scalar_int(0, 20)])),
        ("result", scalar_int(0, 10)),
    ]);
    // A (narrow domain) subtypes B (wide domain): B's argument type must
    // accept everything A can be called with.
    assert_eq!(subtype(&narrow_arg, &wide_arg), Verdict::Holds);
    assert_eq!(subtype(&wide_arg, &narrow_arg), Verdict::Breaks);
}

#[test]
fn identical_contract_accretes() {
    let contract = contract_with_slot(integer_slot(
        "value",
        "out",
        true,
        scalar_int(0, 10),
    ));
    assert_eq!(accretes(&contract, &contract), Ok(Verdict::Holds));
}

#[test]
fn removed_output_always_breaks() {
    let old = contract_with_slot(integer_slot(
        "value",
        "out",
        true,
        scalar_int(0, 10),
    ));
    let new = example_contract();
    assert_eq!(accretes(&old, &new), Ok(Verdict::Breaks));
}

#[test]
fn new_required_input_breaks_but_optional_is_permitted() {
    let old = example_contract();
    let new_required = contract_with_slot(integer_slot(
        "extra",
        "in",
        true,
        scalar_int(0, 10),
    ));
    assert_eq!(accretes(&old, &new_required), Ok(Verdict::Breaks));
    let optional = contract_with_slot(integer_slot(
        "extra",
        "in",
        false,
        scalar_int(0, 10),
    ));
    assert_eq!(accretes(&old, &optional), Ok(Verdict::Holds));
}

#[test]
fn removed_input_requires_a_tombstone() {
    let old = contract_with_slot(integer_slot(
        "legacy",
        "in",
        true,
        scalar_int(0, 10),
    ));
    let new_without_tombstone = example_contract();
    assert_eq!(accretes(&old, &new_without_tombstone), Ok(Verdict::Breaks));
    let tombstone = integer_slot("legacy", "in", false, scalar_int(0, 10));
    let new_with_tombstone =
        with_key("tombstones", formats::arr(vec![tombstone.clone()]));
    assert_eq!(accretes(&old, &new_with_tombstone), Ok(Verdict::Holds));
    // Fabricated tombstones without history are refused.
    assert_eq!(accretes(&example_contract(), &new_with_tombstone), Ok(Verdict::Breaks));
}

#[test]
fn changed_input_default_is_conservatively_a_break() {
    let old_slot = integer_slot("opt", "in", false, scalar_int(0, 10));
    let new_slot = {
        let mut slot = integer_slot("opt", "in", false, scalar_int(0, 10));
        if let Value::Obj(entries) = &mut slot {
            entries.retain(|(k, _)| k != "default");
            entries.push((
                "default".to_string(),
                formats::obj(vec![("present", Value::Bool(true)), ("value", formats::i(0))]),
            ));
        }
        slot
    };
    let old = contract_with_slot(old_slot);
    let new = contract_with_slot(new_slot);
    assert_eq!(accretes(&old, &new), Ok(Verdict::Breaks));
}

#[test]
fn dropped_law_breaks_and_new_required_relation_breaks() {
    let law = formats::obj(vec![
        ("id", formats::s("example.law")),
        ("suite_digest", formats::s(&format!("sha256:{}", "1".repeat(64)))),
        ("slots", formats::arr(Vec::new())),
    ]);
    let old = with_key("laws", formats::arr(vec![law.clone()]));
    assert_eq!(accretes(&old, &example_contract()), Ok(Verdict::Breaks));
    let relation = formats::obj(vec![
        ("id", formats::s("example.rel")),
        ("operator", formats::s("equal")),
        ("left", formats::s("a.b")),
        ("right", formats::s("c.d")),
    ]);
    let new_with_relation = with_key("relations", formats::arr(vec![relation.clone()]));
    assert_eq!(
        accretes(&example_contract(), &new_with_relation),
        Ok(Verdict::Breaks)
    );
}
