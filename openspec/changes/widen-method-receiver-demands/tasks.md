# Tasks: widen-method-receiver-demands

## 1. Bundle-wide pre-pass (cross-file constructors)

- [x] 1.1 Red: contract test — a consumer whose code in one module calls a
  public fn declared in another module of the same bundle, whose return type
  is a recorded single-segment path type, and whose result's methods are
  called in a later statement; assert the method demand resolves with no
  incomplete-demand gap. Same for an impl-method constructor declared in
  another file. Tests fail first.
- [x] 1.2 Green: run the return-type pre-pass over the whole bundle before
  any demand walk (replace the per-file `scan_fn_returns` invocation);
  ordering stays deterministic (bundle file order as supplied).
- [x] 1.3 Contract test — determinism guard: extracting the same bundle
  twice yields identical semantic bytes with the widened pre-pass.

## 2. Declared receiver shapes

- [x] 2.1 Red: contract tests, one per shape —
  - let-bound single-assignment local (`let r = Meter::new(); r.tick();`)
    resolves to `Meter::tick`;
  - let-bound from a recorded-return free fn resolves;
  - field-access receiver (`obj.field.method()` and
    `let f = obj.field; f.method()`) resolves via an inventoried public
    field type;
  - `self`/`Self` receiver inside a public inherent impl body resolves to
    the impl's type;
  - two-hop chain with recorded return types on both callees resolves
    fully (`Meter::new().tick().double()`).
  Tests fail first.
- [x] 2.2 Red: honest-gap tests, one per residual —
  - re-bound local (`let mut r = …; r = …;`) and initializer outside the
    resolved-call shape keep the gap naming the receiver;
  - tuple indexing, private-field access, unknown field keep the gap;
  - `self` in a trait-impl body keeps the named unsupported-construct gap;
  - first chain hop without a recorded return type keeps the gap naming
    the receiver while earlier resolved hops keep their recorded demands;
  - every widened resolution whose method is absent from the inventory
    keeps the `incomplete-demand` gap naming the full
    `<crate>::<Type>::<method>` path and refuses scoped acceptance.
  Tests fail first (the gap cases already pass; assert them to lock the
  rule against rule-creep).

## 3. Deploy specodelic rows

- [x] 3.1 Deploy rows to `openspec/specs/wild-extract/spec.md`: the
  MODIFIED "Bounded method-call resolution" and MODIFIED "Unbounded
  method-call receivers stay disclosed" Requirements mirrored exactly from
  the delta, with constraint/property rows per the house pattern (deriving
  unit properties for the new shapes and the residual-gap locks, observing
  rows so the observability advisory stays clean), ah contract TOMLs after
  rows (orphan-TOML ordering), `ah check` green.
- [x] 3.2 `spk lint openspec` and `openspec validate --all --strict` clean.

## 4. Green implementation

- [x] 4.1 Implement the receiver rules in `src/extract/method_demands.rs`
  and the field-type recording in `src/extract/type_inventory.rs`;
  1.1/2.1/2.2 tests pass; `just test`.
- [x] 4.2 Keep the receiver-shape rule set capped at the five declared
  rules — no heuristics, no fallback inference; anything new needs its own
  declared rule and scenario first.

## 5. Measured gate

- [x] 5.1 Re-run the adopt-audit harness that produced
  `results/adopt-audit-158-1.txt` (testaruda 0.1.0→0.5.5 consecutive pairs);
  record before/after abstention rate and the residual named-gap list as a
  new `results/` file; per the wild-8j4 follow-up threshold, the gap-rate
  measurement is the deliverable.
- [x] 5.2 Confirm the residual gap list partitions into: external-crate
  demands (bd wild-90d's set), unsupported-signature slots (D3), and
  genuinely-unresolvable receiver shapes — no new unexplained categories.

## 6. Tidy

- [x] 6.1 Update the manual's demand-profile section
  (`docs/wild-manual.md`) to describe the five declared receiver shapes and
  the residual disclosure.
- [x] 6.2 File the Option A follow-up ticket (typed-receiver facts as
  extraction inputs) referencing this design's A-section, if the maintainer
  wants it tracked.
