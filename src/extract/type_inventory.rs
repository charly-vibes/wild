// Purpose: type-level inventory accounting for the rust-cargo-local-1
//   profile (beads wild-158) — public enums inventory their variants as
//   named slots (design ruling D2), and impl blocks are accounted per
//   construct (design ruling D3) instead of a blanket blocking gap.
// Responsibilities: own the enum-variant slot rules (variants replace the
//   single opaque enum item, cfg-gated variants and generic enums keep the
//   honest gap).
// Rationale: keeping inventory semantics out of extract.rs honors the
//   pretender line-count ratchet (mirroring extract/mod_files.rs) and makes
//   the "gaps never cure silently" rule auditable in one place.

use super::*;

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
