---
sut_path: /var/home/sasha/para/areas/dev/gh/charly/wild
commit: 4e26885ac3549052cc38394ff3695fa280a403df
updated: 2026-11-27
external_references:
  - path: /var/home/sasha/para/areas/dev/gh/charly/reports/hegel-eval-2026-11-16/README.md
    why: Suite-level Hegel evaluation this run extends.
  - path: https://github.com/antithesishq/antithesis-skills
    why: antithesis-research skill (version 2026-11-12 6ba10e2).
---

# Existing assertions — wild

Scan performed over `src/`, `tests/`, and `prototype/` for Antithesis SDK
assertion calls (`assert_always!`, `assert_sometimes!`, `assert_reachable!`,
`assert_unreachable!`, and their non-macro equivalents) and for any
`antithesis` SDK import.

**No Antithesis SDK assertions were found.** The codebase has no existing
instrumentation of any kind:

- No Antithesis SDK dependency in `Cargo.toml`.
- No Hegel dependency either; there is no `hegeltest` entry in `Cargo.lock`
  and no `.hegel/` entry in `.gitignore`.
- The existing test surface is fixed-example Rust integration tests
  (`tests/v1_checker.rs`, 462 lines) and pytest integration suites
  (`tests/test_*.py`) plus the exhaustive small-scope Python law check in
  `prototype/wild_cat_sim.py`. None of these embed property-tooling
  assertions in shipped code.

Consequence: every property in `property-catalog.md` plans its checks from
scratch (workload-side Hegel assertions in `tests/`); no evidence file needs
to distinguish existing vs. missing SUT-side instrumentation, and nothing
proposed duplicates an assertion that is already present.
