# Tasks

## 1. Derivation mapping (wild-registry `declared_bump_derived`)

- [ ] 1.1 Red: contract tests for the mappings — ADDED-only delta →
  minor/accretes; MODIFIED-or-REMOVED present → major/revokes; RENAMED →
  major (revoke+accrete); multi-change aggregation → single class; empty
  requirement-level delta (row-only additions) → patch; missing base corpus →
  Unknown + named diagnostic, no class proposed.
  Tests fail first.
- [ ] 1.2 Deploy specodelic rows to `openspec/specs/wild-registry/spec.md`:
  constraint `declared_bump_derived` (effect — give it an observing row so
  the observability advisory stays clean; budget extra ah TOMLs per the
  implementor-deviation pattern), deriving unit properties for the mappings,
  mirrored Requirement text identical to the delta.
- [ ] 1.3 Land ah contract TOMLs for the deployed scenarios (after rows —
  orphan-TOML ordering), `ah check` green.
- [ ] 1.4 Green: implement the derivation step; 1.1 tests pass; `just test`.

## 2. Upward-only override (wild-registry `bump_override_upward_only`)

- [ ] 2.1 Red: contract tests — raise with recorded reason carries reason to
  the confirmed claim; lowering attempt refused with
  `bump_class_lowering_refused`, proposed class stands.
- [ ] 2.2 Deploy rows: constraint `bump_override_upward_only` + deriving
  property, mirrored Requirement; ah TOMLs; `ah check` green.
- [ ] 2.3 Green: implement override; 2.1 tests pass.

## 3. Declared-claim record (wild-adopt `declared_bump_recorded`)

- [ ] 3.1 Red: contract tests — derived+confirmed class recorded per release;
  audit lists agreement/disagreement vs computed verdict; disagreement never
  silently reconciled; absent declaration stays Unknown claim, excluded from
  agreement counts.
- [ ] 3.2 Deploy rows to `openspec/specs/wild-adopt/spec.md`: constraint
  `declared_bump_recorded` + deriving property, mirrored Requirement; ah
  TOMLs; `ah check` green.
- [ ] 3.3 Green: implement record; 3.1 tests pass.

## 4. Tidy (separate commits from greens)

- [ ] 4.1 Refactor derivation core for the totality property: every
  well-formed delta shape maps to exactly one class (property test).
- [ ] 4.2 Advisory wiring into the release flow as proposal output only — no
  gate, no exit-code coupling (`shadow_never_blocks` stance).

## 5. Validation

- [ ] 5.1 `ah check --run-tests` zero findings; `just ci` green.
- [ ] 5.2 Manual: run derivation over a testaruda historical pair; confirm
  declared class matches the hand-verified bump for that release.
