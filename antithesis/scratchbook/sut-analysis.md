---
sut_path: /var/home/sasha/para/areas/dev/gh/charly/wild
commit: 4e26885ac3549052cc38394ff3695fa280a403df
updated: 2026-11-27
external_references:
  - path: /var/home/sasha/para/areas/dev/gh/charly/reports/hegel-eval-2026-11-16/README.md
    why: Suite-level Hegel evaluation (verdict, rollout phases, risk register) this repo-level plan builds on.
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/property-catalog.md
    why: Suite-level catalog, section "wild (c22c150)" — screening-depth baselines for the three relation properties.
  - path: /var/home/sasha/para/areas/dev/gh/charly/antithesis/scratchbook/properties/wild.md
    why: Prior per-property evidence at commit c22c150; all line citations re-verified against 4e26885 here.
  - path: https://github.com/antithesishq/antithesis-skills
    why: antithesis-research skill (version 2026-11-12 6ba10e2) whose method and artifact formats this run follows.
  - path: https://hegel.dev/
    why: Engine under evaluation; crate `hegeltest` 0.52.7.
---

# SUT analysis — wild (scoped: v1 relations + check/extract pipeline)

## What wild is

`wild` is a scoped dependency-contract checker for Rust/Cargo updates. Package
`wild-vibes` 0.2.1 (edition 2021, no declared MSRV), binary `wild`, library
`wild` (`Cargo.toml:42-63`). It extracts crate inventories (rust-cargo-local-1),
validates v1 contract documents, and evaluates consumer update plans. Every
command emits a canonical-JSON v1 `envelope` on stdout and maps outcomes to
exits: accept 0, refuse 1, error 2 (`src/main.rs:3-17`).

## Components in scope

| Component | Role | Key surface |
|---|---|---|
| `src/v1.rs` | Strict v1 reader, semantic contract validation, conservative subtype table, accretion rules | `read_document` (:79), `validate_contract` (:98), `subtype` (:546), `accretes` (:804), private `validate_type` (:287) |
| `src/formats.rs` | Strict JSON parse, canonical writer, digest | `parse` (:104), `canonical` (:313), `write_canonical` (:319) |
| `src/main.rs` | CLI dispatch, envelope construction, exit mapping | `run_extract` (:114), `run_check` (:200), `run_update` (:330), `run_v1_accretes` (:704), `envelope` (:37) |
| `src/check.rs`, `src/extract.rs` + modules | Check/extract pipeline orchestration | extraction outcomes, check outcomes → envelope |
| `src/harness.rs` | Landlock/no-new-privs law-suite sandbox for candidate artifacts | `landlock_abi_query` (:145); Linux-only (:63) |

Out of scope for this run: `src/obligations.rs`, `src/update.rs`,
`src/delivery.rs`, `src/cargo_host.rs` internals (they feed the pipeline but
carry no cataloged property of their own here).

## The product claim

The v1 compatibility relation `accretes(old, new)` is meant to be the
composability relation of a category of contracts (`docs/wild-formats-v1.md`
§Contract IR; "the category laws apply to jointly composable interfaces").
Transitivity is the load-bearing law: a chain of individually accepted
revisions must remain acceptable end to end. The only exhaustive check today
is the Python prototype `prototype/wild_cat_sim.py` (`laws()`, 76 states /
n³ triples, 0.02 s); the Rust checker has fixed-example tests only
(`tests/v1_checker.rs`, 462 lines, no generated relation laws).

## State and concurrency

- The CLI is stateless: it reads the requested inputs and writes only the
  requested output locations (`src/main.rs:10-17`); no database, no cache
  directory. Adding Hegel introduces the only new on-disk state
  (`.hegel/examples` failing-example database), which must be gitignored.
- No in-process concurrency; the binary is single-threaded. The Landlock
  sandbox in `src/harness.rs` constrains *candidate artifacts during law
  evaluation*, not the test process itself — Hegel tests must not run inside
  it, and conversely Hegel's default nested-cargo engine build must never be
  triggered inside a sandboxed candidate run.

## Provenance note

All `src/v1.rs` and `src/formats.rs` citations are verified against both the
pinned commit 4e26885 and the live tree (both files unmodified). `src/main.rs`
citations reflect the **live tree** as of 2026-11-27: a peer change (bd
wild-lof, uncommitted) was mid-flight while this scratchbook was written and
shifted main.rs line numbers by ~9, routing every envelope print through
`genesis::wrap` (`src/genesis.rs:26-39`). Re-verify main.rs line numbers
before acting on them.

## Failure-prone areas (evidence-verified at this commit)

1. **Tombstone direction asymmetry** — `retained_inputs` accepts a *narrowed*
   tombstone on removal: `subtype(tombstone, old)` (`src/v1.rs:898`), while
   reactivation requires the slot to contain the tombstoned domain:
   `subtype(old_tombstone, slot)` (`src/v1.rs:966`), and retained inputs check
   the opposite direction `subtype(old, new)` (`src/v1.rs:919`). The narrowing
   on removal plus containment on reactivation lets a chain shrink below its
   origin, which breaks `accretes` transitivity (constructed witness in
   `properties/accretes-is-transitive.md`).
2. **Three-valued conservative verdicts** — `subtype` returns `Unknown`
   whenever its rules cannot establish inclusion (`src/v1.rs:543-545`), and
   reflexivity is deliberately partial (an integer type without an interval
   yields `Unknown`). Any law stated over `subtype` must be conditioned on
   `validate_type`-valid, interval-complete types, or stated as
   never-`Breaks` rather than always-`Holds`.
3. **Private validator** — `validate_type` (`src/v1.rs:287`) is not public;
   the only public validity gate is `validate_contract` on a whole document.
   Generators and tests must currently reach validity through whole-contract
   construction (see `evaluation/synthesis.md`, seam note; matches
   implementability finding I2 in the suite-level scratchbook).
4. **Canonical escaping / digest identity** — canonical bytes fix key order,
   control-character escaping, and safe-integer bounds
   (`docs/wild-formats-v1.md` §Encoding); `type_identical`
   (`src/v1.rs` `formats::canonical(a) == formats::canonical(b)`) and digest
   stability inherit any canonicalization defect.
5. **Duplicated exit mapping** — the accept 0 / refuse 1 / error 2 mapping is
   implemented per command (`src/main.rs:156,241,392,511,822-826`), so the
   CLI contract property must cover all five command paths, including the
   `--version` plain-line exception (`src/main.rs:833-840`, beads wild-9sm).

## Assumptions

- The Python prototype is an independent oracle, not a port: its type lattice
  (`int32/int64/decimal/str`, `prototype/wild_sim.py:8-9`) is coarser than the
  v1 table, so differential agreement is checked only on the mapped fragment.
- `docs/wild-formats-v1.md` is authoritative where code and doc disagree
  (relevant to the tombstone wording "must retain their last accepted meaning
  and type").

## Open Questions

- Is the narrowed-tombstone removal acceptance (`src/v1.rs:898`) intentional,
  or should removal require type retention per the format document? See
  `evaluation/synthesis.md` (recommendation: doc-equality). `(needs human input)`
- Should `validate_type` gain a public seam for property tests, or must
  generators construct validity through whole contracts only? See
  `evaluation/synthesis.md`. `(needs human input)`
