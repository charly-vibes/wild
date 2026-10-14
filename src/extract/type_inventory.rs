// Purpose: type-level inventory accounting for the rust-cargo-local-1
//   profile (beads wild-158) — public enums inventory their variants as
//   named slots (design ruling D2), and impl blocks are accounted per
//   construct (design ruling D3) instead of a blanket blocking gap.
// Responsibilities: own the enum-variant slot rules (variants replace the
//   single opaque enum item, cfg-gated variants and generic enums keep the
//   honest gap) and the impl-block accounting (pub inherent methods
//   inventory as type-qualified opaque slots with versioned meanings,
//   plain private methods carry no public API surface, restricted-
//   visibility methods and trait impls keep named gaps, impl bodies are
//   walked so nothing inside them is silently dropped).
// Rationale: keeping inventory semantics out of extract.rs honors the
//   pretender line-count ratchet (mirroring extract/mod_files.rs) and makes
//   the "gaps never cure silently" rule auditable in one place.

use super::*;

/// Inventory a public enum (design ruling D2, beads wild-158): each variant
/// becomes a named slot `<crate>::<module>::<Enum>::<Variant>` under the
/// enum's qualified meaning, replacing the single opaque enum item. Variant
/// slots follow the identity law — crate identity plus qualified path,
/// never line numbers. Unknown-variant demand paths therefore fail
/// resolution against a named inventory instead of an opaque blob.
pub(super) fn inventory_enum(walk: &mut SourceWalk, node: &syn::ItemEnum) {
    let is_public = matches!(node.vis, syn::Visibility::Public(_));
    let cfg_gated = node.attrs.iter().any(attr_is_cfg);
    if is_public && !cfg_gated {
        if !node.generics.params.is_empty() {
            // a generic enum's variants cannot be inventoried as named
            // slots without inventing type-parameter identities: keep the
            // legacy opaque item and disclose the limitation
            walk.gap(
                "unsupported-construct",
                format!(
                    "generic public enum `{}` cannot be inventoried as named variant slots",
                    node.ident
                ),
                true,
            );
            walk.opaque_pub_item(&node.ident, node, false);
            return;
        }
        let enum_name = node.ident.to_string();
        for variant in &node.variants {
            if variant.attrs.iter().any(attr_is_cfg) {
                walk.gap(
                    "unsupported-construct",
                    format!(
                        "cfg-gated enum variant `{enum_name}::{}` is outside cfg-dependent analysis",
                        variant.ident
                    ),
                    true,
                );
                continue;
            }
            let slot_name = walk.slot_name(&format!("{enum_name}::{}", variant.ident));
            let meaning = walk.meaning_for_slot(&slot_name);
            walk.record_slot(
                slot_name.clone(),
                meaning,
                opaque_type(variant),
                variant.ident.span(),
            );
        }
        return;
    }
    // legacy shapes: cfg-gated public enums keep the opaque item plus the
    // cfg disclosure; non-public enums carry no public API surface
    if is_public {
        walk.opaque_pub_item(&node.ident, node, cfg_gated);
    }
}

/// How an impl item's visibility maps onto the public-API inventory.
enum VisibilityClass {
    Public,
    Restricted,
    Inherited,
}

fn visibility_class(vis: &syn::Visibility) -> VisibilityClass {
    match vis {
        syn::Visibility::Public(_) => VisibilityClass::Public,
        // syn parses `pub(crate)` as a restricted visibility with the `in`
        // token omitted, so both restricted shapes land here
        syn::Visibility::Restricted(_) => VisibilityClass::Restricted,
        syn::Visibility::Inherited => VisibilityClass::Inherited,
    }
}

/// Account one impl block per construct (design ruling D3, beads wild-158).
/// The blanket "method implementations are outside the supported profile"
/// gap is retired: public inherent methods inventory as type-qualified
/// opaque slots (`<crate>::<module>::<Type>::<method>`, versioned meaning)
/// so method-call demands resolve against them, plain private methods carry
/// no public API surface (exactly like private free fns), and the blocking
/// gap is emitted only for what the profile genuinely cannot represent —
/// trait impls and restricted-visibility (`pub(crate)`/`pub(in)`) items.
/// Whatever remains unsupported keeps a named gap; nothing is silent.
pub(super) fn account_impl(walk: &mut SourceWalk, node: &syn::ItemImpl) {
    let self_ty_name = match node.self_ty.as_ref() {
        syn::Type::Path(path) if path.qself.is_none() => {
            path.path.segments.last().map(|seg| seg.ident.to_string())
        }
        _ => None,
    };
    match (&node.trait_, self_ty_name) {
        (Some((_, trait_path, _)), _) => {
            let trait_name = trait_path
                .segments
                .last()
                .map(|seg| seg.ident.to_string())
                .unwrap_or_default();
            let self_ty_text = node.self_ty.to_token_stream().to_string();
            walk.gap(
                "unsupported-construct",
                format!(
                    "trait impl `{trait_name}` for `{self_ty_text}` is outside the supported profile"
                ),
                true,
            );
        }
        (None, None) => {
            let self_ty_text = node.self_ty.to_token_stream().to_string();
            walk.gap(
                "unsupported-construct",
                format!(
                    "impl on a non-path self type `{self_ty_text}` is outside the supported profile"
                ),
                true,
            );
        }
        (None, Some(ty_name)) => {
            for item in &node.items {
                match item {
                    syn::ImplItem::Fn(method) => match visibility_class(&method.vis) {
                        VisibilityClass::Public => {
                            let slot_name =
                                walk.slot_name(&format!("{ty_name}::{}", method.sig.ident));
                            let meaning = walk.meaning_for_slot(&slot_name);
                            walk.record_slot(
                                slot_name,
                                meaning,
                                opaque_type(method),
                                method.sig.ident.span(),
                            );
                        }
                        VisibilityClass::Restricted => {
                            walk.gap(
                                "unsupported-construct",
                                format!(
                                    "restricted-visibility impl method `{ty_name}::{}` is outside the supported profile",
                                    method.sig.ident
                                ),
                                true,
                            );
                        }
                        VisibilityClass::Inherited => {}
                    },
                    syn::ImplItem::Const(item) => account_non_fn_impl_item(
                        walk,
                        &ty_name,
                        "associated constant",
                        &item.ident.to_string(),
                        visibility_class(&item.vis),
                    ),
                    syn::ImplItem::Type(item) => account_non_fn_impl_item(
                        walk,
                        &ty_name,
                        "associated type",
                        &item.ident.to_string(),
                        visibility_class(&item.vis),
                    ),
                    syn::ImplItem::Macro(item) => {
                        let head = item
                            .mac
                            .path
                            .segments
                            .last()
                            .map(|seg| seg.ident.to_string())
                            .unwrap_or_default();
                        walk.gap(
                            "unsupported-construct",
                            format!(
                                "macro item `{head}!` inside impl `{ty_name}` is outside the supported profile"
                            ),
                            true,
                        );
                    }
                    _ => {
                        walk.gap(
                            "unsupported-construct",
                            format!("impl item inside `{ty_name}` is outside the supported profile"),
                            true,
                        );
                    }
                }
            }
        }
    }
    // walk the bodies: demands and method calls inside impl methods were
    // silently skipped before wild-158; per-construct accounting walks them
    // like free-fn bodies
    syn::visit::visit_item_impl(walk, node);
}

fn account_non_fn_impl_item(
    walk: &mut SourceWalk,
    ty_name: &str,
    kind: &str,
    ident: &str,
    class: VisibilityClass,
) {
    match class {
        VisibilityClass::Public | VisibilityClass::Restricted => {
            walk.gap(
                "unsupported-construct",
                format!("{kind} `{ty_name}::{ident}` is outside the supported profile"),
                true,
            );
        }
        VisibilityClass::Inherited => {}
    }
}
