# Design: openness default (v1, in place)

## Decision

Flip the default inside v1. No version bump, no migration, no cross-version
machinery:

1. **Nothing relies on the old default.** The v1 wire schema requires explicit
   `open` on every record and sum, so every contract ever extracted (adopt
   audits, experiments) declares openness explicitly. The `is_open()`
   `unwrap_or(false)` fallback fires only on malformed or partial input —
   there are no legitimate v1 artifacts whose meaning changes. And with no
   released tool, registry, or persisted lineage, there is no deployment
   surface to migrate.
2. **`open` becomes optional; omission means open.** The schema drops `open`
   from `required` for record and sum definitions; the reader resolves the
   effective value. `schema_version` stays `"1"` — this is a pre-1.0 revision
   of the format, not a new format version.
3. **Closure is justified.** A record/sum with `open: false` must carry
   `closed_reason`: a non-empty, human-authored string. Mechanisms may forbid,
   but the author must say why. The reason is part of the canonical form
   (immutable within a lineage, per `name_meaning_immutable`). Because it is
   part of the canonical form, the accretion classification of an edit is
   fixed: any change to a record/sum's `open` value or `closed_reason` text is
   a break (consistent with "opening is a break" and with defaults immutability
   under `defaults_are_slots`). A justification typo costs a new lineage — the
   deliberate price of content-addressed identity, not an oversight.
4. **Canonicalization stays generic.** `formats::canonical` is type-unaware and
   stays that way: an omitted `open` and an explicit `open: true` serialize
   differently, hash differently, and land as distinct revision ids. They are
   semantically equal and trivially accrete each other; the format doc says so.
   (A type-aware canonicalizer that materialized defaults would buy hash
   unification at the cost of duplicating type semantics inside the
   canonicalizer — not worth it.)

## Why not the alternatives

- **Keep closed default (status quo).** Preserves conservatism but leaves the
  information-programming posture as prohibition-by-default, contradicting the
  selection-not-prohibition rule the rest of wild already follows. Rejected.
- **Version-scoped IR v2** (the previous draft of this change). Safe but
  unneeded: it assumed a population of existing v1 contracts and tooling to
  protect — cross-version resolution, mixed-version lineages, a dual schema —
  and wild has none. Insurance with zero beneficiaries is complexity. Rejected
  *for now*: if wild 1.0 ships with adoption, openness-default changes go
  through exactly that path.
- **Classify records as "external facts" vs "mechanisms" and default by
  class.** Requires a semantic classification the IR has no vocabulary for;
  the checker would be guessing intent. The justification field achieves the
  same outcome with no classification machinery. Rejected.

## Ripple analysis

- **Accretion checks.** Unchanged semantics; omissions resolve to open before
  the directional rules apply, so no new accretion cases. Omitted-open and
  explicit-true contracts accrete each other.
- **Subtyping.** `binding_well_formed`'s "open provider sum binds only to an
  open consumer" applies to effective openness; unchanged.
- **Schema.** Draft 2020-12: `open` moves out of `required` for record and sum
  definitions; `closed_reason` added conditionally on `open == false`
  (`if`/`then` keywords). `schema_version` const stays `"1"`.
- **Tests keyed to closed default.** `closed_output_growth_is_break` and the
  `polarity_openness_declared` scenarios remain valid — they declare explicit
  values. New scenarios cover: omitted `open` (accretes), closed without
  `closed_reason` (rejected with a named diagnostic), closed with reason
  (allowed, break rules apply as before), `closed_reason` text edit (break).
- **Existing local artifacts.** Audit/experiment extractions in `results/` all
  declare `open` explicitly; none change meaning or hash.

## Naming

Change id `update-wild-openness-default`; the openness rules land in the
`wild-core` capability alongside the existing polarity constraint.
