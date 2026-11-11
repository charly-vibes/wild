# Tasks: add-conveys-clause

## 1. Proposal

- [x] 1.1 Draft proposal + delta for wild-compose (this change)

## 2. Red (tests first)

- [x] 2.1 Write failing contract tests: conveyed slot → scoped claim not refusal; uncovered path → refusal preserved; new required input under conveyed path still refused by `scoped_substitution`
- [x] 2.2 Add espectacular contract TOML (`.espectacular/wild-compose/`) mapping the new tests; `ah check` shows the expected red/correspondence state

## 3. Green (implementation)

- [x] 3.1 Parse `conveys` clause in the v1 contract format (`src/formats.rs`, `docs/wild-formats-v1.md`, `schemas/wild-v1.schema.json`) — parsing landed in `src/v1.rs` (contract semantics, shared id grammar) and `src/extract.rs` (request-level validation); format doc + schema updated as listed
- [x] 3.2 Extraction: declared-path unknown slots record a scoped conveyance claim instead of demand refusal (`src/extract.rs`, `src/extract/`, `src/check.rs` verdict path)
- [x] 3.3 Deploy spec rows to `openspec/specs/wild-compose/spec.md`: constraint `conveys_forwarding_scoped`, properties `conveyed_slot_claimed_not_rejected` + `conveyed_path_new_required_input_still_caught`, mirrored Requirement with acceptance cases

## 4. Gates

- [ ] 4.1 `spk lint openspec/specs` clean; `openspec validate add-conveys-clause --strict` clean
- [ ] 4.2 `just ci` green; `ah check --run-tests` 0 findings
- [ ] 4.3 Tasks complete → mark all `[x]`
