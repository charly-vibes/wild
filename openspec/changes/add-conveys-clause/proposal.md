# Change: Add a conveys clause for well-behaved conveyance

## Why

Pass-through components (proxies, pipes, registries, middleware) route input
they do not interpret. Today wild has no way to certify that: an unknown input
slot at a path the component merely forwards is treated as unextracted demand
and refused, so honest conveyance is indistinguishable from silent dropping.
Research lesson 8 (.wai/projects/semantic-composition/research/
2026-10-21-lessons-from-hickey-in-context-clojure-conj.md — "well-behaved
conveyance", the `excess` idea: select + excess = all) proposes the fix as a
contract clause. Ticket: wild-hyk.

## What Changes

- Contracts MAY declare a `conveys` clause: a list of input paths whose
  unknown slots are forwarded, not interpreted.
- Extraction records a conveyance claim scoped to the declared paths instead
  of refusing for unextracted demand at those paths.
- INVARIANT (unchanged): conveyance narrows what is *interpreted*
  (extraction-level); it never narrows what is *validated* —
  `scoped_substitution` stands unchanged: restricting demand never hides
  newly introduced required inputs, including under conveyed paths.
- New normative rows in the wild-compose Constraints/Properties tables plus a
  mirrored Requirement; contract tests pin the claim-not-reject behavior and
  the validation-unchanged interaction.

## Impact

- Specs: `openspec/specs/wild-compose/spec.md` (constraint
  `conveys_forwarding_scoped`, two deriving unit properties, Requirement
  mirror, acceptance case).
- Code: v1 contract format + extraction/check verdict paths.
- Tests: red-first contract tests wired to a new espectacular contract TOML.
