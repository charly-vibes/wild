// Purpose: whitelisted std macro demand handling — the closed whitelist,
// the comma-separated argument grammar, format-capture scanning, and the
// capture cross-check (add-std-macro-demand-support +
// add-format-args-demand-support).
// Responsibilities: own every piece of macro-invocation demand semantics so
// `extract.rs` stays under the pretender line-count ratchet; expose only the
// entry points the walker and the demand-resolution stage need.
// Rationale: the whitelist is data, the refusal path is shared, and the
// capture rules are probe-verified — keeping them together makes the closed
// set auditable without tracing control flow.

use super::*;

/// Std expression macros whose expansion is a closed definition that
/// evaluates only their syntactic arguments and cannot reference
/// consumer-visible functions outside them (add-std-macro-demand-support,
/// design decision 2). Auditable data, not control flow.
const ARGUMENT_CONFINED_STD_MACROS: &[&str] = &[
    "println",
    "print",
    "eprintln",
    "eprint",
    "format",
    "panic",
    "assert",
    "assert_eq",
    "assert_ne",
    "debug_assert",
    "debug_assert_eq",
    "debug_assert_ne",
    "todo",
    "unimplemented",
    "unreachable",
    "format_args",
];

/// A comma-separated expression list with optional trailing comma — the
/// argument grammar every whitelisted macro's expansion consumes
/// (add-std-macro-demand-support, design decision 3). `name = expr` parses
/// as `Expr::Assign`, so named-argument values are descended like
/// positional arguments (add-format-args-demand-support, decision 3,
/// probe-corrected).
struct ArgumentExprList(syn::punctuated::Punctuated<syn::Expr, syn::token::Comma>);

impl syn::parse::Parse for ArgumentExprList {
    fn parse(input: syn::parse::ParseStream) -> syn::parse::Result<Self> {
        Ok(ArgumentExprList(syn::punctuated::Punctuated::parse_terminated(
            input,
        )?))
    }
}

impl<'a> SourceWalk<'a> {
    /// Whitelist + parse + descend for macro invocations in expression or
    /// statement position (add-std-macro-demand-support). A whitelisted
    /// argument-confined std macro has its token trees parsed as a
    /// comma-separated expression list and each argument walked like a
    /// direct-call site; any other head, or a parse failure, keeps the
    /// honest `incomplete-demand` refusal. Never guesses.
    pub(super) fn handle_invocation_macro(&mut self, mac: &syn::Macro) {
        let head = mac
            .path
            .segments
            .last()
            .map(|s| s.ident.to_string())
            .unwrap_or_default();
        if !ARGUMENT_CONFINED_STD_MACROS.contains(&head.as_str()) {
            self.refuse_invocation(
                &head,
                "may introduce usages the profile cannot inventory",
            );
            return;
        }
        match mac.parse_body::<ArgumentExprList>() {
            Ok(exprs) => {
                self.scan_format_captures(mac);
                for expr in exprs.0 {
                    self.visit_expr(&expr);
                }
            }
            Err(_) => self.refuse_invocation(
                &head,
                "arguments do not parse as a comma-separated expression list; the expansion cannot be tracked",
            ),
        }
    }

    fn refuse_invocation(&mut self, head: &str, why: &str) {
        self.gap(
            "incomplete-demand",
            format!("macro invocation `{head}!` {why}"),
            true,
        );
    }

    /// Scan the invocation's format-string literal for implicit captures
    /// (add-format-args-demand-support, design decision 4). Since Rust 2021
    /// a capture names a scope value while the token trees carry only a
    /// string literal, so the walker would otherwise silently accept a
    /// provider-value reference. Alias-named captures whose target head is
    /// a declared dependency are disclosed immediately; every other capture
    /// ident is collected for the leaf-name check at demand-resolution time.
    fn scan_format_captures(&mut self, mac: &syn::Macro) {
        // capture idents are scope references; a named argument (`name =
        // expr`, the `=` alone-spaced) shadows the scope name inside the
        // format string, so its ident is not a capture. `==` keeps its first
        // `=` joint-spaced, which distinguishes it from the assignment.
        let trees: Vec<proc_macro2::TokenTree> = mac.tokens.clone().into_iter().collect();
        let named_args: BTreeSet<String> = trees
            .windows(2)
            .filter_map(|w| match (&w[0], &w[1]) {
                (
                    proc_macro2::TokenTree::Ident(id),
                    proc_macro2::TokenTree::Punct(p),
                ) if p.as_char() == '=' && p.spacing() == proc_macro2::Spacing::Alone => {
                    Some(id.to_string())
                }
                _ => None,
            })
            .collect();
        // only the first string-literal token is the format string; later
        // string arguments are data whose braces are literal text
        for tree in trees {
            let text = match &tree {
                proc_macro2::TokenTree::Literal(lit) => lit.to_string(),
                _ => continue,
            };
            // str literals only: format strings are "..." or r"..."/r#"..."#;
            // byte literals (b"...") are not format strings
            if text.starts_with('b') {
                continue;
            }
            let Some(open) = text.find('"') else { continue };
            let content = &text[open + 1..text.rfind('"').unwrap_or(open + 1)];
            for ident in format_capture_idents(content) {
                if named_args.contains(&ident) {
                    continue;
                }
                if let Some(target) = self.alias_map.get(&ident) {
                    let head = target.split("::").next().unwrap_or("");
                    if self.dep_names.iter().any(|d| *d == head) {
                        self.gap(
                            "incomplete-demand",
                            format!(
                                "format capture `{ident}` references provider item `{target}`; capturing a provider item as a value is outside the supported demand profile"
                            ),
                            true,
                        );
                        continue;
                    }
                }
                if !self.capture_idents.contains(&ident) {
                    self.capture_idents.push(ident);
                }
            }
            break;
        }
    }
}

/// A capture identifier collected from a whitelisted macro's format string,
/// attributed to the member it was found in (for the leaf-name check).
pub(super) struct CaptureRef {
    pub(super) ident: String,
    pub(super) crate_name: String,
    pub(super) file: String,
}

/// Cross-check format captures against the supplied provider slots
/// (add-format-args-demand-support, design decision 4, leaf-name path).
/// A capture ident that shares a leaf name with a provider item from
/// another member is disclosed even without a matching alias: shadowing a
/// provider item in a format capture is over-disclosure by design (honest,
/// conservative), never a silent acceptance. Merely scanning identifier
/// strings never establishes resolution — the same law that governs
/// check_demand_resolution applies here.
pub(super) fn check_capture_disclosure(
    all_slots: &[SlotRecord],
    captures: &[CaptureRef],
    diagnostics: &mut Vec<Diagnostic>,
    complete: &mut bool,
) {
    if captures.is_empty() {
        return;
    }
    for capture in captures {
        let provider_leafs: BTreeSet<String> = all_slots
            .iter()
            .filter(|s| s.meaning.split('.').next().unwrap_or("") != capture.crate_name)
            .filter_map(|s| s.meaning.rsplit('.').next().map(std::string::ToString::to_string))
            .collect();
        if provider_leafs.contains(capture.ident.as_str()) {
            diagnostics.push(Diagnostic {
                code: "incomplete-demand",
                severity: "error",
                source: Some(capture.file.clone()),
                reason: format!(
                    "format capture `{}` shares provider item name `{}`; capturing a provider item as a value is outside the supported demand profile",
                    capture.ident, capture.ident
                ),
            });
            *complete = false;
        }
    }
}

/// Implicit capture identifiers inside a format-string body (Rust 2021
/// inline format args; add-format-args-demand-support, design decision 4).
/// Skips `{{`/`}}` escape pairs and digit-only positional placeholders like
/// `{0}`, which reference arguments, not scope variables. The capture is
/// the leading identifier inside a brace; the rest of the placeholder
/// (format spec) is skipped to the closing brace.
fn format_capture_idents(content: &str) -> Vec<String> {
    let chars: Vec<char> = content.chars().collect();
    let mut idents = Vec::new();
    let mut i = 0;
    while i < chars.len() {
        if chars[i] == '{' {
            if chars.get(i + 1) == Some(&'{') {
                i += 2;
                continue;
            }
            let mut j = i + 1;
            let mut ident = String::new();
            while j < chars.len() && (chars[j].is_ascii_alphabetic() || chars[j] == '_') {
                ident.push(chars[j]);
                j += 1;
            }
            // digit-only or empty captures (e.g. `{0}`, `{}`) reference
            // arguments, not scope variables — nothing to check
            if !ident.is_empty() && !idents.contains(&ident) {
                idents.push(ident);
            }
            // skip to the closing brace of this placeholder
            while j < chars.len() && chars[j] != '}' {
                j += 1;
            }
            i = j + 1;
        } else if chars[i] == '}' && chars.get(i + 1) == Some(&'}') {
            i += 2;
        } else {
            i += 1;
        }
    }
    idents
}