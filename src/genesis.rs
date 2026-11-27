// Purpose: genesis envelope shell wrapping the v1 envelope as `data`
//   (beads wild-lof, fleet lane of the genesis add-fleet-adoption-plan).
// Responsibilities: Build the genesis envelope shape (ok, envelope_version,
//   cli_version, envelope_kind, data, warnings, meta) around the unchanged
//   v1 envelope, mapping the v1 decision to a genesis envelope kind:
//   accept -> ok, refuse -> check, error -> error.
// Rationale: The adoption row requires the v1 payload contract to be
//   unchanged and additive: the v1 envelope is carried verbatim as `data`,
//   so the bytes inside the shell are exactly the bytes wild emitted before
//   the wrap, and a consumer that unwraps `data` sees the v1 envelope it
//   already knew. The shell follows the genesis-vibes `Envelope`
//   serialization (fields omitted when absent, zeroed meta) without adding
//   a serde dependency: wild emits canonical JSON through wild::formats,
//   whose sorted-key writer keeps the wrapped payload byte-identical.

use crate::formats::{self, Value};

/// The wild envelope protocol version carried as `envelope_version`: the
/// v1 envelope's own schema version.
pub const ENVELOPE_VERSION: &str = "1";

/// Wrap a v1 envelope in the genesis shell, deriving `envelope_kind` and
/// `ok` from the v1 `decision` field: `accept` is an ok envelope, `refuse`
/// is a check result (the command succeeded, the verdict is refuse), and
/// anything else is an error envelope.
pub fn wrap(v1: &Value) -> Value {
    let (kind, ok) = match v1.get("decision").and_then(Value::as_str) {
        Some("accept") => ("ok", true),
        Some("refuse") => ("check", true),
        _ => ("error", false),
    };
    shell(kind, ok, v1.clone())
}

fn shell(kind: &str, ok: bool, data: Value) -> Value {
    formats::obj(vec![
        ("ok", Value::Bool(ok)),
        ("envelope_version", formats::s(ENVELOPE_VERSION)),
        ("cli_version", formats::s(env!("CARGO_PKG_VERSION"))),
        ("envelope_kind", formats::s(kind)),
        ("data", data),
        ("warnings", formats::arr(Vec::new())),
        (
            "meta",
            formats::obj(vec![
                ("duration_ms", formats::i(0)),
                ("tx", Value::Null),
                ("request_id", Value::Null),
            ]),
        ),
    ])
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn wrap_carries_v1_payload_verbatim() {
        let v1 = formats::obj(vec![
            ("schema_version", formats::s("1")),
            ("kind", formats::s("envelope")),
            ("decision", formats::s("accept")),
        ]);
        let wrapped = wrap(&v1);
        assert_eq!(
            wrapped.get("data").map(|d| formats::canonical(d)),
            Some(formats::canonical(&v1))
        );
        assert_eq!(wrapped.get("ok"), Some(&Value::Bool(true)));
        assert_eq!(
            wrapped.get("envelope_kind"),
            Some(&formats::s("ok"))
        );
        assert_eq!(
            wrapped.get("envelope_version"),
            Some(&formats::s("1"))
        );
    }

    #[test]
    fn refuse_is_a_check_result_error_is_an_error() {
        let refuse = wrap(&formats::obj(vec![("decision", formats::s("refuse"))]));
        assert_eq!(refuse.get("envelope_kind"), Some(&formats::s("check")));
        assert_eq!(refuse.get("ok"), Some(&Value::Bool(true)));
        let error = wrap(&formats::obj(vec![("decision", formats::s("error"))]));
        assert_eq!(error.get("envelope_kind"), Some(&formats::s("error")));
        assert_eq!(error.get("ok"), Some(&Value::Bool(false)));
    }
}
