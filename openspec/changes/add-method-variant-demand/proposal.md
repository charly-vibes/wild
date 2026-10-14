# Change: Widen the rust-cargo-local-1 demand profile (method calls + enum variants)

## Why

The cdp.4 re-audit (`results/adopt-audit-cdp4-1841.txt`) measured all 12
consecutive testaruda release pairs abstaining (refuse/Unknown, exit 1) on
`incomplete-demand` + `unsupported-construct`, with the residual gap
composition measured and ordered: blanket impl-block gaps (19 occurrences in
0.5.5), returned-object method calls (the majority of the 81
incomplete-demand), enum-variant demand paths (`AdapterError::Io`), and
public fns outside the scalar signature subset. Delegation ticket wild-158
pre-approves the scope rulings D1–D7 for widening the two candidate
categories — method-call demand and enum-variant demand — while keeping the
honest gap everywhere the bounded profile cannot resolve a shape.

## What Changes

- **Method-call demand (D1)**: `visit_expr_method_call` no longer
  blanket-gaps. The receiver resolves only in bounded shapes — a path
  expression resolving through the bounded demand rules, or a call whose
  head resolves to an inventoried same-crate constructor/free fn with a
  recorded syntactic return type. On resolution the method call creates the
  demand `<crate>::<Type>::<method>`, validated against the inventory
  (public impl-method opaque slot or typed slot): inventoried → supported
  demand (counterexample-capable), absent → `incomplete-demand` gap naming
  the full path. Receivers outside the bounded shapes (multi-hop chains
  beyond one resolved hop, field access, macro output, unknown identifiers)
  keep the honest `incomplete-demand` gap naming the receiver. No type
  inference beyond the bounded shapes (D7).
- **Enum-variant inventory + demand (D2)**: a public enum inventories its
  variants as named slots (`<Enum>::<Variant>` under the enum's qualified
  meaning) instead of a single opaque enum item; variant demand paths
  resolve as supported demand when the variant is inventoried; unknown
  variant paths keep the `incomplete-demand` gap naming the path. Variant
  slots follow the identity law (crate identity + qualified path, never
  line numbers).
- **Impl-block gap discipline (D3)**: the blanket "method implementations
  are outside the supported profile" `unsupported-construct` gap is
  replaced by per-construct accounting: public impl methods inventory as
  type-qualified opaque slots (existing behavior, kept but now
  type-qualified), plain-private impl items carry no public API surface,
  and the blocking gap is emitted only for impl items the profile genuinely
  cannot represent (restricted `pub(crate)`/`pub(in)` items, trait impls).
  Never silent: whatever remains unsupported keeps a named gap.
- **Signature subset unchanged (D4)**: the unit/bool/i8–u32/text typed-fn
  signature subset stays exactly as-is; non-scalar fns keep opaque-slot +
  `unsupported-construct` treatment.
- New resolution logic lives in new modules under `src/extract/`
  (`method_demands.rs`, `type_inventory.rs`) to honor the extract.rs
  1200-line ratchet (D6). Schema `schemas/wild-local-v1.schema.json`
  unchanged. `docs/wild-local-v1.md` gains the supported-set description.
- `tests/runtime/test_extract.py`: red-first `-k widen` conformance
  fixtures covering the supported and refusal shapes.

**No breaking change** to the request envelope: the profile id stays
`rust-cargo-local-1`.

## Impact

- Affected specs: `wild-extract` (MODIFIED requirements: Bounded
  deterministic Rust extraction — variant inventory + impl accounting;
  Explicit consumer demand coverage — bounded method-call demand + variant
  demand paths)
- Affected code: `src/extract.rs` (visit delegates, `fn_return_tys`
  field), `src/extract/method_demands.rs` (new), `src/extract/type_inventory.rs`
  (new), `src/extract/mod_files.rs` (per-file return-type pre-pass hook)
- Affected docs: `docs/wild-local-v1.md`
- Measured via `python3 experiments/wild_adopt_audit.py --crate testaruda`
  re-run recorded as `results/adopt-audit-158-<n>.txt`
