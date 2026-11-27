---
sut_path: /var/home/sasha/para/areas/dev/gh/charly/wild
commit: 4e26885ac3549052cc38394ff3695fa280a403df
updated: 2026-11-27
external_references:
  - path: /var/home/sasha/para/areas/dev/gh/charly/reports/hegel-eval-2026-11-16/README.md
    why: Suite-level Hegel evaluation this run extends.
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/property-catalog.md
    why: Suite-level catalog section "wild (c22c150)".
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/properties/wild.md
    why: Prior per-property evidence.
  - path: https://github.com/antithesishq/antithesis-skills
    why: antithesis-research skill (version 2026-11-12 6ba10e2).
  - path: https://hegel.dev/
    why: Engine under evaluation; crate `hegeltest` 0.52.7.
---

# Property relationships — wild

Three clusters over the four cataloged properties. Slugs match
`property-catalog.md`.

## Cluster: identity (canonical-is-normal-form at the base)

- `canonical-is-normal-form` underpins the other three. `type_identical`
  (`src/v1.rs`, `formats::canonical(a) == formats::canonical(b)`) decides
  tombstone immutability (`tombstone_history`, `src/v1.rs:943-946`) and the
  record/sum open-vs-closed checks; digest stability is how the CLI's
  `accretes-report` and `checker` fields identify documents.
- Dominance: a canonicalization defect can *mask* relation properties (two
  genuinely different types compare identical, letting an illegal accretion
  hold) or *fabricate* failures. Run `canonical-is-normal-form` first; a red
  there invalidates any green elsewhere.
- Generator sharing: the contract generator (sorted set arrays, id grammar,
  defaults) is shared between `accretes-is-transitive` and
  `cli-exit-envelope-contract`; the permutation machinery is shared with
  `canonical-is-normal-form`. Build the generator once, in that order.

## Cluster: tombstone chain (the transitivity hot path)

- `accretes-is-transitive` fails only through the interaction of
  `retained_inputs`' removal branch (`src/v1.rs:898`,
  `subtype(tombstone, old)`) and `tombstone_history`'s reactivation branch
  (`:966`, `subtype(old_tombstone, slot)`); the retained-input direction
  (`:919`, `subtype(old, new)`) is what the composed triple must satisfy.
- Direction: the two removal/reactivation orientations are the *only* code
  paths with opposing subtype directions; if the tombstone decision
  (`evaluation/synthesis.md`) aligns them, this cluster collapses to green
  and `subtype-is-preorder` transitivity becomes the surviving constraint.
- `subtype-is-preorder` and `accretes-is-transitive` are related but not
  dominance-coupled: `accretes` composes `subtype` verdicts per slot, so a
  `subtype` transitivity red would predict an `accretes` red, but not vice
  versa (the tombstone asymmetry is an `accretes`-only defect).

## Cluster: CLI envelope (projection of the internals)

- `cli-exit-envelope-contract` is downstream of everything: the envelope's
  `decision`/`assurance` fields are the CLI projection of `v1::accretes` and
  the check pipeline verdicts (`src/main.rs:704-828`), and the envelope bytes
  are produced by `formats::canonical`. It is a distinct property, not a
  duplicate: it pins exit codes, member set, and write-scope, none of which
  the in-process properties see.
- Guardrail: the subprocess state machine must not run inside the Landlock
  law sandbox (`src/harness.rs`); keep it in the normal test harness.
