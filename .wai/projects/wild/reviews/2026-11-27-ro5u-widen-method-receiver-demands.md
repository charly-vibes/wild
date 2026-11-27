# RO5U review — widen-method-receiver-demands (bd wild-8j4)

**Date:** 2026-11-27 · **Scope:** `src/extract.rs`, `src/extract/method_demands.rs`, `src/extract/mod_files.rs`, `src/extract/type_inventory.rs`, `tests/runtime/test_extract.py`. Working tree also holds other agents' in-flight edits (`bump.rs`, `feedback.rs`, `genesis.rs`, `main.rs`, `v1.rs`, `tests/v1_checker.rs`) — out of scope, untouched.

## Critical

None.

## High

None.

## Medium

1. **Implicit pre-pass skip on unparseable mod files** — `src/extract/method_demands.rs` (`BundlePrepass::scan_mod_declarations`): invalid-UTF-8 and parse-failure mod files are skipped with `continue`. Acceptable: `mod_files::resolve_mod_file` still emits the named `unsupported-construct` gap during the demand walk, so nothing is silently lost; the skip is only implicit. Concrete fix if revisited: surface a pre-pass note alongside the walk gap.
2. **`self`-resolution gate is impl-level, not method-level** — `src/extract/type_inventory.rs` (`account_impl`): context is set when the inherent impl has ≥1 public fn method, so `self` calls in *private* methods of a *mixed* impl resolve to typed demands (naming private paths that then fail inventory resolution honestly). A private-only impl keeps receiver gaps. Documented in the comment; consistent with D3 (private methods carry no public API surface). Alternative: per-method gate — rejected as less faithful to "public inherent impl" in the design.

## Low

3. **Per-file clone of shared maps** — `src/extract.rs` (`walk_crates` pass 2): `shared_fn_tys`/`shared_field_tys` cloned per bundle file. Small bundles make it negligible; `Arc` later if bundles grow.
4. **Pre-existing scan_impl shape** — multi-segment self types (`impl crate::Meter`) record impl-method keys under the current module (wild-158 incumbent behavior). The new `current_impl_type` gate is stricter (single-segment self types only), so no new drift introduced; noted for a future declared fix.

## Verified dimensions

- **Determinism:** all new state `BTreeMap`; diagnostics order preserved by the two-pass structure (alias gaps pushed in manifest order in pass 2); let-binding and re-assignment invalidation are source-order single-pass — calls before a re-assignment were resolved against the then-correct type, calls after keep the gap (never retroactively cured).
- **Spec conformance:** delta requirement mirrored rule-for-rule (bundle-wide pre-pass, let-bound single-assignment locals, inventoried field access, `self`/`Self` in public inherent impls, hop-folded chains); residual gap list matches (`incomplete-demand` naming the receiver, trait-impl `self` keeps the D3 `unsupported-construct` gap too). Delta says "re-assigned local", not "`let mut`" — `let mut` binds unless re-assigned.
- **Tests:** 9 new receiver-widening tests red→green; 6 pre-existing `widen` tests (one-hop ctor, absent-method, unbounded chain, enum variants, determinism) stay green: 15 passed.
