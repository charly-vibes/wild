// Purpose: bounded demand-path resolution for the rust-cargo-local-1
//   profile (beads wild-158) — the single place that turns a syntactic
//   path into a crate-qualified demand target under design ruling D1.
// Responsibilities: own the bounded resolution rules (declared dependency
//   heads, import aliases with rest, crate-qualified heads, module-relative
//   multi-segment candidates validated at demand-resolution time), the
//   demand-entry recording shared by direct calls, expression paths,
//   struct literals, and method calls, and the method-receiver resolution
//   shapes (constructor calls with recorded return types, plain type
//   paths) — never type inference beyond those shapes.
// Rationale: keeping resolution semantics out of extract.rs honors the
//   pretender line-count ratchet (mirroring extract/mod_files.rs) and makes
//   the "gaps never cure silently" rule auditable in one place.

use super::*;

impl<'a> SourceWalk<'a> {
    /// module-relative same-crate candidate for a locally-written path
    /// (wild-158): paths resolve relative to the current module, so the
    /// candidate is validated against the inventory at demand-resolution
    /// time instead of being resolved by identifier guessing here.
    pub(super) fn module_relative_target(&self, joined: &str) -> String {
        if self.module_prefix.is_empty() {
            format!("{}::{joined}", self.crate_name)
        } else {
            format!(
                "{}::{}::{joined}",
                self.crate_name,
                self.module_prefix.join("::")
            )
        }
    }

    /// Bounded demand-path resolution (wild-158). Returns the
    /// crate-qualified target and, when the head was an import alias, the
    /// alias name. Resolution is purely syntactic against the declared
    /// workspace facts: declared dependency heads, import aliases,
    /// crate-qualified heads, and local module-relative multi-segment
    /// paths. Module-relative candidates are validated against the
    /// inventory at demand-resolution time — an unknown candidate keeps
    /// the honest incomplete-demand gap there, never an invented
    /// resolution. Bare single-segment and `self`/`Self`/`super`-qualified
    /// paths stay outside the demand profile (unchanged treatment).
    pub(super) fn bounded_target(
        &self,
        head: &str,
        rest: &[&str],
    ) -> Option<(String, Option<String>)> {
        if rest.is_empty() {
            return self
                .alias_map
                .get(head)
                .map(|t| (t.clone(), Some(head.to_string())));
        }
        if self.dep_names.iter().any(|d| d == head) {
            return Some((format!("{head}::{}", rest.join("::")), None));
        }
        if let Some(target) = self.alias_map.get(head) {
            return Some((
                format!("{target}::{}", rest.join("::")),
                Some(head.to_string()),
            ));
        }
        if head == "crate" || head == self.crate_name {
            return Some((
                format!("{}::{}", self.crate_name, rest.join("::")),
                None,
            ));
        }
        if head == "self" || head == "Self" || head == "super" {
            // `self`/`Self`/`super`-qualified paths need scope knowledge the
            // bounded shapes do not carry; they stay outside the demand
            // profile (unchanged incumbent treatment)
            return None;
        }
        let joined = format!("{head}::{}", rest.join("::"));
        Some((self.module_relative_target(&joined), None))
    }

    /// Record one demand entry against an already-resolved target
    /// (wild-158 method-call resolution routes here). Unsupplied provider
    /// sources keep the incumbent gap; slot presence is validated at
    /// demand-resolution time.
    pub(super) fn record_resolved_demand(
        &mut self,
        target: &str,
        alias: Option<&str>,
        span: proc_macro2::Span,
    ) {
        if let Some(provider_slot) = self.meaning_of(target) {
            self.demand.push(formats::obj(vec![
                ("consumer", formats::s(&self.crate_name)),
                ("called", formats::s(target)),
                (
                    "alias",
                    match alias {
                        Some(a) => formats::s(a),
                        None => Value::Null,
                    },
                ),
                ("provider_slot", formats::s(&provider_slot)),
            ]));
            let loc = span.start();
            self.locations.push(formats::obj(vec![
                ("slot", formats::s(target)),
                ("file", formats::s(&self.current_file)),
                ("line", formats::i(loc.line as i64)),
                ("col", formats::i(loc.column as i64)),
            ]));
        } else {
            self.gap(
                "incomplete-demand",
                format!(
                    "demand `{target}` cannot resolve: provider source is not supplied in the bundle"
                ),
                true,
            );
        }
    }

    pub(super) fn record_demand(&mut self, callee: &str, span: proc_macro2::Span) {
        let mut parts = callee.split("::");
        let head = parts.next().unwrap_or("").to_string();
        let rest: Vec<&str> = parts.collect();
        let Some((target, alias)) = self.bounded_target(&head, &rest) else {
            // `self`/`super`-qualified multi-segment paths stay outside the
            // demand profile (unchanged incumbent treatment)
            return;
        };
        self.record_resolved_demand(&target, alias.as_deref(), span);
    }
}

/// Outcome of bounded method-receiver resolution (design ruling D1,
/// beads wild-158).
pub(super) enum ReceiverOutcome {
    /// The receiver resolved in a bounded shape to a crate-qualified type
    /// target: the method demand `<type_target>::<method>` is recorded and
    /// validated against the full inventory at demand-resolution time.
    ResolvedType(String),
    /// The receiver is outside the bounded shapes (multi-hop chains beyond
    /// one resolved hop, field access, macro output, literals, unknown
    /// identifiers): the honest gap names the receiver. Never inferred.
    Unresolved(String),
}

fn receiver_text(receiver: &syn::Expr) -> String {
    receiver.to_token_stream().to_string()
}

/// The syntactic return-type name of a signature when it is a
/// single-segment, uppercase-initial path type (`-> Meter`); scalars and
/// complex types record nothing. This is written syntax, not inference.
fn recorded_return_ty(output: &syn::ReturnType) -> Option<String> {
    let syn::ReturnType::Type(_, ty) = output else {
        return None;
    };
    let syn::Type::Path(path) = ty.as_ref() else {
        return None;
    };
    if path.qself.is_some() || path.path.segments.len() != 1 {
        return None;
    }
    let ident = path.path.segments.last()?.ident.to_string();
    if ident.starts_with(|c: char| c.is_ascii_uppercase()) {
        Some(ident)
    } else {
        None
    }
}

fn qualify(walk: &SourceWalk, prefix: &[String], suffix: &str) -> String {
    if prefix.is_empty() {
        format!("{}::{suffix}", walk.crate_name)
    } else {
        format!(
            "{}::{}::{suffix}",
            walk.crate_name,
            prefix.join("::")
        )
    }
}

fn scan_items(walk: &mut SourceWalk, items: &[syn::Item], prefix: Vec<String>) {
    for item in items {
        match item {
            syn::Item::Fn(f) => {
                if matches!(f.vis, syn::Visibility::Public(_)) {
                    if let Some(ty) = recorded_return_ty(&f.sig.output) {
                        // key: fn target; value: crate-qualified type target
                        // (declaring module base + return type name)
                        walk.fn_return_tys.insert(
                            qualify(walk, &prefix, &f.sig.ident.to_string()),
                            qualify(walk, &prefix, &ty),
                        );
                    }
                }
            }
            syn::Item::Impl(imp) => scan_impl(walk, imp, &prefix),
            syn::Item::Mod(m) => {
                if let Some((_, nested)) = &m.content {
                    let mut nested_prefix = prefix.clone();
                    nested_prefix.push(m.ident.to_string());
                    scan_items(walk, nested, nested_prefix);
                }
            }
            _ => {}
        }
    }
}

/// Record constructor return types from one inherent impl on a named path
/// type; trait impls are outside the profile and record nothing.
fn scan_impl(walk: &mut SourceWalk, imp: &syn::ItemImpl, prefix: &[String]) {
    if imp.trait_.is_some() {
        return;
    }
    let syn::Type::Path(path) = imp.self_ty.as_ref() else {
        return;
    };
    if path.qself.is_some() {
        return;
    }
    let Some(seg) = path.path.segments.last() else {
        return;
    };
    let ty_name = seg.ident.to_string();
    for impl_item in &imp.items {
        let syn::ImplItem::Fn(m) = impl_item else {
            continue;
        };
        if !matches!(m.vis, syn::Visibility::Public(_)) {
            continue;
        }
        let target = qualify(walk, prefix, &format!("{ty_name}::{}", m.sig.ident));
        if let Some(ty) = recorded_return_ty(&m.sig.output) {
            walk.fn_return_tys.insert(target, qualify(walk, prefix, &ty));
        }
    }
}

impl<'a> SourceWalk<'a> {
    /// Pre-pass over one file's items recording the syntactic return types
    /// of public free fns and public inherent impl methods (single-segment,
    /// uppercase-initial path types only) so one-hop constructor receivers
    /// resolve without type inference (wild-158 D1). Called before the
    /// demand walk of the same file so use sites see declarations declared
    /// later in the file; cross-file and cross-crate constructors keep the
    /// honest gap (D7 threshold — file a follow-up, never approximate).
    pub(super) fn scan_fn_returns(walk: &mut SourceWalk, items: &[syn::Item]) {
        scan_items(walk, items, walk.module_prefix.clone());
    }

    /// Resolve a method-call receiver in the bounded shapes (wild-158 D1):
    /// a path expression resolving through the bounded demand rules, or a
    /// call expression whose head resolves to an inventoried constructor
    /// with a recorded return type. Everything else — chains, field
    /// access, macro output, literals, bare unknown identifiers — stays
    /// honestly unresolved.
    pub(super) fn resolve_method_receiver(&self, receiver: &syn::Expr) -> ReceiverOutcome {
        match receiver {
            syn::Expr::Path(p) if p.qself.is_none() => {
                let mut parts = p
                    .path
                    .segments
                    .iter()
                    .map(|s| s.ident.to_string())
                    .collect::<Vec<_>>();
                let head = parts.drain(..1).next().unwrap_or_default();
                match self.bounded_target(&head, &parts.iter().map(String::as_str).collect::<Vec<_>>()) {
                    Some((target, _)) => ReceiverOutcome::ResolvedType(target),
                    None => ReceiverOutcome::Unresolved(receiver_text(receiver)),
                }
            }
            syn::Expr::Call(call) => {
                if let syn::Expr::Path(func) = &*call.func {
                    if func.qself.is_none() {
                        let mut parts = func
                            .path
                            .segments
                            .iter()
                            .map(|s| s.ident.to_string())
                            .collect::<Vec<_>>();
                        let head = parts.drain(..1).next().unwrap_or_default();
                        let rest: Vec<&str> = parts.iter().map(String::as_str).collect();
                        if let Some((fn_target, _)) = self.bounded_target(&head, &rest) {
                            if let Some(type_target) = self.fn_return_tys.get(&fn_target) {
                                return ReceiverOutcome::ResolvedType(type_target.clone());
                            }
                        }
                    }
                }
                ReceiverOutcome::Unresolved(receiver_text(receiver))
            }
            _ => ReceiverOutcome::Unresolved(receiver_text(receiver)),
        }
    }

    /// Handle one method call (wild-158 D1). A bounded receiver creates the
    /// demand `<crate>::<Type>::<method>` — resolving against the inventoried
    /// impl-method/typed slots yields supported demand, an absent method
    /// fails demand resolution naming the full path, and a receiver outside
    /// the bounded shapes keeps the honest incomplete-demand gap naming the
    /// receiver. The call is always descended afterwards so arguments and
    /// nested calls record their own demands (never silently dropped).
    pub(super) fn handle_method_call(walk: &mut SourceWalk, node: &syn::ExprMethodCall) {
        let method = node.method.to_string();
        match walk.resolve_method_receiver(&node.receiver) {
            ReceiverOutcome::ResolvedType(type_target) => {
                let target = format!("{type_target}::{method}");
                walk.record_resolved_demand(&target, None, node.method.span());
            }
            ReceiverOutcome::Unresolved(receiver) => {
                walk.gap(
                    "incomplete-demand",
                    format!(
                        "method call `.{method}` on receiver `{receiver}` is outside the supported demand profile: the receiver is not resolvable in the bounded shapes"
                    ),
                    true,
                );
            }
        }
    }
}
