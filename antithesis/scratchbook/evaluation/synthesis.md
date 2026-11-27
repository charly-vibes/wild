---
sut_path: /var/home/sasha/para/areas/dev/gh/charly/wild
commit: 4e26885ac3549052cc38394ff3695fa280a403df
updated: 2026-11-27
external_references:
  - path: /var/home/sasha/para/areas/dev/gh/charly/reports/hegel-eval-2026-11-16/README.md
    why: Suite-level Hegel evaluation (verdict §1-5, risks §6, alternatives §7) this repo-level synthesis applies to wild.
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/evaluation/antithesis-fit.md
    why: Suite-level lens rows 20-22 (wild CHEAP-PBT / NEEDS-PBT classification) and generator-cost findings.
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/evaluation/implementability.md
    why: Finding I2 — wild/subtype-holds-preorder depends on the private validator.
  - path: https://github.com/antithesishq/antithesis-skills
    why: antithesis-research skill (version 2026-11-12 6ba10e2).
  - path: https://hegel.dev/
    why: Engine under evaluation; crate `hegeltest` 0.52.7.
---

# Evaluation synthesis — wild

Scoped run (targeted property research): the suite-level scratchbook
(classified wild at commit c22c150) was treated as prior input; this run
re-verified every wild citation against 4e26885, added the CLI
exit/envelope property, and settled the tombstone question into a concrete
recommendation. Method note: this is one analyst, not the skill's full
ensemble; a full per-repo scratchbook (sut ensemble, three evaluation
lenses) would be the next step if the property set grows beyond these four.

## Verdict

**Use Hegel in this repo — as a `tests/`-only, exactly-pinned dev-dependency,
after the tombstone decision lands. This ticket adds no code; the
implementation sequence below is for bd wild-dr2.**

1. **Tombstone first (blocks everything red).** `accretes-is-transitive` is
   predicted red solely because of the narrowed-tombstone removal acceptance
   (`src/v1.rs:898`). Recommendation: make removal require canonical type
   equality between the tombstone and the removed input — this is what
   `docs/wild-formats-v1.md` already says ("tombstones ... must retain their
   last accepted meaning and type"), it is simpler than any subtype check,
   and it restores transitivity. The prototype's widened-tombstone direction
   (`prototype/wild_sim.py:77-82`, `sub(old.ty, tomb.ty)`) also restores the
   law but contradicts the document's wording; adopt it only together with a
   doc change. Do not keep the narrowed acceptance. Until the owner decides,
   write the property as a red test with the documented witness so the
   divergence is pinned, not discovered.
2. **Dependency shape.** `hegeltest = "=0.52.7"`, feature `static-engine`,
   dev-dependency only, never in shipped runtime paths (suite verdict §1).
   Rationale specific to wild: the default engine's nested-cargo build
   breaks vendored/offline builds and wild ships a published crate
   (`wild-vibes` 0.2.1); the suite-level risk register additionally flags
   the nested build vs. wild's Landlock roots.
3. **Test layout.** One file, `tests/hegel_properties.rs`:
   - `#[hegel::test]` for `subtype-is-preorder` (three sub-tests: never-self-
     breaks; Holds transitivity; Breaks symmetry) and
     `canonical-is-normal-form` (roundtrip/idempotence; permutation;
     digest stability) — pure, cheap, run in every CI invocation.
   - `#[hegel::state_machine]` for `cli-exit-envelope-contract`, spawning
     `CARGO_BIN_EXE_wild`, ≤ 12 steps, asserting envelope-canonicality,
     (exit, decision) pairs, and write scope.
   - `accretes-is-transitive` lands as red (step 1) or green after the fix;
     pair it with the prototype: `prototype/wild_cat_sim.py::laws()` stays
     the independent exhaustive oracle on its small-scope lattice, and the
     generator's seed contracts are cross-checked to map into it
     (differential: prototype accretes ⟹ Rust does not report Breaks on the
     mapped fragment).
4. **Hygiene.** Add `.hegel/` to `.gitignore` (Phase 0 item, not done yet —
   verified absent); accept the `ci` profile's DB-off derandomized behavior;
   record cold/warm build delta when the file lands.
5. **Seam decision for the owner.** `validate_type` is private
   (`src/v1.rs:287`). Interim generator works through `validate_contract`
   wrapping, but a `pub` seam (suite finding I2) removes a silent-coverage
   hole; fold it into wild-dr2 rather than widening the API piecemeal.

## Predicted portfolio

| Property | Predicted | Blocks CI adoption? |
|---|---|---|
| accretes-is-transitive | **RED** (tombstone witness) | Yes — triage fix-first; the fix is small and doc-aligned |
| subtype-is-preorder | GREEN (reflexivity, Holds-transitivity); Breaks symmetry lower confidence | No |
| canonical-is-normal-form | GREEN | No |
| cli-exit-envelope-contract | GREEN (rounding boundary unpinned) | No |

Per the suite-level rule, at least one real defect should be in the judged
set: here it is the tombstone/transitivity red, which is a genuine spec/code
divergence — Hegel's marginal value in wild is exactly this kind of
composed-sequence defect plus the minimal shrinking of the recursive type
space.

## Findings register

- **Confirmed (code, this commit):** tombstone direction asymmetry
  (`src/v1.rs:898` vs `:966` vs `:919`); `validate_type` private; no
  Antithesis/Hegel instrumentation anywhere; `.hegel/` untracked; canonical
  examples pinned only as three fixed tests.
- **Refined from suite level:** all `src/v1.rs` citations from c22c150-era
  notes shifted (e.g. removal check was `:829`, now `:898`; reactivation
  `:880-905`, now `:927-969`); the transitivity counterexample survives the
  shift unchanged.
- **Concurrent work observed:** bd wild-lof (uncommitted while this
  scratchbook was written) wraps every CLI stdout print in a genesis shell
  (`src/genesis.rs:26-39`), shifting `src/main.rs` lines by ~9. The CLI
  property is written to hold under either stdout shape; see
  `properties/cli-exit-envelope-contract.md` investigation log.
- **New territory:** `cli-exit-envelope-contract` fills the suite-level
  catalog's recorded CLI gap for wild.
- **Not done here (deliberate):** no Hegel file was written, no production
  code changed, no dependency added — bd wild-dr2 owns implementation.

## Open Questions

- Tombstone intent: narrowed removal — bug or feature? `(needs human input)` — recommendation above; owner call, tracked in
  `properties/accretes-is-transitive.md`.
- `validate_type` public seam in wild-dr2? `(needs human input)` — interim workaround documented; API-widening is an owner call.
- Breaks-symmetry confidence: resolve empirically the first time the Hegel
  file runs; restate or split the sub-property if red.
