# Change: Add string signature support to the rust-cargo-local-1 profile

## Why

The wild-m7f.4 held-out re-run proved the wild arm's remaining held-out Unknowns
trace to the provider-side signature subset: public functions taking or returning
text (`&str`, `String`, `&String`) fall outside `scalar_type` in `src/extract.rs`,
so they emit `unsupported-construct` gaps with opaque slots and the extraction is
refused as incomplete. The v1 IR already defines a text scalar domain
(`docs/wild-formats-v1.md`: scalar domains are `unit`, `boolean`, `integer`,
`string`, `bytes`), so supporting text scalars in public signatures is genuine
runtime semantics — OpenSpec territory per `experiments/heldout/README.md`
ruling 1 — and never a fixture rewrite to manufacture agreement.

## What Changes

- `src/extract.rs` (`scalar_type` only): `String` maps to the scalar
  `text-owned`; `&str` and `&String` normalize to the scalar `text-borrowed`
  (deref coercion is standard Rust semantics, not a widening). Both emit
  `{"shape":"scalar","name":...}` with no `min`/`max` fields — text is
  unbounded, mirroring the `boolean` precedent.
- Conservative type identity: owned and borrowed text are distinct scalar
  names. The subtype checker already requires identical scalar spelling
  (`is_subtype` breaks on name mismatch), so owned↔borrowed confusion can never
  yield a false Holds. No checker edits.
- Still unsupported — gap path unchanged: `&mut str`, `&mut String` (mutable
  borrows are outside the v1 value-transfer model), bare `str`, `char`, `Cow`,
  `Vec<u8>`, and generic arguments.
- `tests/runtime/test_extract.py`: red-first conformance fixtures for the new
  text-scalar signature behavior and the retained refusal shape.
- Deferred to archive time (not this change): `schemas/wild-v1.schema.json`
  scalar-name enum and `docs/wild-formats-v1.md` mirrors, per the mh5.5
  archive-time mirror precedent.

**No breaking change** to the request envelope: the profile id stays
`rust-cargo-local-1`.

## Impact

- Affected specs: `wild-extract` (MODIFIED requirement: Bounded deterministic
  Rust extraction)
- Affected code: `src/extract.rs` (`scalar_type`),
  `tests/runtime/test_extract.py`
- Unaffected: demand resolution, macro handling, the subtype/accretion checker,
  the held-out machinery, the other nine spec capabilities
