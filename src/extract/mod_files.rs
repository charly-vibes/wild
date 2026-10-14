// Purpose: non-inline module-file resolution for the rust-cargo-local-1
//   profile (beads wild-cdp.4) — resolving `pub mod name;` declarations to
//   their committed files so adopt verdicts ground on real fleet code.
// Responsibilities: own the mod-path candidate rules (entry files and
//   mod.rs resolve in their own directory; other files in a stem-named
//   sibling directory), bundle-only file lookup, UTF-8/parse refusals, and
//   the scoped alias merge for the resolved file's walk.
// Rationale: keeping resolution semantics out of extract.rs honors the
//   pretender line-count ratchet (mirroring extract/macro_demands.rs) and
//   makes the "gaps never cure silently" rule auditable in one place.

use super::*;

/// Resolve a public non-inline module (`pub mod name;`) to its file
/// inside the committed bundle and walk it as part of the public
/// inventory (wild-cdp.4). Candidates follow Rust's mod-path rules
/// relative to the declaring file: `src/name.rs` and
/// `src/name/mod.rs`, nested under the declaring file's stem
/// (`src/outer.rs` declares into `src/outer/`). An absent file keeps
/// the honest gap — missing files never cure silently.
pub(super) fn resolve_mod_file(walk: &mut SourceWalk, name: &str, cfg_gated: bool) {
    let path = Path::new(&walk.current_file);
    let dir = path.parent().unwrap_or_else(|| Path::new(""));
    let stem = path
        .file_stem()
        .map(|s| s.to_string_lossy().to_string())
        .unwrap_or_default();
    // rustc's mod-path rule: mod.rs and the crate-entry files (lib.rs,
    // main.rs) resolve their modules in their own directory; any other
    // file resolves them in a sibling directory named after its stem
    // (`src/outer.rs` declares into `src/outer/`)
    let base = if matches!(stem.as_str(), "mod" | "lib" | "main") {
        dir.to_path_buf()
    } else {
        dir.join(&stem)
    };
    let candidates = [
        join_rel(&base, &format!("{name}.rs")),
        join_rel(&base, &format!("{name}/mod.rs")),
    ];
    let Some(rel) = candidates
        .iter()
        .find(|c| walk.loaded.contains_key(c.as_str()))
        .cloned()
    else {
        walk.gap(
            "unsupported-construct",
            format!("non-inline module `{name}` requires file resolution"),
            true,
        );
        return;
    };
    if cfg_gated {
        walk.gap(
            "unsupported-construct",
            format!("cfg-gated module `{name}` is outside cfg-dependent analysis"),
            true,
        );
    }
    let bytes = match walk.loaded.get(&rel) {
        Some(bytes) => bytes,
        None => unreachable!("candidate membership checked above"),
    };
    let text = match std::str::from_utf8(bytes) {
        Ok(text) => text,
        Err(e) => {
            walk.gap(
                "unsupported-construct",
                format!("module file `{rel}` is not valid UTF-8: {e}"),
                true,
            );
            return;
        }
    };
    let file = match syn::parse_file(text) {
        Ok(file) => file,
        Err(e) => {
            walk.gap(
                "unsupported-construct",
                format!("parse failure in `{rel}`: {e}"),
                true,
            );
            return;
        }
    };
    // module-file use items scope their aliases to that file (plus its
    // nested modules), mirroring the lib.rs pre-pass: merge over the
    // enclosing aliases for the duration of this file's walk only
    let mut scoped = walk.alias_map.clone();
    let mut use_gaps: Vec<String> = Vec::new();
    for item in &file.items {
        if let syn::Item::Use(use_item) = item {
            collect_use_tree(&use_item.tree, String::new(), &mut scoped, &mut use_gaps);
        }
    }
    for reason in use_gaps {
        walk.gap("unsupported-construct", reason, true);
    }
    let prev_file = std::mem::replace(&mut walk.current_file, rel);
    let prev_aliases = std::mem::replace(&mut walk.alias_map, scoped);
    walk.module_prefix.push(name.to_string());
    // per-file pre-pass for the resolved module file (wild-158 D1): the
    // module prefix is already pushed, so keys match the demand walk's
    SourceWalk::scan_fn_returns(walk, &file.items);
    walk.visit_file(&file);
    walk.module_prefix.pop();
    walk.alias_map = prev_aliases;
    walk.current_file = prev_file;
}
