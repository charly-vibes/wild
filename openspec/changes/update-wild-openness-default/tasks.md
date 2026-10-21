# Tasks: update-wild-openness-default

Ordered red → green → refactor where implementation is touched; corpus and
schema work precedes code so the contract tests have something normative to
check against.

## 1. Spec corpus (specodelic)

- [ ] 1.1 Update `openspec/specs/wild-core/spec.md`: revise
      `polarity_openness_declared` to state version-scoped defaults (v1
      explicit/closed-convention; v2 open-by-default) and justified closure;
      keep the explicit-value property `closed_output_growth_is_break`
      unchanged and add property rows for the v2 omitted-`open` accretion case
      and the missing-`closed_reason` rejection case.
- [ ] 1.2 Run `spk lint openspec/specs` and `spk graph openspec/specs`; both
      green (no dangling references, no drift findings).

## 2. Shared formats and schema

- [ ] 2.1 Extend `docs/wild-formats-v1.md` with a "wire schema_version 2"
      section (and adjust the doc title to cover both versions): optional
      `open`, effective-openness resolution, `closed_reason` requirement and
      break-on-edit rule, cross-version rule.
- [ ] 2.2 Update `schemas/wild-v1.schema.json` with the v2 record/sum
      definition (`open` optional, default true; `closed_reason` required when
      false) while keeping the v1 definitions intact; schema validates as
      draft 2020-12.
- [ ] 2.3 Contract test: the schema gate accepts a v2 record omitting `open`
      and rejects a v2 `open: false` without `closed_reason`.

## 3. Checker (Rust)

- [ ] 3.1 Write the failing tests first: version-aware openness fallback in
      `src/v1.rs` (`is_open` → `false` for v1, effective `true` for a v2
      omitted field), canonical-form materialization of the effective value,
      and the named diagnostic for unjustified closure.
- [ ] 3.2 Implement until green: `schema_version` awareness in
      `src/v1.rs`/`src/formats.rs` (the refusal path at
      `src/main.rs`'s "unknown schema_version" check gains `"2"` as an
      accepted value; the field itself is unchanged); no behavior change for
      v1 inputs (existing v1 test suite stays green unmodified).
- [ ] 3.3 Refactor pass: fold duplicated openness-resolution logic into one
      `effective_openness(version, type)` helper; tidy separately from the
      feature commit.
- [ ] 3.4 Create the `.espectacular/wild-core/` contract TOMLs for the six
      v2 scenarios (one per scenario, scoped to its single test — see the
      `scenario-scoped-tests` playbook; `ah scenario new` resolves
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
