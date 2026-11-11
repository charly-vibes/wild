# Tasks: add-on-absent-fallible

## 1. Proposal

- [x] 1.1 Draft proposal + deltas for wild-core and wild-tiers (this change)

## 2. Red (tests first)

- [ ] 2.1 Failing contract tests: absent input at fallible slot → handled outcome not refusal; clause direction (gaining accretes / revoking breaks); fallible slot stays in closure validation; tier placement (scoped claim recorded, static verdict kinds unchanged)

## 3. Green (implementation)

- [ ] 3.1 Parse `on_absent` on required input slots (`src/formats.rs`, `docs/wild-formats-v1.md`, `schemas/wild-v1.schema.json`)
- [ ] 3.2 Demand/check semantics: fallible-absence outcome instead of caller-violation refusal (`src/check.rs`); accretion direction in the accretion checker (`src/update.rs`)
- [ ] 3.3 Deploy spec rows: wild-core `absence_as_policy` + 3 properties; wild-tiers `absence_observed_at_runtime` + 1 property; mirrored Requirements in both deployed specs

## 4. Gates

- [ ] 4.1 `spk lint openspec/specs` clean; `openspec validate add-on-absent-fallible --strict` clean
- [ ] 4.2 `just ci` green; `ah check --run-tests` 0 findings
- [ ] 4.3 Tasks complete → mark all `[x]`
