---
sut_path: /var/home/sasha/para/areas/dev/gh/charly/wild
commit: 4e26885ac3549052cc38394ff3695fa280a403df
updated: 2026-11-27
external_references:
  - path: /var/home/sasha/para/areas/dev/gh/charly/reports/hegel-eval-2026-11-16/README.md
    why: Suite-level Hegel evaluation this run extends.
  - path: https://github.com/antithesishq/antithesis-skills
    why: antithesis-research skill (version 2026-11-12 6ba10e2).
  - path: https://hegel.dev/
    why: Engine under evaluation; crate `hegeltest` 0.52.7.
---

# Deployment topology — wild

**For the Hegel property plan, no Antithesis container topology is needed.**
All four cataloged properties run in-process or as ordinary subprocesses on
the developer machine / CI runner (`tests/` harness):

- `accretes-is-transitive`, `subtype-is-preorder`, `canonical-is-normal-form`
  — pure in-process calls into the `wild` library; no filesystem or network
  state beyond Hegel's own `.hegel/examples` database (gitignored; disabled
  by the `ci` profile).
- `cli-exit-envelope-contract` — subprocess state machine spawning the binary
  built by the same `cargo test` invocation (`CARGO_BIN_EXE_wild`), writing
  only into a temp working directory.

Two topology-relevant constraints are recorded for the implementer
(bd wild-dr2):

1. **static-engine.** Use `hegeltest = "=0.52.7"` with the `static-engine`
   feature: the default engine build invokes nested cargo and fails
   vendored/offline builds; wild publishes a crate and values hermetic
   builds (suite-level evaluation §2, §6).
2. **Never inside the Landlock sandbox.** wild's own law-suite sandbox
   (`src/harness.rs`) restricts candidate artifacts during law evaluation;
   Hegel test processes and their engine must not run under it, and the
   Hegel engine build must never be triggered inside a sandboxed candidate
   run (the suite-level risk register flags this as the wild-specific
   blocker).

If this scratchbook is later reused for a full Antithesis platform run
(crash/fault injection), the minimal useful topology is a single container
holding the `wild` binary, the strict v1 fixture corpus, and test templates
under `/opt/antithesis/test/v1/`; every additional container would expand
state space without a cataloged property to justify it.
