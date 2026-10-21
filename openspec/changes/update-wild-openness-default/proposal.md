# Change: Update the openness default to open with justified closure (IR v2)

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

Grounding: the wai research artifact
`.wai/projects/semantic-composition/research/2026-10-21-lessons-from-hickey-in-context-clojure-conj.md`
(lesson 7 and tension A);
`openspec/specs/wild-core/spec.md` `polarity_openness_declared`,
`slot_shapes_closed`; `schemas/wild-v1.schema.json` (both record and sum
already *require* explicit `open`, so v1 contracts are unaffected by a default
change — no re-hashing, no lineage churn).

## What Changes

- Introduce an IR schema version bump (v2) in which record and sum `open` is
  *optional, defaulting to `true`* when omitted, and a `closed` declaration
  must carry a non-empty `closed_reason` justification string.
- v1 contracts are version-tagged and stay exactly as they are: explicit
  `open`, closed-by-convention in authoring, unchanged hashes, unchanged
  verdicts. The v1 checker fallback (`is_open()` → `false`) remains the v1
  behavior; v2 fallback is `true`.
- Update the specodelic corpus (`wild-core` `polarity_openness_declared` and
  derived properties), the v1 formats reference (new v2 section), and the JSON
  Schema to carry the v2 shape.
- No changes to accretion semantics: the directional rules (closed output sum
  growth is a break; input sum growth is an accretion; open requires open per
  `binding_well_formed`) hold unchanged. Only the *default* and the
  *justification requirement* change.

## Impact

- Affected specs: `wild-core` (openness polarity), and indirectly the formats
  reference and shared schema it points to (`slot_shapes_closed` precedent:
  this is an IR schema version change, not a mere contract-hash change).
- Affected code: `src/v1.rs` (version-aware openness fallback), `src/formats.rs`
  (canonical form for the optional field), plus their tests.
- Not affected: tombstones (tension B stays a chosen prohibition), demand
  extraction, composition/resolver rules, certificates, adopt/deploy levels.
- Out of scope (filed as beads issues): the `conveys` conveyance clause and
  `on_absent: fallible` required inputs, both from the same lessons doc.
