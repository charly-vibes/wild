# Design: add-string-signature-support

Context: `scalar_type` in `src/extract.rs` is the single gate for the
rust-cargo-local-1 signature subset (public free-fn arguments and returns).
Text-taking public functions currently take the unsupported-construct gap path
(wild-73j branch), producing opaque slots and incomplete inventory. This change
adds text scalars to that subset only.

## Decisions

### D1 — Type identity is conservative (three distinct type identities)

- `String` → scalar name `text-owned`
- `&str` and `&String` → scalar name `text-borrowed`
- Both shapes: `{"shape":"scalar","name":...}` with NO `min`/`max` fields
  (text is unbounded; mirrors the `boolean` precedent).

The conservative subtype table (`is_subtype` in `src/check.rs`) already Breaks
on scalar-name mismatch, so owned↔borrowed confusion can never yield a false
Holds. Verify with tests; do not edit the table unless a test proves a gap.

### D2 — Normalization: `&String` maps to `text-borrowed`

Deref coercion is standard Rust semantics, not a widening. `&mut str` /
`&mut String` stay unsupported: mutable borrows are outside the v1
value-transfer model → unsupported-construct gap as today.

### D3 — Bare `str` and other text-like types remain unsupported

`char`, `Cow`, `Vec<u8>`, and generic arguments keep the existing gap path,
unchanged.

### D4 — Scope: signature subset only

Public free fn arguments + returns. No changes to demand resolution, macro
support, or the subtype/accretion checker beyond what D1 implies
(name-equality already handles text scalars). `scalar_type`'s only call sites
are the signature-subset paths in `visit_item_fn`, so the slice is bounded by
construction.

## Test shape

Runtime tests mirror `test_public_fn_with_non_scalar_return_is_opaque_gap_not_panic`:

- Red/green test: provider with `pub fn shout(x: &str) -> String`,
  `pub fn owned_len(s: String) -> u32`, `pub fn alias_len(s: &String) -> u32`
  — after green: rc=0, complete inventory, function-type slots whose arguments
  and results carry `text-borrowed`/`text-owned` scalars. Red: rc=1 refusal
  with `unsupported-construct` gaps.
- Guard test (green today, stays green): `&mut str` argument keeps the
  unsupported-construct refusal and an opaque slot.

## Risks

- Schema enum: `schemas/wild-v1.schema.json` currently enumerates scalar names
  `unit|boolean|string|bytes`. Runtime extraction does not schema-validate
  emitted contracts, and the schema/docs mirrors are deferred to archive time
  (mh5.5 precedent) — disclosed in proposal.md.
- Held-out freeze: the extractor binary digest changes; the next held-out
  re-run (wild-f4i) re-freezes per its existing machinery. Out of scope here.
