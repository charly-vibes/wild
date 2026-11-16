# Change: Add declared-bump derivation — the maintainer-side declared-claim generator

## Why

`ddl upgrade` currently decides on "semver bump class and release age alone"
(add-wild-contract-bundle-convention proposal, rung-2 gap statement): the
declared bump is an author's guess, and `wild-adopt`'s
`past_claims_audited` invariant audits it against computed verdicts — but the
declared side it audits is hand-written and unverifiable at authoring time.

A Rule-of-5 review of the release/semver investigation (2026-11-16 session)
pinned the direction of evidence: version strings never establish accretion
edges (`wild-adopt/spec.md:19`, `history_reconstructed`) and
`wild-compose/spec.md:93` states the contribution as machine-checked labels.
The missing seam is the **maintainer-side declared-claim generator**: derive
the declared bump class from the reviewed spec-corpus delta itself, so the
audit loop compares a delta-derived declaration against computed verdicts
instead of vibes against verdicts.

Direction is pinned by the review (CORR-001): the classifier proposes, the
adopt layer audits, and the human can only bump upward — revocation already
passed review as a MODIFIED/REMOVED delta, so by derivation time the thinking
has happened; accretion is free.

Ticket: wild-zh6.

## What Changes

- **Declared-bump derivation (wild-registry)**: from the corpus delta between
  the base release and the candidate tree, derive exactly one bump class:
  ADDED-only → minor (accretes); any MODIFIED/REMOVED → major (revokes);
  empty corpus delta → patch; no computable base → Unknown with a named
  diagnostic. A missing base never yields a fabricated class.
- **Upward-only override (wild-registry)**: the maintainer may raise the
  proposed class (patch→minor→major) with a recorded reason; lowering is
  refused with the named diagnostic `bump_class_lowering_refused` and the
  proposed class stands.
- **Declared-claim record (wild-adopt)**: the proposed and confirmed classes
  are recorded per release so `past_claims_audited` compares declared vs
  computed; disagreements are listed and never silently reconciled; releases
  without a recorded declaration remain Unknown claims (status quo
  preserved).
- **Shadow-first stance**: v1 gates nothing — the derivation is advisory
  output in the release flow, consistent with `shadow_never_blocks`.
- **Out of scope**: standalone release-bundle diff tooling, per-profile
  extractor bump semantics (design note only), and per-tool release CI wiring
  (the fleet attach-bundle tickets own that).

## Impact

- Specs: `openspec/specs/wild-registry/spec.md` (constraints
  `declared_bump_derived`, `bump_override_upward_only` with deriving
  properties, mirrored Requirements),
  `openspec/specs/wild-adopt/spec.md` (constraint `declared_bump_recorded`,
  mirrored Requirement).
- Code: a new maintainer-side derivation step in the tool implementation
  (subcommand or release-flow step — implementation lane decides).
- Tests: red-first contract tests pinning the four delta→class mappings,
  the upward-only override, and the audit-record behavior; ah contract
  TOMLs land after row deployment (orphan-TOML ordering).
