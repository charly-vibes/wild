# Change: Update the openness default to open with justified closure

## Why

Records and sums in the contract IR default to **closed**: consumers must
tolerate additions only where the provider explicitly declared openness
(`polarity_openness_declared`: "default closed"; `src/v1.rs` `is_open()` falls
back to `false`). Rich Hickey's "In Context" (Clojure/Conj 2026) argues the
opposite default for *information* — facts about the world flowing between
parts: require what you need, never reject what you didn't ask about
("it is not wrong to pass more stuff"). wild's own verdict philosophy agrees
(scope claims, never print bare "compatible"), but the type vocabulary
prohibits by default — the one place in the design where the default posture is
prohibition rather than selection.

The resolution adopted here is *open by default, closure justified*: a record
or sum may still be closed (mechanisms are contrivances; the author writes all
the rules), but closure must be a declared, reasoned decision rather than an
unstated default.

**Why this can be a v1-in-place change:** wild has no released tool, no
registry, and no persisted contracts (a design with a prototype — see
`openspec/project.md`). The v1 wire schema *requires* explicit `open` on every
record and sum, so every contract ever extracted (including the adopt-audit
extractions in `results/`) declares openness explicitly; nothing relies on the
prose default or the checker fallback. There is no compatibility surface to
protect. This window closes the day wild 1.0 ships with adoption — after that,
an openness-default change would require the version-scoped IR-v2 machinery
(documented in the design's alternatives).

Grounding: the wai research artifact
`.wai/projects/semantic-composition/research/2026-10-21-lessons-from-hickey-in-context-clojure-conj.md`
(lesson 7 and tension A);
`openspec/specs/wild-core/spec.md` `polarity_openness_declared`,
`slot_shapes_closed`; `schemas/wild-v1.schema.json` (record and sum definitions
require explicit `open` today).

## What Changes

- Flip the v1 openness default: `open` becomes *optional* in the wire schema,
  omitting it means `true`, and a `closed` declaration must carry a non-empty
  `closed_reason` justification string. `schema_version` stays `"1"`.
- Update the prose rule (`polarity_openness_declared`), the formats reference's
  openness sections, the shared schema, and the checker (`is_open` fallback
  becomes `true`; the reader resolves the effective value; unjustified closure
  is rejected with a named diagnostic).
- `canonical()` stays generic and type-unaware: an omitted `open` and an
  explicit `open: true` are different bytes and therefore different revision
  ids — semantically equal, trivially accreting, documented.
- No changes to accretion semantics: the directional rules (closed output sum
  growth is a break; input sum growth is an accretion; open requires open per
  `binding_well_formed`) hold unchanged. Only the *default* and the
  *justification requirement* change.

## Impact

- Affected specs: `wild-core` (openness polarity), and the formats reference
  and shared schema it points to.
- Affected code: `src/v1.rs` (openness resolution, unjustified-closure
  diagnostic), `src/formats.rs` (schema-level parsing of the optional field),
  plus their tests.
- Not affected: tombstones (tension B stays a chosen prohibition), demand
  extraction, composition/resolver rules, certificates, adopt/deploy levels,
  `schema_version` acceptance.
- Out of scope (filed as beads issues): the `conveys` conveyance clause and
  `on_absent: fallible` required inputs, both from the same lessons doc.
