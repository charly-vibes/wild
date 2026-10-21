# Design: openness default (IR v2)

## Decision

Version-scoped defaults, explicit migration-free stability:

1. **v1 is frozen.** Every v1 record/sum already serializes `open` explicitly
   (schema `required` lists it), so "default closed" in v1 is prose + checker
   fallback + authoring convention. None of that changes. Existing revision
   hashes, lineage ancestry, and verdicts are untouched — the hash-churn risk
   raised in the lessons doc does not materialize, because there are no
   default-relying v1 contracts to reinterpret.
2. **v2 defaults open.** In schema version 2, `open` becomes optional on
   records and sums; omission means `open: true`. Canonical form in v2
   materializes the effective value, so identity remains content-addressed and
   stable (`canonical_form_stable`).
3. **Closure is justified.** A v2 record/sum with `open: false` must carry
   `closed_reason`: a non-empty, human-authored string. This is the
   Hickey-consistent move — mechanisms may forbid, but the author must say why.
   The reason is part of the canonical form (immutable within a lineage, per
   `name_meaning_immutable`).

## Why not the alternatives

- **Keep closed default (status quo).** Preserves conservatism but leaves the
  information-programming posture as prohibition-by-default, contradicting the
  selection-not-prohibition rule the rest of wild already follows. Rejected.
- **Flip the v1 default in place.** Would silently reinterpret existing
  contracts and require re-hashing or a re-interpretation layer; breaks
  content-addressed identity (`identity_content_addressed`). Rejected.
- **Classify records as "external facts" vs "mechanisms" and default by
  class.** Requires a semantic classification the IR has no vocabulary for;
  the checker would be guessing intent. The justification field achieves the
  same outcome with no classification machinery. Rejected.

## Ripple analysis

- **Accretion checks.** Unchanged semantics; v2 omissions resolve to open
  before the directional rules apply, so no new accretion cases.
- **Subtyping.** `binding_well_formed`'s "open provider sum binds only to an
  open consumer" applies to effective openness in both versions; a v1 (explicit)
  and v2 (defaulted) contract interoperate through their effective values.
- **Cross-version checks.** A v2 candidate against a v1 ancestor uses each
  contract's own version's default. Mixed-version lineages are the migration
  surface; the checker rejects cross-version ambiguity only where effective
  openness cannot be resolved (never silently).
- **Schema.** Draft 2020-12: `open` moves out of `required` for the v2
  definition, `closed_reason` added conditionally on `open == false`
  (`if`/`then` keywords).
- **Tests keyed to closed default.** `closed_output_growth_is_break` and the
  `polarity_openness_declared` scenarios remain valid — they declare explicit
  values. New scenarios cover: omitted `open` in v2 (accretes), v2 closed
  without `closed_reason` (rejected with a named diagnostic), v2 closed with
  reason (allowed, break rules apply as before).

## Naming

Change id `update-wild-openness-default`; the v2 openness rules land in the
`wild-core` capability alongside the existing polarity constraint.
