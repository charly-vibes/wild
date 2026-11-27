// Purpose: bounded demand-path resolution for the rust-cargo-local-1
//   profile (beads wild-158) — the single place that turns a syntactic
//   path into a crate-qualified demand target under design ruling D1.
// Responsibilities: own the bounded resolution rules (declared dependency
//   heads, import aliases with rest, crate-qualified heads, module-relative
//   multi-segment candidates validated at demand-resolution time), the
//   demand-entry recording shared by direct calls, expression paths,
//   struct literals, and method calls, and the method-receiver resolution
//   shapes (constructor calls with bundle-wide recorded return types,
//   plain type paths, let-bound single-assignment locals, inventoried
//   field access, self/Self in inherent impl bodies, and hop-folded
//   chains — widen-method-receiver-demands) — never type inference beyond
//   those shapes.
// Rationale: keeping resolution semantics out of extract.rs honors the
//   pretender line-count ratchet (mirroring extract/mod_files.rs) and makes
//   the "gaps never cure silently" rule auditable in one place.

use super::mod_files::mod_file_candidates;
use super::*;

impl<'a> SourceWalk<'a> {
    /// module-relative same-crate candidate for a locally-written path
    /// (wild-158): paths resolve relative to the current module, so the
    /// candidate is validated against the inventory at demand-resolution
    /// time instead of being resolved by identifier guessing here.
    pub(super) fn module_relative_target(&self, joined: &str) -> String {
        if self.module_prefix.is_empty() {
            format!("{}::{joined}", self.ctx.crate_name)
        } else {
            format!(
                "{}::{}::{joined}",
                self.ctx.crate_name,
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
        if self.ctx.dep_names.iter().any(|d| d == head) {
            return Some((format!("{head}::{}", rest.join("::")), None));
        }
        if let Some(target) = self.alias_map.get(head) {
            return Some((
                format!("{target}::{}", rest.join("::")),
                Some(head.to_string()),
            ));
        }
        if head == "crate" || head == self.ctx.crate_name {
            return Some((
                format!("{}::{}", self.ctx.crate_name, rest.join("::")),
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
    /// sources keep the incumbent gap unless the target sits under a
    /// declared conveys input path (wild-hyk), which records a scoped
    /// conveyance claim instead, or under a declared on_absent input path
    /// (wild-adc), which records a scoped fallible-absence outcome instead
    /// — the slot stays required, only the absence handling changes; slot
    /// presence is validated at demand-resolution time.
    pub(super) fn record_resolved_demand(
        &mut self,
        target: &str,
        alias: Option<&str>,
        span: proc_macro2::Span,
    ) {
        if let Some(provider_slot) = self.meaning_of(target) {
            let mut entry = vec![
                ("consumer", formats::s(&self.ctx.crate_name)),
                ("called", formats::s(target)),
                (
                    "alias",
                    match alias {
                        Some(a) => formats::s(a),
                        None => Value::Null,
                    },
                ),
                ("provider_slot", formats::s(&provider_slot)),
            ];
            // the declared absence policy rides on the demand entry
            // (wild-adc) so the contract slot carries it
            if let Some(scope) = super::conveyed_scope(self.ctx.on_absent, target) {
                entry.push(("on_absent", formats::s("fallible")));
                entry.push(("scope", formats::s(&scope)));
            }
            self.out.demand.push(formats::obj(entry));
            let loc = span.start();
            self.out.locations.push(formats::obj(vec![
                ("slot", formats::s(target)),
                ("file", formats::s(&self.current_file)),
                ("line", formats::i(loc.line as i64)),
                ("col", formats::i(loc.column as i64)),
            ]));
        } else if let Some(scope) = super::conveyed_scope(self.ctx.conveys, target) {
            // wild-hyk: the target sits under a declared conveys input path,
            // so the unknown slot is forwarded not interpreted: record a
            // conveyance claim scoped to the covering declared path instead
            // of the incomplete-demand refusal. The claim never exempts
            // validation — the forwarded input stays a required opaque
            // in-slot, and check still refuses a newly introduced one.
            self.out.demand.push(formats::obj(vec![
                ("consumer", formats::s(&self.ctx.crate_name)),
                ("called", formats::s(target)),
                (
                    "alias",
                    match alias {
                        Some(a) => formats::s(a),
                        None => Value::Null,
                    },
                ),
                ("provider_slot", formats::s(target)),
                ("conveyed", Value::Bool(true)),
                ("scope", formats::s(&scope)),
            ]));
            let loc = span.start();
            self.out.locations.push(formats::obj(vec![
                ("slot", formats::s(target)),
                ("file", formats::s(&self.current_file)),
                ("line", formats::i(loc.line as i64)),
                ("col", formats::i(loc.column as i64)),
            ]));
        } else if let Some(scope) = super::conveyed_scope(self.ctx.on_absent, target) {
            // wild-adc: the target sits under a declared on_absent input
            // path, so the absent demand records a scoped fallible-absence
            // outcome instead of the incomplete-demand refusal — the
            // outside world lacked the fact, and the consumer declared it
            // handles that. The claim never exempts validation: the slot
            // stays a required in-slot, and check still refuses a newly
            // introduced one.
            self.out.demand.push(formats::obj(vec![
                ("consumer", formats::s(&self.ctx.crate_name)),
                ("called", formats::s(target)),
                (
                    "alias",
                    match alias {
                        Some(a) => formats::s(a),
                        None => Value::Null,
                    },
                ),
                ("provider_slot", formats::s(target)),
                ("on_absent", formats::s("fallible")),
                ("absent", Value::Bool(true)),
                ("scope", formats::s(&scope)),
            ]));
            let loc = span.start();
            self.out.locations.push(formats::obj(vec![
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

/// The written type name when the type is a single-segment,
/// uppercase-initial path type (`Meter`); scalars, generics, and complex
/// types record nothing. This is written syntax, not inference.
fn recorded_path_ty(ty: &syn::Type) -> Option<String> {
    let syn::Type::Path(path) = ty else {
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

/// The syntactic return-type name of a signature when it is a
/// single-segment, uppercase-initial path type (`-> Meter`); scalars and
/// complex types record nothing. This is written syntax, not inference.
fn recorded_return_ty(output: &syn::ReturnType) -> Option<String> {
    let syn::ReturnType::Type(_, ty) = output else {
        return None;
    };
    recorded_path_ty(ty)
}

fn qualify(crate_name: &str, prefix: &[String], suffix: &str) -> String {
    if prefix.is_empty() {
        format!("{}::{suffix}", crate_name)
    } else {
        format!("{}::{}::{suffix}", crate_name, prefix.join("::"))
    }
}

// ---- bundle-wide pre-pass (widen-method-receiver-demands, rule 1) ----

/// The bundle-wide pre-pass state: crate identity plus the loaded bundle
/// files for public non-inline module resolution. It records written
/// syntax only — return types of public fns and public inherent impl
/// methods, and public named-field types of public structs — into the
/// shared maps consumed by every per-file demand walk.
pub(super) struct BundlePrepass<'a> {
    crate_name: &'a str,
    loaded: &'a BTreeMap<String, Vec<u8>>,
    current_file: String,
    /// fn target → crate-qualified type target (wild-158 D1)
    fn_return_tys: BTreeMap<String, String>,
    /// type target → field name → crate-qualified field type target
    field_tys: BTreeMap<String, BTreeMap<String, String>>,
}

impl<'a> BundlePrepass<'a> {
    /// Scan one crate root file and (recursively) its public non-inline
    /// module files, returning the bundle maps before any demand walk runs
    /// (widen-method-receiver-demands, rule 1). No inference: written
    /// syntax only, validated at demand-resolution time.
    pub(super) fn scan_crate(
        crate_name: &'a str,
        source_path: &str,
        file: &syn::File,
        loaded: &'a BTreeMap<String, Vec<u8>>,
    ) -> (
        BTreeMap<String, String>,
        BTreeMap<String, BTreeMap<String, String>>,
    ) {
        let mut pre = BundlePrepass {
            crate_name,
            loaded,
            current_file: source_path.to_string(),
            fn_return_tys: BTreeMap::new(),
            field_tys: BTreeMap::new(),
        };
        pre.scan_items(&file.items, Vec::new());
        (pre.fn_return_tys, pre.field_tys)
    }

    fn qualify(&self, prefix: &[String], suffix: &str) -> String {
        qualify(self.crate_name, prefix, suffix)
    }

    /// Scan one file's items (rule 1): public free fn return types,
    /// inherent-impl constructor return types, public struct field types,
    /// inline module bodies, and public non-inline module files (rustc
    /// mod-path rule, mirroring mod_files::resolve_mod_file) so
    /// cross-file references resolve bundle-wide before any demand walk.
    fn scan_items(&mut self, items: &[syn::Item], prefix: Vec<String>) {
        for item in items {
            match item {
                syn::Item::Fn(f) => {
                    if matches!(f.vis, syn::Visibility::Public(_)) {
                        if let Some(ty) = recorded_return_ty(&f.sig.output) {
                            // key: fn target; value: crate-qualified type
                            // target (declaring module base + return type)
                            self.fn_return_tys.insert(
                                self.qualify(&prefix, &f.sig.ident.to_string()),
                                self.qualify(&prefix, &ty),
                            );
                        }
                    }
                }
                syn::Item::Impl(imp) => {
                    for (target, ty) in self.scan_impl(imp, &prefix) {
                        self.fn_return_tys.insert(target, ty);
                    }
                }
                syn::Item::Struct(s) => {
                    if let Some((ty_target, fields)) = self.scan_struct_fields(s, &prefix) {
                        self.field_tys.entry(ty_target).or_default().extend(fields);
                    }
                }
                syn::Item::Mod(m) => {
                    let name = m.ident.to_string();
                    if let Some((_, nested)) = &m.content {
                        let mut nested_prefix = prefix.clone();
                        nested_prefix.push(name);
                        self.scan_items(nested, nested_prefix);
                    } else if matches!(m.vis, syn::Visibility::Public(_)) {
                        // public non-inline module: resolve against the
                        // loaded bundle files with the rustc mod-path rule
                        // (mirroring mod_files::resolve_mod_file) and scan
                        // under the module prefix
                        let Some(rel) = mod_file_candidates(Path::new(&self.current_file), &name)
                            .into_iter()
                            .find(|c| self.loaded.contains_key(c.as_str()))
                        else {
                            continue;
                        };
                        let Ok(text) = std::str::from_utf8(
                            self.loaded.get(rel.as_str()).expect("membership checked"),
                        ) else {
                            continue;
                        };
                        let Ok(file) = syn::parse_file(text) else {
                            continue;
                        };
                        let mut nested_prefix = prefix.clone();
                        nested_prefix.push(name);
                        let prev_file = std::mem::replace(&mut self.current_file, rel);
                        self.scan_items(&file.items, nested_prefix);
                        self.current_file = prev_file;
                    }
                }
                _ => {}
            }
        }
    }

    /// Collect a public struct's named fields with single-segment,
    /// uppercase-initial path types (rule 1). A field typed by one of the
    /// struct's generic parameters records nothing: a generic parameter is
    /// not a type target, and a generic-typed receiver keeps the honest
    /// gap. Returns the type target and its field map, or None when the
    /// struct is private or no field qualifies.
    fn scan_struct_fields(
        &self,
        s: &syn::ItemStruct,
        prefix: &[String],
    ) -> Option<(String, BTreeMap<String, String>)> {
        if !matches!(s.vis, syn::Visibility::Public(_)) {
            return None;
        }
        let syn::Fields::Named(named) = &s.fields else {
            return None;
        };
        let generic_params: BTreeSet<String> = s
            .generics
            .params
            .iter()
            .filter_map(|p| match p {
                syn::GenericParam::Type(t) => Some(t.ident.to_string()),
                _ => None,
            })
            .collect();
        let ty_target = self.qualify(prefix, &s.ident.to_string());
        let mut fields = BTreeMap::new();
        for field in &named.named {
            if !matches!(field.vis, syn::Visibility::Public(_)) {
                continue;
            }
            let Some(field_ty) = recorded_path_ty(&field.ty) else {
                continue;
            };
            if generic_params.contains(&field_ty) {
                continue;
            }
            let field_name = field.ident.as_ref().expect("named field").to_string();
            let qualified = self.qualify(prefix, &field_ty);
            fields.insert(field_name, qualified);
        }
        if fields.is_empty() {
            None
        } else {
            Some((ty_target, fields))
        }
    }

    /// Collect constructor return types from one inherent impl on a named
    /// path type; trait impls are outside the profile and record nothing.
    /// Returns (method target, return type target) pairs.
    fn scan_impl(&self, imp: &syn::ItemImpl, prefix: &[String]) -> Vec<(String, String)> {
        let mut pairs = Vec::new();
        if imp.trait_.is_some() {
            return pairs;
        }
        let syn::Type::Path(path) = imp.self_ty.as_ref() else {
            return pairs;
        };
        if path.qself.is_some() {
            return pairs;
        }
        let Some(seg) = path.path.segments.last() else {
            return pairs;
        };
        let ty_name = seg.ident.to_string();
        for impl_item in &imp.items {
            let syn::ImplItem::Fn(m) = impl_item else {
                continue;
            };
            if !matches!(m.vis, syn::Visibility::Public(_)) {
                continue;
            }
            let target = self.qualify(prefix, &format!("{ty_name}::{}", m.sig.ident));
            if let Some(ty) = recorded_return_ty(&m.sig.output) {
                pairs.push((target, self.qualify(prefix, &ty)));
            }
        }
        pairs
    }
}

impl<'a> SourceWalk<'a> {
    /// Resolve a method-call receiver in the declared receiver shapes
    /// (widen-method-receiver-demands): a path expression resolving
    /// through the bounded demand rules — including a let-bound
    /// single-assignment local (rule 2) and `self`/`Self` inside an
    /// inherent impl body (rule 4); a call expression whose head resolves
    /// to a constructor or free function with a bundle-wide recorded
    /// return type; a field-access receiver whose field type is
    /// inventoried from a public struct-field declaration (rule 3); and a
    /// method chain folded hop-by-hop through recorded return types
    /// (rule 5). Everything else — trait objects, generics, macro output,
    /// closures, re-assigned locals, unknown identifiers — stays honestly
    /// unresolved.
    pub(super) fn resolve_method_receiver(&self, receiver: &syn::Expr) -> ReceiverOutcome {
        match receiver {
            // rule 5: chains fold hop-by-hop; a hop whose callee target has
            // no recorded return type keeps the gap naming the receiver,
            // while the already-resolved hops keep their recorded demands
            syn::Expr::MethodCall(inner) => match self.resolve_method_receiver(&inner.receiver) {
                ReceiverOutcome::ResolvedType(type_target) => {
                    let hop_target = format!("{type_target}::{}", inner.method);
                    match self.out.fn_return_tys.get(&hop_target) {
                        Some(returned) => ReceiverOutcome::ResolvedType(returned.clone()),
                        None => ReceiverOutcome::Unresolved(receiver_text(receiver)),
                    }
                }
                ReceiverOutcome::Unresolved(r) => ReceiverOutcome::Unresolved(r),
            },
            syn::Expr::Path(p) if p.qself.is_none() => {
                let mut parts = p
                    .path
                    .segments
                    .iter()
                    .map(|s| s.ident.to_string())
                    .collect::<Vec<_>>();
                let head = parts.drain(..1).next().unwrap_or_default();
                let rest = parts.iter().map(String::as_str).collect::<Vec<_>>();
                if rest.is_empty() {
                    // rule 2: a let-bound single-assignment local shadows
                    // any same-named alias for its receiver uses
                    if let Some(ty) = self.binding_type(&head) {
                        return ReceiverOutcome::ResolvedType(ty);
                    }
                    // rule 4: self/Self inside an inherent impl body
                    if head == "self" || head == "Self" {
                        if let Some(ty) = &self.current_impl_type {
                            return ReceiverOutcome::ResolvedType(ty.clone());
                        }
                    }
                }
                match self.bounded_target(&head, &rest) {
                    Some((target, _)) => ReceiverOutcome::ResolvedType(target),
                    None => ReceiverOutcome::Unresolved(receiver_text(receiver)),
                }
            }
            // rule 3: field access resolves via the inventoried public
            // field type; tuple indexing and unknown/private fields stay
            // unresolved
            syn::Expr::Field(f) => match &f.member {
                syn::Member::Named(ident) => match self.resolve_method_receiver(&f.base) {
                    ReceiverOutcome::ResolvedType(type_target) => {
                        match self
                            .out
                            .field_tys
                            .get(&type_target)
                            .and_then(|m| m.get(&ident.to_string()))
                        {
                            Some(ty) => ReceiverOutcome::ResolvedType(ty.clone()),
                            None => ReceiverOutcome::Unresolved(receiver_text(receiver)),
                        }
                    }
                    ReceiverOutcome::Unresolved(r) => ReceiverOutcome::Unresolved(r),
                },
                syn::Member::Unnamed(_) => ReceiverOutcome::Unresolved(receiver_text(receiver)),
            },
            syn::Expr::Call(_) => match self.resolve_let_init(receiver) {
                Some(ty) => ReceiverOutcome::ResolvedType(ty),
                None => ReceiverOutcome::Unresolved(receiver_text(receiver)),
            },
            _ => ReceiverOutcome::Unresolved(receiver_text(receiver)),
        }
    }

    /// The type of a let-bound single-assignment local, innermost scope
    /// first (rule 2).
    fn binding_type(&self, ident: &str) -> Option<String> {
        self.bindings
            .iter()
            .rev()
            .find_map(|scope| scope.get(ident).cloned())
    }

    /// Invalidate a local's binding at its re-assignment site: the walk
    /// runs in source order, so calls before the re-assignment were
    /// already resolved against the then-correct type and calls after it
    /// keep the honest gap (rule 2 residual, never retroactively cured).
    pub(super) fn clear_binding(&mut self, ident: &str) {
        for scope in self.bindings.iter_mut().rev() {
            if scope.remove(ident).is_some() {
                break;
            }
        }
    }

    /// The recorded type of a let initializer in the declared shapes: a
    /// call whose head resolves through the bounded demand rules and whose
    /// callee target has a bundle-wide recorded return type (rule 2), or a
    /// field access whose field type is inventoried from a public
    /// struct-field declaration. Method-call initializers, macro output,
    /// and everything else record nothing.
    fn resolve_let_init(&self, init: &syn::Expr) -> Option<String> {
        match init {
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
                            if let Some(ty) = self.out.fn_return_tys.get(&fn_target) {
                                return Some(ty.clone());
                            }
                        }
                    }
                }
                None
            }
            syn::Expr::Field(f) => {
                let syn::Member::Named(ident) = &f.member else {
                    return None;
                };
                match self.resolve_method_receiver(&f.base) {
                    ReceiverOutcome::ResolvedType(type_target) => self
                        .out
                        .field_tys
                        .get(&type_target)
                        .and_then(|m| m.get(&ident.to_string()))
                        .cloned(),
                    ReceiverOutcome::Unresolved(_) => None,
                }
            }
            _ => None,
        }
    }

    /// Rule 2: a `let` binding whose initializer resolves through the
    /// declared shapes records the binding's type for the remainder of the
    /// scope block. `let mut` binds too — single assignment means the
    /// local is never re-assigned, which the walk enforces at the
    /// assignment site. An initializer outside the shapes, a non-ident
    /// pattern, or a `ref` binding records nothing.
    pub(super) fn record_let_binding(walk: &mut SourceWalk, node: &syn::Local) {
        let Some(init) = node.init.as_ref().map(|i| &*i.expr) else {
            return;
        };
        let syn::Pat::Ident(pat) = &node.pat else {
            return;
        };
        if pat.by_ref.is_some() {
            return;
        }
        let Some(ty) = walk.resolve_let_init(init) else {
            return;
        };
        if let Some(scope) = walk.bindings.last_mut() {
            scope.insert(pat.ident.to_string(), ty);
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
