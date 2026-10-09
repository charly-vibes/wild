// Purpose: Strict v1 JSON handling for the wild extractor (beads wild-mh5.1).
// Responsibilities: Parse JSON with v1 refusal rules (duplicate keys,
//   floating-point numbers, integers outside the exact-integer range, and
//   unpaired surrogates are invalid), emit canonical bytes per
//   docs/wild-formats-v1.md (recursively sorted object keys by Unicode
//   scalar value, no whitespace or BOM, base-ten integers, lowercase
//   \u00xx control escapes, unescaped solidus, literal UTF-8 otherwise),
//   and compute sha256 content digests over canonical or raw bytes.
// Rationale: v1 identity is canonical-bytes hashing, so the reader and
//   canonicalizer are ported byte-for-byte from the normative rules rather
//   than delegated to a JSON library whose parser silently deduplicates
//   keys and admits floats — both refusals the local-1 protocol requires.

use sha2::{Digest, Sha256};

/// Maximum exact integer magnitude per v1: [-2^53+1, 2^53-1].
pub const MAX_SAFE_INTEGER: i64 = 9007199254740991;

/// Parsed v1 JSON value. Objects preserve entry order; duplicate keys are
/// refused at parse time, so canonicalization may sort freely.
#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Null,
    Bool(bool),
    Int(i64),
    Str(String),
    Arr(Vec<Value>),
    Obj(Vec<(String, Value)>),
}

impl Value {
    pub fn get(&self, key: &str) -> Option<&Value> {
        match self {
            Value::Obj(entries) => entries.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }

    pub fn as_str(&self) -> Option<&str> {
        match self {
            Value::Str(s) => Some(s),
            _ => None,
        }
    }

    pub fn as_int(&self) -> Option<i64> {
        match self {
            Value::Int(i) => Some(*i),
            _ => None,
        }
    }

    pub fn as_bool(&self) -> Option<bool> {
        match self {
            Value::Bool(b) => Some(*b),
            _ => None,
        }
    }

    pub fn as_arr(&self) -> Option<&[Value]> {
        match self {
            Value::Arr(items) => Some(items),
            _ => None,
        }
    }

    pub fn as_obj(&self) -> Option<&[(String, Value)]> {
        match self {
            Value::Obj(entries) => Some(entries),
            _ => None,
        }
    }

    pub fn str_field(&self, key: &str) -> Result<&str, String> {
        self.get(key)
            .and_then(Value::as_str)
            .ok_or_else(|| format!("missing string field `{key}`"))
    }
}

/// Construct an object from ordered (key, value) pairs.
pub fn obj(entries: Vec<(&str, Value)>) -> Value {
    Value::Obj(entries.into_iter().map(|(k, v)| (k.to_string(), v)).collect())
}

pub fn s(v: &str) -> Value {
    Value::Str(v.to_string())
}

pub fn i(v: i64) -> Value {
    Value::Int(v)
}

pub fn arr(items: Vec<Value>) -> Value {
    Value::Arr(items)
}

/// Parse JSON text under v1 refusal rules.
pub fn parse(text: &str) -> Result<Value, String> {
    if text.starts_with('\u{feff}') {
        return Err("byte-order mark is invalid in v1 documents".to_string());
    }
    let bytes: Vec<char> = text.chars().collect();
    let mut pos = 0usize;
    let value = parse_value(&bytes, &mut pos)?;
    skip_ws(&bytes, &mut pos);
    if pos != bytes.len() {
        return Err(format!("trailing content at char {pos}"));
    }
    Ok(value)
}

fn skip_ws(bytes: &[char], pos: &mut usize) {
    while *pos < bytes.len() && matches!(bytes[*pos], ' ' | '\t' | '\n' | '\r') {
        *pos += 1;
    }
}

fn parse_value(bytes: &[char], pos: &mut usize) -> Result<Value, String> {
    skip_ws(bytes, pos);
    let Some(&c) = bytes.get(*pos) else {
        return Err("unexpected end of input".to_string());
    };
    match c {
        '{' => parse_object(bytes, pos),
        '[' => parse_array(bytes, pos),
        '"' => Ok(Value::Str(parse_string(bytes, pos)?)),
        't' => literal(bytes, pos, "true", Value::Bool(true)),
        'f' => literal(bytes, pos, "false", Value::Bool(false)),
        'n' => literal(bytes, pos, "null", Value::Null),
        '-' | '0'..='9' => parse_number(bytes, pos),
        _ => Err(format!("unexpected character `{c}` at char {pos}")),
    }
}

fn literal(bytes: &[char], pos: &mut usize, word: &str, value: Value) -> Result<Value, String> {
    for expected in word.chars() {
        let Some(&c) = bytes.get(*pos) else {
            return Err("unexpected end of input".to_string());
        };
        if c != expected {
            return Err(format!("invalid literal near char {pos}"));
        }
        *pos += 1;
    }
    Ok(value)
}

fn parse_object(bytes: &[char], pos: &mut usize) -> Result<Value, String> {
    *pos += 1; // consume '{'
    let mut entries: Vec<(String, Value)> = Vec::new();
    skip_ws(bytes, pos);
    if bytes.get(*pos) == Some(&'}') {
        *pos += 1;
        return Ok(Value::Obj(entries));
    }
    loop {
        skip_ws(bytes, pos);
        if bytes.get(*pos) != Some(&'"') {
            return Err(format!("expected object key at char {pos}"));
        }
        let key = parse_string(bytes, pos)?;
        skip_ws(bytes, pos);
        if bytes.get(*pos) != Some(&':') {
            return Err(format!("expected `:` at char {pos}"));
        }
        *pos += 1;
        let value = parse_value(bytes, pos)?;
        if entries.iter().any(|(k, _)| *k == key) {
            return Err(format!("duplicate object key `{key}`"));
        }
        entries.push((key, value));
        skip_ws(bytes, pos);
        match bytes.get(*pos) {
            Some(',') => *pos += 1,
            Some('}') => {
                *pos += 1;
                return Ok(Value::Obj(entries));
            }
            _ => return Err(format!("expected `,` or `}}` at char {pos}")),
        }
    }
}

fn parse_array(bytes: &[char], pos: &mut usize) -> Result<Value, String> {
    *pos += 1; // consume '['
    let mut items = Vec::new();
    skip_ws(bytes, pos);
    if bytes.get(*pos) == Some(&']') {
        *pos += 1;
        return Ok(Value::Arr(items));
    }
    loop {
        items.push(parse_value(bytes, pos)?);
        skip_ws(bytes, pos);
        match bytes.get(*pos) {
            Some(',') => *pos += 1,
            Some(']') => {
                *pos += 1;
                return Ok(Value::Arr(items));
            }
            _ => return Err(format!("expected `,` or `]` at char {pos}")),
        }
    }
}

fn parse_number(bytes: &[char], pos: &mut usize) -> Result<Value, String> {
    let start = *pos;
    if bytes.get(*pos) == Some(&'-') {
        *pos += 1;
    }
    let digits_start = *pos;
    while matches!(bytes.get(*pos), Some('0'..='9')) {
        *pos += 1;
    }
    if *pos == digits_start {
        return Err(format!("invalid number at char {start}"));
    }
    if bytes[digits_start] == '0' && *pos - digits_start > 1 {
        return Err(format!("leading zero is invalid at char {start}"));
    }
    if matches!(bytes.get(*pos), Some('.') | Some('e') | Some('E')) {
        return Err(format!("floating-point numbers are invalid at char {start}"));
    }
    let text: String = bytes[start..*pos].iter().collect();
    let int: i64 = text
        .parse()
        .map_err(|_| format!("integer out of range at char {start}"))?;
    if int.abs() > MAX_SAFE_INTEGER {
        return Err(format!("integer out of exact range at char {start}"));
    }
    Ok(Value::Int(int))
}

fn parse_string(bytes: &[char], pos: &mut usize) -> Result<String, String> {
    *pos += 1; // consume opening quote
    let mut out = String::new();
    loop {
        let Some(&c) = bytes.get(*pos) else {
            return Err("unterminated string".to_string());
        };
        *pos += 1;
        match c {
            '"' => return Ok(out),
            '\\' => {
                let Some(&esc) = bytes.get(*pos) else {
                    return Err("unterminated escape".to_string());
                };
                *pos += 1;
                match esc {
                    '"' => out.push('"'),
                    '\\' => out.push('\\'),
                    '/' => out.push('/'),
                    'b' => out.push('\u{0008}'),
                    'f' => out.push('\u{000c}'),
                    'n' => out.push('\n'),
                    'r' => out.push('\r'),
                    't' => out.push('\t'),
                    'u' => {
                        let cp = parse_hex4(bytes, pos)?;
                        if (0xd800..=0xdbff).contains(&cp) {
                            // high surrogate must pair
                            if bytes.get(*pos) != Some(&'\\') || bytes.get(*pos + 1) != Some(&'u') {
                                return Err("unpaired high surrogate".to_string());
                            }
                            *pos += 2;
                            let low = parse_hex4(bytes, pos)?;
                            if !(0xdc00..=0xdfff).contains(&low) {
                                return Err("invalid low surrogate".to_string());
                            }
                            let combined =
                                0x10000 + ((cp - 0xd800) << 10) + (low - 0xdc00);
                            out.push(char::from_u32(combined).ok_or("invalid surrogate pair")?);
                        } else if (0xdc00..=0xdfff).contains(&cp) {
                            return Err("unpaired low surrogate".to_string());
                        } else {
                            out.push(char::from_u32(cp).ok_or("invalid code point")?);
                        }
                    }
                    _ => return Err(format!("invalid escape `\\{esc}`")),
                }
            }
            c if (c as u32) < 0x20 => {
                return Err(format!("raw control character at char {pos}"));
            }
            c => out.push(c),
        }
    }
}

fn parse_hex4(bytes: &[char], pos: &mut usize) -> Result<u32, String> {
    let mut value = 0u32;
    for _ in 0..4 {
        let Some(&c) = bytes.get(*pos) else {
            return Err("unexpected end of \\u escape".to_string());
        };
        let digit = c
            .to_digit(16)
            .ok_or_else(|| format!("invalid hex digit `{c}`"))?;
        value = value * 16 + digit;
        *pos += 1;
    }
    Ok(value)
}

/// Canonical bytes per docs/wild-formats-v1.md.
pub fn canonical(value: &Value) -> String {
    let mut out = String::new();
    write_canonical(value, &mut out);
    out
}

fn write_canonical(value: &Value, out: &mut String) {
    match value {
        Value::Null => out.push_str("null"),
        Value::Bool(true) => out.push_str("true"),
        Value::Bool(false) => out.push_str("false"),
        Value::Int(n) => out.push_str(&n.to_string()),
        Value::Str(s) => write_escaped(s, out),
        Value::Arr(items) => {
            out.push('[');
            for (idx, item) in items.iter().enumerate() {
                if idx > 0 {
                    out.push(',');
                }
                write_canonical(item, out);
            }
            out.push(']');
        }
        Value::Obj(entries) => {
            let mut keys: Vec<&str> = entries.iter().map(|(k, _)| k.as_str()).collect();
            keys.sort();
            out.push('{');
            for (idx, key) in keys.iter().enumerate() {
                if idx > 0 {
                    out.push(',');
                }
                write_escaped(key, out);
                out.push(':');
                let (_, value) = entries.iter().find(|(k, _)| k == key).expect("sorted key");
                write_canonical(value, out);
            }
            out.push('}');
        }
    }
}

fn write_escaped(text: &str, out: &mut String) {
    out.push('"');
    for c in text.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out.push('"');
}

/// sha256 content digest: `sha256:` plus 64 lowercase hex digits.
pub fn sha256_digest(bytes: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(bytes);
    format!("sha256:{:x}", hasher.finalize())
}

/// Validate a `sha256:<64 lowercase hex>` digest string.
pub fn is_digest(text: &str) -> bool {
    let Some(hex) = text.strip_prefix("sha256:") else {
        return false;
    };
    hex.len() == 64 && hex.bytes().all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn canonical_rules_match_the_format_document_examples() {
        let cases: Vec<(&str, &str)> = vec![
            (r#"{"b":2,"a":1}"#, r#"{"a":1,"b":2}"#),
            (r#"{ "text": "\u0061" }"#, r#"{"text":"a"}"#),
            (r#"{"text":"\n"}"#, r#"{"text":"\u000a"}"#),
        ];
        for (input, expected) in cases {
            let value = parse(input).expect("parses");
            assert_eq!(canonical(&value), expected);
        }
    }

    #[test]
    fn refusals() {
        for bad in [
            r#"{"a":1,"a":2}"#,
            r#"{"a":1.0}"#,
            r#"{"a":01}"#,
            r#"{"a":9007199254740992}"#,
            // leading byte-order mark is invalid input
            "\u{feff}{}",
            // raw control character inside a string
            "{\"a\":\"line\nbreak\"}",
        ] {
            assert!(parse(bad).is_err(), "{bad} must be refused");
        }
    }
}
