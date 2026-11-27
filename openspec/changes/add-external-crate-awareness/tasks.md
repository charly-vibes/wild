# Tasks: add-external-crate-awareness

## 1. Stage C — typed incomplete-demand reasons (zero-trust)

- [ ] 1.1 Red: contract tests — an unresolved demand into `std::…` is
  emitted with reason `std-item` (or `external-crate-unmodeled` for
  non-std crate heads); an unresolved demand whose slot exists as an
  unsupported-signature slot carries `unsupported-signature`; a method call
  on an unresolvable receiver carries `unresolved-receiver`; a bounded
  demand naming an absent target carries `unknown-target`; every existing
  gap message still names the target. Refusal behavior unchanged. Tests
  fail first.
- [ ] 1.2 Deploy rows to `openspec/specs/wild-extract/spec.md`: ADDED
  "Typed incomplete-demand disclosure reasons" mirrored from the delta
  (constraint + deriving unit property + observing row per the house
  pattern), ah contract TOMLs after rows (orphan-TOML ordering), `ah check`
  green.
- [ ] 1.3 Green: implement reason tagging at gap emission in
  `src/extract/demand_resolution.rs` and the gap emitters;
  1.1 tests pass; `just test`.
- [ ] 1.4 Measurement: re-run the adopt-audit harness
  (`results/adopt-audit-158-1.txt` harness); record the residual-cause
  distribution as a new `results/` file — this is the before picture for
  stage A.

## 2. Stage A — declared external signature bundles

- [ ] 2.1 Format lane: extend the extraction request/bundle format
  (`docs/wild-formats-v1.md`, `schemas/wild-v1.schema.json`) to declare
  external signature inventories — crate name, content digest, provenance
  (generating tool + version, upstream crate version). No implicit std
  entry: std is declared like any other crate.
- [ ] 2.2 Red: contract tests —
  - a demand resolving against a declared, digest-matching external
    inventory records the demand with `origin: external` and the supplying
    digest;
  - the same external name without a declared inventory keeps the typed
    gap (`external-crate-unmodeled`);
  - a digest mismatch is an input-binding failure requiring fresh
    extraction;
  - the extraction report and the emitted contract carry the external
    digest set used;
  - a check consuming a contract with external origins reports the digest
    set, and an unverifiable digest yields Unknown assurance, never a
    silent pass.
  Tests fail first.
- [ ] 2.3 Deploy rows: ADDED "Declared external signature bundles"
  mirrored from the delta (constraint + deriving unit properties + observing
  row), ah TOMLs, `ah check` green; `spk lint openspec` and
  `openspec validate --all --strict` clean.
- [ ] 2.4 Green: implement external-inventory loading (hashed input),
  origin-marked resolution in `src/extract/demand_resolution.rs`, and
  digest-set reporting; 2.2 tests pass; `just test`.
- [ ] 2.5 Bundle-author tooling: a step that runs the same extractor
  profile over a declared dependency to generate its signature inventory
  and record provenance (offline, over that dependency's supplied source).

## 3. Measured gate

- [ ] 3.1 Re-run the adopt-audit harness on testaruda 0.1.0→0.5.5 with a
  bundle declaring std + testaruda's third-party deps; record before/after
  abstention rate and residual named-gap list in a new `results/` file;
  per the wild-90d follow-up threshold, the gap-rate measurement is the
  deliverable.
- [ ] 3.2 Confirm the residual gap list partitions into unsupported-
  signature slots, genuinely-unknown items, and — if any remain —
  typed `external-crate-unmodeled` entries naming undeclared externals
  (each one a deliberate abstention, not silence).

## 4. Tidy

- [ ] 4.1 Update the manual (`docs/wild-manual.md`): the trust model
  (declared digest-pinned external inventories, provenance, origin marking,
  no implicit std trust) and how a bundle author generates and declares an
  external inventory.
- [ ] 4.2 Record Option B's rejection and rationale in the change archive
  notes so the scope decision stays auditable.
