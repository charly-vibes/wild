# subtype-is-preorder — evidence

## Identification

Baseline candidate 2 of bd wild-wz9; refined from the suite-level
`properties/wild.md` entry, re-verified at 4e26885.

- Dispatch: `subtype`, `src/v1.rs:546-614` — scalars `:616` (interval
  containment; interval-less integer → Unknown), records `:678` (required-B
  fields present and subtype in A; A-emitted fields accepted by B; extra A
  fields need open B; open A needs open B), sums `:763` (named variants with
  subtype payloads unless B open; open A needs open B), sequences/maps
  (item/value covariance with contained length/cardinality intervals),
  functions `:583-590` (contravariant arguments, covariant result), opaque
  (identical fingerprint only).
- Verdict meet: `Verdict::and` — Unknown dominates Holds; any definite
  violation dominates Unknown (three-valued, fail-closed, `src/v1.rs:543-545`).

## What goes wrong if violated

`accretes` composes `subtype` verdicts per slot (`src/v1.rs:859,898,919,966`);
a non-transitive Holds would let an accretion chain diverge from its composed
relation exactly as the tombstone witness does. A self-Breaks would make an
identity step a hard failure — contradicting
`tests/v1_checker.rs:194-201` (identical contract accretes) at the type level.

## Existing instrumentation vs. missing

`tests/v1_checker.rs` covers fixed pairs: interval containment
(`:125-134`), opaque Unknown-not-guess (`:138-143`), extra-field/open rules
(`:146-172`), function contravariance (`:176-190`). No generated relation
laws; no reflexivity/transitivity checks. `validate_type` is private
(`src/v1.rs:287`), so validity currently enters only through
`validate_contract` on a whole document (`src/v1.rs:98`).

## Seam

- Interim (no code change): wrap each generated type as the `type` of a
  single input slot in a minimal contract, call public `validate_contract`,
  and treat `Err` as generator rejection. This exercises exactly
  `validate_type` plus the slot-level checks, which is the intended
  validity notion.
- Preferred (wild-dr2): a `pub` seam for `validate_type` — matches
  suite-level `evaluation/implementability.md` finding I2 (major). Without
  it, a generator bug that produces a whole-contract-invalid type silently
  shrinks coverage.

## Generator sketch (recursive types)

- Depth-bounded recursive type values: scalars (`unit`, `boolean`, `integer`
  with optional `min`/`max` at and across the ±9007199254740991 bounds,
  `string`, `bytes` as `{base64: ...}`), records (fields with required flags,
  optional `open` + `closed_reason` on closure), sums (named variants, open/
  closed), sequences/maps with inclusive length/cardinality intervals,
  function types (bounded arity), opaque fingerprints.
- Validity constraints by construction: `min ≤ max`, closed declarations
  carry non-empty `closed_reason` (`closure-unjustified` otherwise), defaults
  inhabit types (not relevant at type level but needed if slots are built),
  finite trees (v1 forbids cyclic type references).
- Law checks per generated (a, b, c): reflexivity `subtype(a,a) != Breaks`;
  transitivity Holds∘Holds → Holds; Breaks symmetry
  `Breaks(a,b) ⟹ Breaks(b,a)` — kept as a separate Hegel test so a
  lower-confidence hypothesis cannot mask the core laws.

## Predicted red/green

- **GREEN** predicted for reflexivity-never-Breaks and Holds-transitivity:
  each shape rule is a conjunction of interval/field containments, and
  containment is transitive; Unknown short-circuits to non-Holds, never to a
  false Breaks. This is a hypothesis from reading, not an executed check —
  the point of the property is to confirm it.
- **Breaks symmetry:** lower confidence. Records where B lacks a field A
  emits break one direction and depend on openness in the other
  (`src/v1.rs:678-760`); write it, but be ready to split or restate it if the
  first run contradicts the prediction.

**Open Questions:**

- Should an interval-less integer type be a *valid* type at all? `(partial: code treats it as valid-but-Unknown — scalar_subtype returns Unknown without an interval; the format doc does not forbid it)`
  - Examined: `src/v1.rs:616-640`, `validate_type` interval handling
    (`src/v1.rs:375`, `interval`), `docs/wild-formats-v1.md` §Contract IR
    ("integer types specify inclusive min and max, with min ≤ max").
  - Found: `validate_type` accepts an integer type with no interval;
    `scalar_subtype` then cannot establish inclusion (Unknown), including
    reflexively.
  - Conclusion: the property conditions on `validate_type`-valid types and
    states reflexivity as never-Breaks; if the owner later forbids
    interval-less integers, the generator drops them and reflexivity can be
    restated as always-Holds.
