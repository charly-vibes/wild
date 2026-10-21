# Tasks: update-wild-openness-default

Ordered red → green → refactor where implementation is touched; corpus and
schema work precedes code so the contract tests have something normative to
check against.

## 1. Spec corpus (specodelic)

- [ ] 1.1 Update `openspec/specs/wild-core/spec.md`: revise
      `polarity_openness_declared` to state the open default and justified
      closure (drop "default closed"); keep the explicit-value property
      `closed_output_growth_is_break` unchanged and add property rows for the
      omitted-`open` accretion case and the missing-`closed_reason` rejection
      case.
- [ ] 1.2 Run `spk lint openspec/specs` and `spk graph openspec/specs`; both
      green (no dangling references, no drift findings).

## 2. Shared formats and schema

- [ ] 2.1 Revise the openness sections of `docs/wild-formats-v1.md` in place:
      optional `open` (omission = open), effective-openness resolution,
      `closed_reason` requirement and break-on-edit rule, distinct-ids-
      accreting note for omitted versus explicit-true. `schema_version` stays
      `"1"`.
- [ ] 2.2 Update `schemas/wild-v1.schema.json`: `open` leaves the `required`
      arrays for record and sum definitions; `closed_reason` added
      conditionally on `open == false` (`if`/`then` keywords).
- [ ] 2.3 Contract test: the schema gate accepts a record omitting `open` and
      rejects an `open: false` without `closed_reason`.

## 3. Checker (Rust)

- [ ] 3.1 Write the failing tests first: `is_open` fallback becomes `true`,
      the reader resolves the effective value, unjustified closure is rejected
      with a named diagnostic, and omitted-open versus explicit-true contracts
      get distinct revision ids while accreting each other.
- [ ] 3.2 Implement until green in `src/v1.rs`/`src/formats.rs`; existing
      explicitly-declaring v1 fixtures stay green unmodified.
- [ ] 3.3 Refactor pass: fold duplicated openness-resolution logic into one
      `effective_openness(ty)` helper; tidy separately from the feature commit.
- [ ] 3.4 Create the `.espectacular/wild-core/` contract TOMLs for the five
      v1-default scenarios (one per scenario, scoped to its single test — see
      the `scenario-scoped-tests` playbook; `ah scenario new` resolves
      `--requirement` by exact requirement heading). Done at apply time, when
      the tests they bind to exist — design-stage declaration placeholders
      would be fake verification.

## 4. Docs and bookkeeping

- [ ] 4.1 Update `docs/wild-manual.md` openness row (concepts table) and
      §5.2 verdict table rows that mention closed sums.
- [ ] 4.2 Update the wai research artifact
      `.wai/projects/semantic-composition/research/2026-10-21-lessons-from-hickey-in-context-clojure-conj.md`
      tension A to resolved-by-proposal status (point here).
- [ ] 4.3 `just test` green; `openspec validate update-wild-openness-default --strict` green before apply; `ah check --changes update-wild-openness-default` green; spk lint green after archive.
