# Design: wild-cdp.3 — rung 2 contract-bundle convention + ddl shadow verdict path

Date: 2026-10-14 · Ticket: wild-cdp.3 (P2, DESIGN lane) · Change:
`openspec/changes/add-wild-contract-bundle-convention/` (proposal.md,
design.md, tasks.md, deltas for `wild-registry` + `wild-adopt`)

## Ruling compliance (D1–D7, all followed as stated)

- **D1 bundle convention** — as stated: bundle = directory (tar+gzip when
  shipped, plain dir for local/dev) containing exactly `contract.json`
  (canonical local-1 extraction output of the release tree) and
  `manifest.toml` `{tool, version, commit, profile = "rust-cargo-local-1",
  contract_sha256, extractor_version, extracted_at}`. Manifest is the
  digest-bound trust-chain head; anything absent from it is unverifiable by
  construction. Asset name pinned:
  `<tool>-<version>-contract-bundle.tar.gz`.
- **D2 stamping + refusal law** — release CI extracts from the exact tree it
  builds (same checkout as the published artifact), stamps `contract_sha256`,
  attaches the bundle. Consumer refusal laws named in the delta:
  `bundle-digest-mismatch` (recomputed sha256 ≠ manifest) and
  `bundle-commit-mismatch` (manifest commit ≠ target release commit); named
  diagnostics, never silent acceptance.
- **D3 base-contract caching** — cache at install/upgrade commit time under
  the ddl state dir `contracts/<tool>/<version>/`, contract digest recorded
  in the lock entry (extends `wild-registry.lock_pins_hashes`, which already
  pins contract hash per contracted entry). Missing/corrupt base → Unknown
  verdict with named diagnostic `missing-base-contract`; never fabricated,
  never silently skipped.
- **D4 shadow verdict path** — `ddl upgrade` fetches + verifies the candidate
  bundle, loads the cached base, runs `wild check`
  candidate-vs-installed-base, renders compatible / incompatible / unknown +
  named reasons beside the existing semver/age decision. Exit codes and
  gating unchanged (advisory only). Integration point verified in the ddl
  source: `dulce_de_leche::installer::upgrade_tool` (installer.rs:2053) /
  `upgrade_all_tools` (installer.rs:2251), observed at `src/main.rs::cmd_upgrade`
  (main.rs:964). No ddl code changed in this slice.
- **D5 pilot ordering** — testaruda end-to-end first (13-version corpus,
  `experiments/wild_adopt_audit.py` cross-checks shadow verdicts), then
  fleet-wide via owner-named bd tickets. No other repo edited in this slice.
- **D6 spec home** — deltas in the change; deployed-spec homes: `wild-registry`
  (artifact class: bundle shape, stamping, refusal law, base caching) and
  `wild-adopt` (shadow-verdict consumption side; consistent with the existing
  `shadow_never_blocks` and `observe_is_read_only` constraints). Every delta
  states abstention honestly: bundle presence does not imply verdict
  compatibility; Unknown stays a first-class rendered verdict.
- **D7 open questions** — surfaced below with recommended defaults; none
  blocking.

## Measured evidence (cited, not optimistic)

Both rung-1 audit runs (`results/adopt-audit-cdp4-1841.txt` pre-wild-158 and
`results/adopt-audit-158-1.txt` post-wild-158) replayed all 12 consecutive
testaruda release pairs:

| Metric | cdp4-1841 | 158-1 |
| --- | --- | --- |
| pairs audited | 12 | 12 |
| consistent / disagreement / errored | 0 / 0 / 0 | 0 / 0 / 0 |
| abstained (unknown, refuse/Unknown, exit 1) | 12 (100.0%) | 12 (100.0%) |
| determinism (byte identity) | pass | pass |

Post-wild-158 residual gap ordering (measured, per the rung-1 addendum 2):
(1) method calls on non-bounded receivers (locals, literals, std objects —
wild-8j4), (2) std/external-crate references outside the supplied bundle
(wild-90d), (3) trait impls (named gaps), (4) non-scalar signature fns.
Diagnostic volume grew honestly with disclosure (0.5.5: 81 → 414
incomplete-demand; blanket impl-block `unsupported-construct` gaps 0/12
pairs). Design consequence encoded in the deltas: with today's profile,
Unknown is the *expected* verdict for real releases — the shadow path
measures real gap rates before anything gates (rung 3), exactly the
shadow-first ordering the research artifact prescribes.

## Meters (actual outputs this run)

- `openspec validate --all --strict` → **11 passed, 0 failed (11 items)**
  (10 baseline + the open change; brief expected 11 ✓). Change itself:
  "Change 'add-wild-contract-bundle-convention' is valid".
- `spk lint openspec` → **ok: true, issues: 0, files: 10** (38 skip-warnings,
  all pre-existing "no frontmatter — not a spec file" skips).
- `ah check --changes add-wild-contract-bundle-convention` → **8 structural
  `no-toml` findings** (5 wild-registry + 3 wild-adopt scenarios), the
  expected pre-archive steady state per the brief — contracts bind at
  archive; no TOMLs fabricated for a design-only change.
- `JUST_TEMPDIR=/tmp just ci` → **exit 0** (python 21 ingested, rust gate
  warnings pre-existing, calibration gate ✓).

## Follow-up tickets filed (bd, owner slots named)

- **wild-xc4** (P2) — PILOT: attach contract bundle to testaruda releases
  (charly-vibes/testaruda).
- **wild-xgd** (P2) — ddl consumer side: bundle verify + base-contract cache
  + shadow rendering in upgrade (dulce-de-leche).
- Fleet release-CI tickets (P3, each blocked-by wild-xc4): **wild-5n8** wai
  (charly-vibes/wai), **wild-0tk** dont (charly-vibes/dont), **wild-39w** ah
  (charly-vibes/espectacular), **wild-wdr** pretender
  (charly-vibes/pretender), **wild-u54** vampiro (charly-vibes/vampiro),
  **wild-d1p** incitaciones (charly-vibes/incitaciones), **wild-l04** turu
  (charly-vibes/whisper), **wild-5aj** specodelic (charly-vibes/specodelic),
  **wild-0yt** funkalization (charly-vibes/funkalization), **wild-twd** ddl
  bundle attach (dulce-de-leche), **wild-zjv** wild bundle attach
  (charly-vibes/wild). openspec and bd are out of bundle scope (no
  structural extraction path; authored laws only, gate last).

## Open questions for the user (D7 — recommended defaults, not blocking)

1. **Bundle asset format alternatives** — default: tar+gzip asset named
   `<tool>-<version>-contract-bundle.tar.gz`; plain directory stays the
   local/dev shape. Alternative: OCI artifact / GH pages JSON. Recommend
   tar+gzip (no new infra; GitHub release assets already carry binaries).
2. **Cache location/bundling with existing ddl state** — default:
   `contracts/<tool>/<version>/` under the ddl state dir, digest in the lock
   entry. Alternative: bundle inside the existing dot-ddl cache dir with an
   index. Recommend the flat `contracts/` tree (digest-verified per use;
   trivially cleanable per version).
3. **Should shadow verdicts later gate (rung 3)?** — default: not until the
   pilot measures real gap rates; gate only after Unknown rate for the
   fleet's own updates is measured and the honest abstention causes are
   triaged (wild-8j4 type inference, wild-90d std awareness). Recommend
   keeping rung-3 as its own ticket with pilot data as its input.

## Blockers

None. Design slice complete; not pushed, not closed (orchestrator owns ship).
