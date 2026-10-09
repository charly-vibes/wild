// Purpose: rust-cargo-local-1 extraction for the wild extractor (beads
//   wild-mh5.1).
// Responsibilities: Validate local-1 extraction requests (field whitelist,
//   kind/version/profile, bundle confinement, raw digest binding), load
//   supplied bundles immutably, inventory the declared supported subset
//   with syn (public free functions over unit/bool/i8-u32 signatures,
//   ordinary modules, direct dependency-qualified calls, explicit
//   non-glob aliases) without executing project code, inventory other
//   public declarations as opaque with formatting-invariant fingerprints,
//   emit explicit gaps for unsupported constructs (macros, methods,
//   traits, globs, FFI, cfg, returned-object calls, function pointers),
//   and assemble the contract/demand/provenance/report local-1 records
//   with slot ids derived from crate identity and qualified path.
// Rationale: The design law requires deterministic identities that never
//   depend on line numbers (semantic contract bytes must be identical
//   across checkout locations and formatting) while provenance and raw
//   digests stay location-accurate. Gaps are explicit and uncuring: an
//   unsupported construct marks the inventory incomplete rather than
//   inventing a complete contract.

use crate::formats::{self, Value};
use quote::ToTokens;
use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};
use syn::spanned::Spanned;
use syn::visit::Visit;

pub const PROFILE: &str = "rust-cargo-local-1";
pub const LOCAL_VERSION: &str = "local-1";

const REQUEST_FIELDS: &[&str] = &[
    "version",
    "kind",
    "profile",
    "bundle_root",
    "files",
    "target",
    "toolchain",
    "features",
    "extractor",
];

pub struct ExtractionOutcome {
    pub contract: Value,
    pub demand: Value,
    pub provenance: Value,
    pub report: Value,
    pub complete_inventory: bool,
    pub diagnostics: Vec<Value>,
    pub slot_names: Vec<String>,
}

struct Diagnostic {
    code: &'static str,
    severity: &'static str,
    source: Option<String>,
    reason: String,
}

impl Diagnostic {
    fn to_value(&self) -> Value {
        formats::obj(vec![
            ("code", formats::s(self.code)),
            ("severity", formats::s(self.severity)),
            (
                "source",
                match &self.source {
                    Some(path) => formats::s(path),
                    None => Value::Null,
                },
            ),
            ("slots", formats::arr(Vec::new())),
            ("reason", formats::s(&self.reason)),
        ])
    }
}

struct SlotRecord {
    name: String,
    meaning: String,
    ty: Value,
}

/// Validate the request envelope shape; returns bundle root and file
/// commitment list on success. Every refusal is an error-class input.
fn validate_request(request: &Value) -> Result<(PathBuf, Vec<(String, String)>), String> {
    if request.str_field("version")? != LOCAL_VERSION {
        return Err(format!(
            "unsupported protocol version `{}`; expected {LOCAL_VERSION}",
            request.str_field("version")?
        ));
    }
    if request.str_field("kind")? != "extraction-request" {
        return Err(format!(
            "unsupported record kind `{}` for extract",
            request.str_field("kind")?
        ));
    }
    if request.str_field("profile")? != PROFILE {
        return Err(format!(
            "unsupported profile `{}`; expected {PROFILE}",
            request.str_field("profile")?
        ));
    }
    if let Value::Obj(entries) = request {
        for (key, _) in entries {
            if !REQUEST_FIELDS.contains(&key.as_str()) {
                return Err(format!("unknown request field `{key}`"));
            }
        }
    }
    for field in ["target", "toolchain", "bundle_root"] {
        if request.get(field).and_then(Value::as_str).is_none() {
            return Err(format!("missing string field `{field}`"));
        }
    }
    let features = request
        .get("features")
        .and_then(Value::as_arr)
        .ok_or("missing array field `features`")?;
    if features.iter().any(|f| f.as_str().is_none()) {
        return Err("features must be an array of strings".to_string());
    }
    let extractor = request.get("extractor").ok_or("missing field `extractor`")?;
    if let Value::Obj(entries) = extractor {
        for (key, _) in entries {
            if !matches!(key.as_str(), "name" | "digest") {
                return Err(format!("unknown extractor field `{key}`"));
            }
        }
        let digest = extractor.str_field("digest")?;
        if !formats::is_digest(digest) {
            return Err(format!("invalid extractor digest `{digest}`"));
        }
        extractor.str_field("name")?;
    } else {
        return Err("`extractor` must be an object".to_string());
    }
    let files_obj = request.get("files").ok_or("missing field `files`")?;
    let files = match files_obj {
        Value::Obj(entries) => {
            let mut out = Vec::new();
            for (rel, digest_value) in entries {
                let digest = digest_value
                    .as_str()
                    .ok_or("file digests must be strings")?;
                if !formats::is_digest(digest) {
                    return Err(format!("invalid digest for `{rel}`"));
                }
                if is_confined(rel).is_none() {
                    return Err(format!(
                        "input-mismatch: filesystem reference `{rel}` escapes the supplied bundle"
                    ));
                }
                out.push((rel.clone(), digest.to_string()));
            }
            out
        }
        _ => return Err("`files` must be an object".to_string()),
    };
    Ok((PathBuf::from(request.str_field("bundle_root")?), files))
}

/// Return the bundle-relative normalized path, or None when the reference
/// escapes the bundle (absolute, dot/dot-dot components, or empty).
fn is_confined(rel: &str) -> Option<PathBuf> {
    if rel.is_empty() || rel.starts_with('/') {
        return None;
    }
    let path = Path::new(rel);
    for component in path.components() {
        match component {
            std::path::Component::Normal(part) => {
                if part == ".." || part == "." {
                    return None;
                }
            }
            _ => return None,
        }
    }
    Some(path.to_path_buf())
}

/// Verify each listed file exists inside the bundle with matching raw bytes.
fn load_bundle(
    root: &Path,
    files: &[(String, String)],
) -> Result<BTreeMap<String, Vec<u8>>, String> {
    let mut loaded = BTreeMap::new();
    for (rel, digest) in files {
        let rel_path =
            is_confined(rel).ok_or_else(|| format!("input-mismatch: `{rel}` escapes bundle"))?;
        let path = root.join(&rel_path);
        let bytes = std::fs::read(&path)
            .map_err(|e| format!("input-mismatch: bundle file `{rel}` unreadable: {e}"))?;
        let actual = formats::sha256_digest(&bytes);
        if &actual != digest {
            return Err(format!(
                "input-mismatch: raw digest for `{rel}` is `{actual}`, request commits `{digest}`; a fresh extraction of the current bundle is required"
            ));
        }
        loaded.insert(rel.clone(), bytes);
    }
    Ok(loaded)
}

struct MemberManifest {
    name: String,
    version: String,
    deps: Vec<String>,
    source_path: String, // bundle-relative path of src/lib.rs
}

fn parse_member_manifest(rel_manifest: &str, text: &str) -> Result<MemberManifest, String> {
    let doc: toml::Value =
        toml::from_str(text).map_err(|e| format!("malformed manifest `{rel_manifest}`: {e}"))?;
    let package = doc
        .get("package")
        .ok_or_else(|| format!("manifest `{rel_manifest}` has no [package]"))?;
    let name = package
        .get("name")
        .and_then(|v| v.as_str())
        .ok_or_else(|| format!("manifest `{rel_manifest}` has no package name"))?
        .to_string();
    let version = package
        .get("version")
        .and_then(|v| v.as_str())
        .ok_or_else(|| {
            format!("manifest `{rel_manifest}` has no package version: crate identity would be invented")
        })?
        .to_string();
    let mut deps = Vec::new();
    if let Some(table) = doc.get("dependencies").and_then(|v| v.as_table()) {
        for (key, value) in table {
            // `name = { path = ... }` and `name = "version"` both name the dep
            let dep_name = value
                .get("package")
                .and_then(|v| v.as_str())
                .unwrap_or(key.as_str());
            deps.push(dep_name.to_string());
        }
    }
    let manifest_dir = Path::new(rel_manifest)
        .parent()
        .map(|p| p.to_path_buf())
        .unwrap_or_default();
    let source_path = join_rel(&manifest_dir, "src/lib.rs");
    Ok(MemberManifest {
        name,
        version,
        deps,
        source_path,
    })
}

fn join_rel(dir: &Path, rel: &str) -> String {
    let mut owned = dir.to_path_buf();
    owned.push(rel);
    owned
        .components()
        .map(|c| c.as_os_str().to_string_lossy().to_string())
        .collect::<Vec<_>>()
        .join("/")
}

fn unit_scalar() -> Value {
    formats::obj(vec![
        ("shape", formats::s("scalar")),
        ("name", formats::s("unit")),
    ])
}

fn integer_scalar(min: i64, max: i64) -> Value {
    formats::obj(vec![
        ("shape", formats::s("scalar")),
        ("name", formats::s("integer")),
        ("min", formats::i(min)),
        ("max", formats::i(max)),
    ])
}

/// Map a Rust type to a v1 type value for the supported scalar subset.
fn scalar_type(ty: &syn::Type) -> Option<Value> {
    match ty {
        syn::Type::Tuple(tuple) if tuple.elems.is_empty() => Some(unit_scalar()),
        syn::Type::Paren(paren) => scalar_type(&paren.elem),
        syn::Type::Path(path) => {
            if path.qself.is_some() || path.path.segments.len() != 1 {
                return None;
            }
            let seg = path.path.segments.last()?;
            if !seg.arguments.is_empty() {
                return None;
            }
            match seg.ident.to_string().as_str() {
                "bool" => Some(formats::obj(vec![
                    ("shape", formats::s("scalar")),
                    ("name", formats::s("boolean")),
                ])),
                "u8" => Some(integer_scalar(0, 255)),
                "u16" => Some(integer_scalar(0, 65535)),
                "u32" => Some(integer_scalar(0, 4294967295)),
                "i8" => Some(integer_scalar(-128, 127)),
                "i16" => Some(integer_scalar(-32768, 32767)),
                "i32" => Some(integer_scalar(-2147483648, 2147483647)),
                _ => None,
            }
        }
        _ => None,
    }
}

fn function_type(arguments: Vec<Value>, result: Value) -> Value {
    formats::obj(vec![
        ("shape", formats::s("function")),
        ("arguments", formats::arr(arguments)),
        ("result", result),
    ])
}

fn opaque_type(item: &impl ToTokens) -> Value {
    formats::obj(vec![
        ("shape", formats::s("opaque")),
        (
            "fingerprint",
            formats::s(&formats::sha256_digest(item.to_token_stream().to_string().as_bytes())),
        ),
    ])
}

/// Walk one crate's source with syn, collecting slots, demand, and gaps.
struct SourceWalk<'a> {
    crate_name: String,
    dep_names: &'a [String],
    versions: &'a BTreeMap<String, String>,
    alias_map: BTreeMap<String, String>,
    module_prefix: Vec<String>,
    slots: Vec<SlotRecord>,
    demand: Vec<Value>,
    diagnostics: Vec<Diagnostic>,
    locations: Vec<Value>,
    complete: bool,
    callee_spans: BTreeSet<(usize, usize)>,
    current_file: String,
}

impl<'a> SourceWalk<'a> {
    fn gap(&mut self, code: &'static str, reason: String, complete_killer: bool) {
        if complete_killer {
            self.complete = false;
        }
        self.diagnostics.push(Diagnostic {
            code,
            severity: if complete_killer { "error" } else { "warning" },
            source: Some(self.current_file.clone()),
            reason,
        });
    }

    /// meaning id for a `crate::path` target from crate identity.
    fn meaning_of(&self, target: &str) -> Option<String> {
        let mut parts = target.split("::");
        let crate_name = parts.next()?;
        let version = self.versions.get(crate_name)?;
        let mut meaning = format!("{crate_name}.{version}");
        for seg in parts {
            meaning.push('.');
            meaning.push_str(seg);
        }
        Some(meaning)
    }

    fn record_slot(&mut self, name: String, meaning: String, ty: Value, span: proc_macro2::Span) {
        let loc = span.start();
        self.slots.push(SlotRecord { name, meaning, ty });
        self.locations.push(formats::obj(vec![
            ("slot", formats::s(&self.slots.last().expect("pushed").name)),
            ("file", formats::s(&self.current_file)),
            ("line", formats::i(loc.line as i64)),
            ("col", formats::i(loc.column as i64)),
        ]));
    }

    /// Inventory a public non-function declaration as an opaque slot with
    /// a formatting-invariant fingerprint; cfg-gated declarations also
    /// produce a gap because visibility cannot be established for a
    /// conditionally compiled item.
    fn opaque_pub_item(&mut self, ident: &proc_macro2::Ident, node: &impl ToTokens, cfg_gated: bool) {
        let slot_name = self.slot_name(&ident.to_string());
        let meaning = format!("{}.{}", self.crate_name, slot_name.replace("::", "."));
        let span = ident.span();
        let loc = span.start();
        self.slots.push(SlotRecord {
            ty: opaque_type(node),
            name: slot_name.clone(),
            meaning,
        });
        self.locations.push(formats::obj(vec![
            ("slot", formats::s(&slot_name)),
            ("file", formats::s(&self.current_file)),
            ("line", formats::i(loc.line as i64)),
            ("col", formats::i(loc.column as i64)),
        ]));
        if cfg_gated {
            self.gap(
                "unsupported-construct",
                format!("cfg-gated declaration `{slot_name}` is outside cfg-dependent analysis"),
                true,
            );
        }
    }

    fn slot_name(&self, suffix: &str) -> String {
        if self.module_prefix.is_empty() {
            format!("{}::{suffix}", self.crate_name)
        } else {
            format!(
                "{}::{}::{suffix}",
                self.crate_name,
                self.module_prefix.join("::")
            )
        }
    }

    fn path_key(path: &syn::Path) -> (usize, usize) {
        let start = path.span().start();
        (start.line, start.column)
    }

    fn record_demand(&mut self, callee: &str, span: proc_macro2::Span) {
        let mut resolved: Option<String> = None;
        let mut alias: Option<String> = None;
        let mut parts = callee.split("::");
        let head = parts.next().unwrap_or("");
        let rest: Vec<&str> = parts.collect();
        if rest.is_empty() {
            if let Some(target) = self.alias_map.get(head) {
                alias = Some(head.to_string());
                resolved = Some(target.clone());
            }
        } else if self.dep_names.iter().any(|d| d == head) {
            resolved = Some(callee.to_string());
        } else if !rest.is_empty()
            && head != "crate"
            && head != "self"
            && head != "super"
            && head != self.crate_name
        {
            // multi-segment path whose head is neither an explicit alias nor
            // a declared dependency: the demand mechanism is outside the
            // supported profile, so the inventory is incomplete (never
            // silently dropped)
            self.gap(
                "incomplete-demand",
                format!(
                    "demand `{callee}` cannot resolve: `{head}` is not a declared dependency of this crate"
                ),
                true,
            );
        }
        if let Some(target) = resolved {
            if let Some(provider_slot) = self.meaning_of(&target) {
                self.demand.push(formats::obj(vec![
                    ("consumer", formats::s(&self.crate_name)),
                    ("called", formats::s(&target)),
                    (
                        "alias",
                        match &alias {
                            Some(a) => formats::s(a),
                            None => Value::Null,
                        },
                    ),
                    ("provider_slot", formats::s(&provider_slot)),
                ]));
                let loc = span.start();
                self.locations.push(formats::obj(vec![
                    ("slot", formats::s(&target)),
                    ("file", formats::s(&self.current_file)),
                    ("line", formats::i(loc.line as i64)),
                    ("col", formats::i(loc.column as i64)),
                ]));
            } else {
                // dep-qualified call whose provider source/manifest is not
                // in the bundle: the demand cannot be resolved, so the
                // inventory is incomplete (never silently dropped)
                self.gap(
                    "incomplete-demand",
                    format!(
                        "demand `{target}` cannot resolve: provider source is not supplied in the bundle"
                    ),
                    true,
                );
            }
        }
    }
}

impl<'a> Visit<'a> for SourceWalk<'a> {
    fn visit_item_mod(&mut self, node: &'a syn::ItemMod) {
        let name = node.ident.to_string();
        let is_public = matches!(node.vis, syn::Visibility::Public(_));
        let cfg_gated = node.attrs.iter().any(attr_is_cfg);
        if is_public && cfg_gated {
            self.gap(
                "unsupported-construct",
                format!("cfg-gated module `{name}` is outside cfg-dependent analysis"),
                true,
            );
        }
        match &node.content {
            Some((_, _items)) if is_public && !cfg_gated => {
                self.module_prefix.push(name);
                syn::visit::visit_item_mod(self, node);
                self.module_prefix.pop();
            }
            None => {
                self.gap(
                    "unsupported-construct",
                    format!("non-inline module `{name}` requires file resolution"),
                    true,
                );
            }
            // private modules carry no public API surface
            Some((_, _items)) => {}
        }
    }

    fn visit_item_fn(&mut self, node: &'a syn::ItemFn) {
        let is_public = matches!(node.vis, syn::Visibility::Public(_));
        let name = node.sig.ident.to_string();
        if is_public {
            let has_cfg = node.attrs.iter().any(attr_is_cfg);
            let shape_supported = !has_cfg
                && node.sig.generics.params.is_empty()
                && node.sig.constness.is_none()
                && node.sig.asyncness.is_none()
                && node.sig.unsafety.is_none()
                && node.sig.abi.is_none();
            let mut args_ok = true;
            let mut arg_types: Vec<Value> = Vec::new();
            for input in &node.sig.inputs {
                if matches!(input, syn::FnArg::Receiver(_)) {
                    args_ok = false;
                    break;
                }
                match input {
                    syn::FnArg::Typed(typed) => match scalar_type(&typed.ty) {
                        Some(t) => arg_types.push(t),
                        None => {
                            args_ok = false;
                            break;
                        }
                    },
                    _ => {
                        args_ok = false;
                        break;
                    }
                }
            }
            let result_ok = match &node.sig.output {
                syn::ReturnType::Default => Some(unit_scalar()),
                syn::ReturnType::Type(_, ty) => scalar_type(ty),
            };
            if shape_supported && args_ok {
                let qualified = if self.module_prefix.is_empty() {
                    name.clone()
                } else {
                    format!("{}::{}", self.module_prefix.join("::"), name)
                };
                let target = format!("{}::{}", self.crate_name, qualified);
                let meaning = self
                    .meaning_of(&target)
                    .unwrap_or_else(|| format!("{}.{}", self.crate_name, qualified));
                self.record_slot(
                    self.slot_name(&name),
                    meaning,
                    function_type(arg_types, result_ok.expect("unit fallback")),
                    node.sig.ident.span(),
                );
            } else {
                let slot_name = self.slot_name(&name);
                let meaning = format!("{}.{}", self.crate_name, slot_name.replace("::", "."));
                self.slots.push(SlotRecord {
                    ty: opaque_type(node),
                    name: slot_name.clone(),
                    meaning,
                });
                self.gap(
                    "unsupported-construct",
                    format!(
                        "public function `{slot_name}` is outside the {PROFILE} signature subset"
                    ),
                    true,
                );
            }
        }
        syn::visit::visit_item_fn(self, node);
    }

    fn visit_item_impl(&mut self, node: &'a syn::ItemImpl) {
        self.gap(
            "unsupported-construct",
            "method implementations are outside the supported profile".to_string(),
            true,
        );
        for item in &node.items {
            if let syn::ImplItem::Fn(method) = item {
                if matches!(method.vis, syn::Visibility::Public(_)) {
                    let slot_name = self.slot_name(&method.sig.ident.to_string());
                    self.slots.push(SlotRecord {
                        ty: opaque_type(method),
                        name: slot_name.clone(),
                        meaning: format!("{}.{}", self.crate_name, slot_name.replace("::", ".")),
                    });
                }
            }
        }
    }

    fn visit_item_trait(&mut self, node: &'a syn::ItemTrait) {
        self.gap(
            "unsupported-construct",
            format!("trait `{}` is outside the supported profile", node.ident),
            true,
        );
    }

    fn visit_item_struct(&mut self, node: &'a syn::ItemStruct) {
        if matches!(node.vis, syn::Visibility::Public(_)) {
            self.opaque_pub_item(&node.ident, node, node.attrs.iter().any(attr_is_cfg));
        }
        syn::visit::visit_item_struct(self, node);
    }

    fn visit_item_enum(&mut self, node: &'a syn::ItemEnum) {
        if matches!(node.vis, syn::Visibility::Public(_)) {
            self.opaque_pub_item(&node.ident, node, node.attrs.iter().any(attr_is_cfg));
        }
        syn::visit::visit_item_enum(self, node);
    }

    fn visit_item_const(&mut self, node: &'a syn::ItemConst) {
        if matches!(node.vis, syn::Visibility::Public(_)) {
            self.opaque_pub_item(&node.ident, node, node.attrs.iter().any(attr_is_cfg));
        }
        syn::visit::visit_item_const(self, node);
    }

    fn visit_item_static(&mut self, node: &'a syn::ItemStatic) {
        if matches!(node.vis, syn::Visibility::Public(_)) {
            self.opaque_pub_item(&node.ident, node, node.attrs.iter().any(attr_is_cfg));
        }
        syn::visit::visit_item_static(self, node);
    }

    fn visit_item_type(&mut self, node: &'a syn::ItemType) {
        if matches!(node.vis, syn::Visibility::Public(_)) {
            self.opaque_pub_item(&node.ident, node, node.attrs.iter().any(attr_is_cfg));
        }
        syn::visit::visit_item_type(self, node);
    }

    fn visit_item_foreign_mod(&mut self, _node: &'a syn::ItemForeignMod) {
        self.gap(
            "unsupported-construct",
            "FFI declarations are outside the supported profile".to_string(),
            true,
        );
    }

    fn visit_item_macro(&mut self, node: &'a syn::ItemMacro) {
        let head = node
            .mac
            .path
            .segments
            .last()
            .map(|s| s.ident.to_string())
            .unwrap_or_default();
        self.gap(
            "unsupported-construct",
            format!("macro `{head}!` may generate declarations the profile cannot inventory"),
            true,
        );
        self.gap(
            "incomplete-demand",
            format!("macro `{head}!` may introduce usages the profile cannot inventory"),
            true,
        );
        // deliberately not descended: macro bodies are unexpanded input
    }

    fn visit_expr_macro(&mut self, node: &'a syn::ExprMacro) {
        let head = node
            .mac
            .path
            .segments
            .last()
            .map(|s| s.ident.to_string())
            .unwrap_or_default();
        self.gap(
            "incomplete-demand",
            format!("macro invocation `{head}!` may introduce usages the profile cannot inventory"),
            true,
        );
    }

    fn visit_expr_method_call(&mut self, node: &'a syn::ExprMethodCall) {
        self.gap(
            "incomplete-demand",
            format!(
                "returned-object method call `.{}` is outside the supported demand profile",
                node.method
            ),
            true,
        );
    }

    fn visit_expr_call(&mut self, node: &'a syn::ExprCall) {
        if let syn::Expr::Path(path) = &*node.func {
            let callee: String = path
                .path
                .segments
                .iter()
                .map(|s| s.ident.to_string())
                .collect::<Vec<_>>()
                .join("::");
            let key = Self::path_key(&path.path);
            self.callee_spans.insert(key);
            self.record_demand(&callee, path.path.span());
        }
        syn::visit::visit_expr_call(self, node);
    }

    fn visit_expr_path(&mut self, node: &'a syn::ExprPath) {
        let callee: String = node
            .path
            .segments
            .iter()
            .map(|s| s.ident.to_string())
            .collect::<Vec<_>>()
            .join("::");
        let is_demand_shaped = self.alias_map.contains_key(callee.as_str())
            || self
                .dep_names
                .iter()
                .any(|d| callee.starts_with(&format!("{d}::")));
        if is_demand_shaped && !self.callee_spans.contains(&Self::path_key(&node.path)) {
            self.gap(
                "incomplete-demand",
                format!("function-pointer flow `{callee}` is outside the supported demand profile"),
                true,
            );
        }
        syn::visit::visit_expr_path(self, node);
    }
}

fn collect_use_tree(
    tree: &syn::UseTree,
    prefix: String,
    alias_map: &mut BTreeMap<String, String>,
    gaps: &mut Vec<String>,
) {
    match tree {
        syn::UseTree::Name(use_name) => {
            let local = use_name.ident.to_string();
            alias_map.insert(local.clone(), format!("{prefix}{local}"));
        }
        syn::UseTree::Rename(rename) => {
            let local = rename.rename.to_string();
            alias_map.insert(local, format!("{prefix}{}", rename.ident));
        }
        syn::UseTree::Path(use_path) => {
            collect_use_tree(
                &use_path.tree,
                format!("{prefix}{}::", use_path.ident),
                alias_map,
                gaps,
            );
        }
        syn::UseTree::Glob(_) => {
            gaps.push("glob reexports are outside the supported profile".to_string());
        }
        syn::UseTree::Group(use_group) => {
            for grouped in &use_group.items {
                collect_use_tree(grouped, prefix.clone(), alias_map, gaps);
            }
        }
    }
}

fn attr_is_cfg(attr: &syn::Attribute) -> bool {
    let Some(seg) = attr.path().segments.last() else {
        return false;
    };
    matches!(seg.ident.to_string().as_str(), "cfg" | "cfg_attr")
}

/// Extract the local-1 records for one bundle from a validated request.
/// `Err` classifies as error (exit 2); `Ok` carries the gap-aware outcome.
/// Parse workspace member manifests from the committed bundle bytes.
fn load_workspace(
    loaded: &BTreeMap<String, Vec<u8>>,
) -> Result<Vec<MemberManifest>, String> {
    let root_manifest_bytes = loaded
        .get("Cargo.toml")
        .ok_or("input-mismatch: bundle has no committed Cargo.toml")?;
    let root_text = std::str::from_utf8(root_manifest_bytes)
        .map_err(|e| format!("malformed Cargo.toml: {e}"))?;
    let root_doc: toml::Value =
        toml::from_str(root_text).map_err(|e| format!("malformed Cargo.toml: {e}"))?;
    let member_manifests: Vec<String> = match root_doc.get("workspace").and_then(|w| w.get("members"))
    {
        Some(members) => members
            .as_array()
            .ok_or("workspace members must be an array")?
            .iter()
            .filter_map(|m| m.as_str().map(str::to_string))
            .map(|m| format!("{m}/Cargo.toml"))
            .collect(),
        None => vec!["Cargo.toml".to_string()],
    };
    let mut manifests = Vec::new();
    for rel in &member_manifests {
        let text = loaded
            .get(rel)
            .ok_or_else(|| format!("input-mismatch: bundle file `{rel}` unreadable"))?;
        let text = std::str::from_utf8(text).map_err(|e| format!("malformed `{rel}`: {e}"))?;
        manifests.push(parse_member_manifest(rel, text)?);
    }
    Ok(manifests)
}

/// Walk every member crate's source; accumulates slots, demand, gaps.
fn walk_crates(
    manifests: &[MemberManifest],
    loaded: &BTreeMap<String, Vec<u8>>,
    versions: &BTreeMap<String, String>,
    out: &mut WalkAccumulator,
) -> Result<(), String> {
    for manifest in manifests {
        let source_bytes = loaded.get(&manifest.source_path).ok_or_else(|| {
            format!(
                "input-mismatch: bundle file `{}` unreadable",
                manifest.source_path
            )
        })?;
        let source_text = std::str::from_utf8(source_bytes)
            .map_err(|e| format!("malformed `{}`: {e}", manifest.source_path))?;
        let file: syn::File = syn::parse_file(source_text).map_err(|e| {
            format!(
                "unsupported-construct: parse failure in `{}`: {e}",
                manifest.source_path
            )
        })?;
        // pre-pass: collect import aliases before any body walk so demand
        // resolution never depends on `use` item position in the file
        let mut alias_map: BTreeMap<String, String> = BTreeMap::new();
        let mut use_gaps: Vec<String> = Vec::new();
        for item in &file.items {
            if let syn::Item::Use(use_item) = item {
                collect_use_tree(
                    &use_item.tree,
                    String::new(),
                    &mut alias_map,
                    &mut use_gaps,
                );
            }
        }
        for reason in use_gaps {
            out.diagnostics.push(Diagnostic {
                code: "unsupported-construct",
                severity: "error",
                source: Some(manifest.source_path.clone()),
                reason,
            });
            out.complete = false;
        }
        let mut walk = SourceWalk {
            crate_name: manifest.name.clone(),
            dep_names: &manifest.deps,
            versions,
            alias_map,
            module_prefix: Vec::new(),
            slots: Vec::new(),
            demand: Vec::new(),
            diagnostics: Vec::new(),
            locations: Vec::new(),
            complete: true,
            callee_spans: BTreeSet::new(),
            current_file: manifest.source_path.clone(),
        };
        walk.visit_file(&file);
        out.complete = out.complete && walk.complete;
        out.slots.append(&mut walk.slots);
        out.demand.append(&mut walk.demand);
        out.diagnostics.append(&mut walk.diagnostics);
        out.locations.append(&mut walk.locations);
    }
    Ok(())
}

struct WalkAccumulator {
    slots: Vec<SlotRecord>,
    demand: Vec<Value>,
    diagnostics: Vec<Diagnostic>,
    locations: Vec<Value>,
    complete: bool,
}

/// Cross-check every demand entry against the supplied provider slots.
/// Merely scanning identifier strings never establishes resolution: a
/// demand whose target is absent from the provider's declared inventory
/// (removed, renamed, private, or unsupported-signature slot) is a
/// completeness gap, never a silently resolved in-slot.
fn check_demand_resolution(
    all_slots: &[SlotRecord],
    all_demand: &[Value],
    diagnostics: &mut Vec<Diagnostic>,
    complete: &mut bool,
) {
    let meanings: BTreeSet<&str> = all_slots.iter().map(|s| s.meaning.as_str()).collect();
    for entry in all_demand {
        let called = entry.str_field("called").unwrap_or_default();
        let provider_slot = entry.str_field("provider_slot").unwrap_or_default();
        if !meanings.contains(provider_slot) {
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
fn resolve_in_slots(
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
        });
    }
    Ok(in_slots)
}

/// Assemble the canonical v1 contract document from slots and in-slots.
fn assemble_contract(
    all_slots: &[SlotRecord],
    in_slots: &[SlotRecord],
) -> (Value, Vec<String>) {
    let mut contract_slots: Vec<Value> = Vec::new();
    let mut slot_names: Vec<String> = Vec::new();
    for record in all_slots.iter().chain(in_slots.iter()) {
        let polarity = if in_slots.iter().any(|s| s.name == record.name) {
            "in"
        } else {
            "out"
        };
        contract_slots.push(formats::obj(vec![
            ("name", formats::s(&record.name)),
            ("meaning", formats::s(&record.meaning)),
            ("polarity", formats::s(polarity)),
            ("facet", formats::s("api")),
            ("type", record.ty.clone()),
            ("required", Value::Bool(true)),
            (
                "default",
                formats::obj(vec![("present", Value::Bool(false))]),
            ),
        ]));
        slot_names.push(record.name.clone());
    }
    contract_slots.sort_by(|a, b| {
        a.str_field("name")
            .unwrap_or_default()
            .cmp(b.str_field("name").unwrap_or_default())
    });
    slot_names.sort();
    let contract = formats::obj(vec![
        ("schema_version", formats::s("1")),
        ("kind", formats::s("contract")),
        ("slots", formats::arr(contract_slots)),
        ("tombstones", formats::arr(Vec::new())),
        ("laws", formats::arr(Vec::new())),
        ("relations", formats::arr(Vec::new())),
        ("sunsets", formats::arr(Vec::new())),
    ]);
    (contract, slot_names)
}

/// Extract the local-1 records for one bundle from a validated request.
/// `Err` classifies as error (exit 2); `Ok` carries the gap-aware outcome.
pub fn extract(request: &Value) -> Result<ExtractionOutcome, String> {
    let (bundle_root, files) = validate_request(request)?;
    let bundle_root = bundle_root
        .canonicalize()
        .map_err(|e| format!("input-mismatch: bundle root unreadable: {e}"))?;
    let loaded = load_bundle(&bundle_root, &files)?;
    let manifests = load_workspace(&loaded)?;

    let mut versions: BTreeMap<String, String> = BTreeMap::new();
    for manifest in &manifests {
        versions.insert(manifest.name.clone(), manifest.version.clone());
    }

    let mut accumulated = WalkAccumulator {
        slots: Vec::new(),
        demand: Vec::new(),
        diagnostics: Vec::new(),
        locations: Vec::new(),
        complete: true,
    };
    walk_crates(&manifests, &loaded, &versions, &mut accumulated)?;
    check_demand_resolution(
        &accumulated.slots,
        &accumulated.demand,
        &mut accumulated.diagnostics,
        &mut accumulated.complete,
    );

    let in_slots = resolve_in_slots(&accumulated.slots, &accumulated.demand)?;
    let (contract, slot_names) = assemble_contract(&accumulated.slots, &in_slots);

    let mut demand_sorted = accumulated.demand;
    demand_sorted.sort_by(|a, b| {
        a.str_field("called")
            .unwrap_or_default()
            .cmp(b.str_field("called").unwrap_or_default())
    });
    let demand = formats::obj(vec![
        ("version", formats::s(LOCAL_VERSION)),
        ("kind", formats::s("demand")),
        ("entries", formats::arr(demand_sorted)),
    ]);

    let mut file_records = Vec::new();
    for (rel, bytes) in &loaded {
        file_records.push(formats::obj(vec![
            ("path", formats::s(rel)),
            ("raw_digest", formats::s(&formats::sha256_digest(bytes))),
        ]));
    }
    let provenance = formats::obj(vec![
        ("version", formats::s(LOCAL_VERSION)),
        ("kind", formats::s("provenance")),
        ("bundle_root", formats::s(&bundle_root.to_string_lossy())),
        ("files", formats::arr(file_records)),
        ("locations", formats::arr(accumulated.locations)),
    ]);

    let diagnostic_values: Vec<Value> = accumulated
        .diagnostics
        .iter()
        .map(Diagnostic::to_value)
        .collect();
    let report = formats::obj(vec![
        ("version", formats::s(LOCAL_VERSION)),
        ("kind", formats::s("extraction-report")),
        ("profile", formats::s(PROFILE)),
        ("complete_inventory", Value::Bool(accumulated.complete)),
        ("diagnostics", formats::arr(diagnostic_values.clone())),
    ]);

    Ok(ExtractionOutcome {
        contract,
        demand,
        provenance,
        report,
        complete_inventory: accumulated.complete,
        diagnostics: diagnostic_values,
        slot_names,
    })
}
