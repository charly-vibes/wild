# Report: wild-cdp.3 — rung 2 design (contract-bundle convention + ddl shadow verdict path)

Status: **complete** (design slice; no implementation code, no ddl-repo
changes, no pushes, not bd-closed — orchestrator owns ship).

## Commits (wild repo, not pushed)

- **238ca1a** — `design(wild-cdp.3): rung-2 contract-bundle convention + ddl
  shadow verdict path (openspec change + design doc)` — adds
  `openspec/changes/add-wild-contract-bundle-convention/` (proposal.md,
  design.md, tasks.md, deltas for `wild-registry` + `wild-adopt`) and the
  design doc `.wai/projects/software-updates/designs/2026-10-14-wild-cdp-3-rung-2-design.md`.
- **213b73b** — `chore(wild-cdp.3): orchestrator run artifacts —
  spawn/orient/brief research for rung-2 design` (pre-existing untracked
  pipeline/research artifacts committed with the run).

## Deliverables

1. `openspec/changes/add-wild-contract-bundle-convention/` — proposal,
   design, tasks, and spec deltas specifying all four components:
   bundle convention (D1), release-CI stamping + consumer refusal law (D2),
   base-contract caching (D3), shadow verdict rendering (D4), pilot
   ordering (D5). Spec homes per D6: `wild-registry` (2 ADDED requirements,
   5 scenarios) + `wild-adopt` (1 ADDED requirement, 3 scenarios).
2. Design summary at
   `.wai/projects/software-updates/designs/2026-10-14-wild-cdp-3-rung-2-design.md`
   (decisions vs rulings D1–D7, measured-evidence citations, open questions).
3. Per-tool pilot follow-up tickets in bd (13 filed, owner named per repo).

## Measured evidence cited (both audit files read in full)

- `results/adopt-audit-cdp4-1841.txt` and `results/adopt-audit-158-1.txt`:
  12/12 consecutive testaruda release pairs abstained in **both** runs
  (verdict unknown, refuse/Unknown, exit 1; 0 consistent / 0 disagreement /
  0 errored; unknown rate 100.0%; determinism pass in both).
- Post-wild-158 residual gap ordering (from the rung-1 addendum 2 in the
  dogfooding research doc): non-bounded-receiver method calls (wild-8j4),
  std/external outside the bundle (wild-90d), trait impls, non-scalar
  signature fns; disclosure growth 0.5.5: 81→414 incomplete-demand; blanket
  impl-block unsupported-construct 0/12 pairs. The change states abstention
  honestly: Unknown stays first-class; bundle presence ≠ compatibility.
- ddl integration points verified in source (read-only):
  `installer.rs::upgrade_tool` (2053) / `upgrade_all_tools` (2251), observed
  at `main.rs::cmd_upgrade` (964); fleet inventory taken from
  `dulce-de-leche/src/platform.rs::MANAGED_TOOLS` (14 tools; openspec + bd
  excluded from bundle scope — no structural extraction path).

## Meter outputs (actual)

- `openspec validate --all --strict` → `Totals: 11 passed, 0 failed (11
  items)` (brief expected 11 with the change open ✓); change itself: valid.
- `spk lint openspec` → `ok: true, issues: 0, files: 10` (38 pre-existing
  skip-warnings only).
- `ah check --changes add-wild-contract-bundle-convention` → 8 structural
  `no-toml` findings (5 wild-registry + 3 wild-adopt scenarios) — the
  expected pre-archive steady state per the brief; no TOMLs fabricated for a
  design-only change (contracts bind at archive).
- `JUST_TEMPDIR=/tmp just ci` → exit 0 (21 python results ingested; rust
  adapter "matched no known test item" warnings and vacuous calibration are
  pre-existing baseline noise).
- Pre-commit hooks green on both commits (testaruda-config, ah-check,
  pretender-gate, specodelic-gates).

## Follow-up tickets filed (bd, owner slots named)

- **wild-xc4** (P2) pilot — testaruda release.yml bundle attach
  (charly-vibes/testaruda).
- **wild-xgd** (P2) — ddl consumer side: verify + cache + shadow rendering
  (dulce-de-leche).
- Fleet P3 release-CI tickets, each blocked-by wild-xc4: **wild-5n8** wai,
  **wild-0tk** dont, **wild-39w** ah, **wild-wdr** pretender, **wild-u54**
  vampiro, **wild-d1p** incitaciones, **wild-l04** turu, **wild-5aj**
  specodelic, **wild-0yt** funkalization, **wild-twd** ddl (bundle attach),
  **wild-zjv** wild.

## Design decisions taken vs rulings

All of D1–D7 followed as stated. Interpretation notes: (a) refusal
diagnostics named concretely (`bundle-digest-mismatch`,
`bundle-commit-mismatch`, `missing-base-contract`) since D2/D3 demand named
diagnostics; (b) asset filename pinned as
`<tool>-<version>-contract-bundle.tar.gz` (D1 leaves format open — flagged
as open question OQ1); (c) caching spec placed in `wild-registry` because
`lock_pins_hashes` already pins contract hash per contracted lock entry, so
the cache extends an existing invariant rather than inventing a new home;
(d) shadow rendering spec placed in `wild-adopt` alongside the existing
`shadow_never_blocks`/`observe_is_read_only` constraints it must not
contradict.

## Open questions for the user (D7, recommended defaults in the design doc)

1. Bundle asset format alternatives (default: tar+gzip release asset).
2. Cache location/bundling with existing ddl state (default:
   `contracts/<tool>/<version>/` under the state dir, digest in lock entry).
3. Whether shadow verdicts should later gate — rung 3 scope; recommend
   gating only after the pilot measures real Unknown rates and the
   abstention causes are triaged (wild-8j4, wild-90d).

## Honest blockers

None. Remaining limits stated plainly: the design does not (and cannot yet)
claim any Compatible verdicts for real releases — measured Unknown rate is
100% on the only audited corpus, and that is exactly what the shadow path
must render honestly before anything gates.
