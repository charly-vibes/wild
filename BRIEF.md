# Project status brief

## Purpose / current state

none

## Focus

none

## In flight

- wild-bsp — release: add release workflow and publish wild binaries on GitHub Releases (status: open; priority: 1; age: 2d; blocked by: wild-g7o)
- wild-dr2 — Implement Hegel property tests (status: open; priority: 1; age: 2d; blocked by: wild-wz9)
- wild-fq1 — docs: apply README front-door standard v0.4 (§5.1) (status: open; priority: 1; age: 2d)
- wild-g7o — implement update-wild-openness-default: open-by-default with justified closure (v1-in-place, pre-1.0 window) (status: open; priority: 1; age: 2d)
- wild-wz9 — Research: Hegel property-based testing plan (antithesis-research) (status: open; priority: 1; age: 2d)
- wild-7p9 — stale global tests-pass oracle: ~/.wai/resources/oracles/tests-pass.sh hardcodes specodelic-gre-wt worktree (status: open; priority: 2; age: 7d)
- wild-ee4 — tmpfs near-full: /tmp at 18G/25.4G quota after compile-oracle run - Errno 122 risk for next heavy cargo/pytest run (status: open; priority: 2; age: 7d)
- wild-xgd — ddl: bundle verify + base-contract cache + shadow verdict rendering in upgrade (status: in_progress; priority: 2; age: 35d)
- wild-zh6 — implement add-declared-bump-derivation: corpus-delta bump classifier, upward-only override, audit record (status: open; priority: 2; age: 2d)
- wild-0tk — Attach contract bundle to dont releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-0yt — Attach contract bundle to funkalization releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-39w — Attach contract bundle to ah releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-5aj — Attach contract bundle to specodelic releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-5n8 — Attach contract bundle to wai releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-8j4 — Method-call demand on non-bounded receivers needs real type inference (status: open; priority: 3; age: 35d)
- wild-90d — rust-cargo-local-1 std/external-crate awareness for demand resolution (status: open; priority: 3; age: 35d)
- wild-d1p — Attach contract bundle to incitaciones releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-l04 — Attach contract bundle to turu releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-twd — Attach contract bundle to ddl releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-u54 — Attach contract bundle to vampiro releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-wdr — Attach contract bundle to pretender releases (release.yml) (status: open; priority: 3; age: 35d)
- wild-zjv — Attach contract bundle to wild releases (release.yml) (status: open; priority: 3; age: 35d)

## Blocked / waiting

- wild-bsp — release: add release workflow and publish wild binaries on GitHub Releases (status: open; priority: 1; age: 2d; blocked by: wild-g7o)
- wild-dr2 — Implement Hegel property tests (status: open; priority: 1; age: 2d; blocked by: wild-wz9)

## Next / ready

- wild-fq1 — docs: apply README front-door standard v0.4 (§5.1) (status: open; priority: 1; age: 2d)
- wild-g7o — implement update-wild-openness-default: open-by-default with justified closure (v1-in-place, pre-1.0 window) (status: open; priority: 1; age: 2d)
- wild-wz9 — Research: Hegel property-based testing plan (antithesis-research) (status: open; priority: 1; age: 2d)
- wild-7p9 — stale global tests-pass oracle: ~/.wai/resources/oracles/tests-pass.sh hardcodes specodelic-gre-wt worktree (status: open; priority: 2; age: 7d)
- wild-ee4 — tmpfs near-full: /tmp at 18G/25.4G quota after compile-oracle run - Errno 122 risk for next heavy cargo/pytest run (status: open; priority: 2; age: 7d)
(14 more omitted)

## Parked

none

### Needs re-triage

none

## Recent

- c22c150ae509b2c1c6cf4704a5b64b7f09362a43 docs: portfolio task-state hygiene per rule-of-5 review — tick landed gates, annotate wild-xgd core (f728b03), wild-g7o blocks wild-bsp (2026-11-16T15:43:39Z)
- 054ed73f9009f8afcfb288a58e1f1521cbe600fd docs(wild-zh6): amend bump-derivation per rule-of-5 review — requirement-level measurement, RENAMED/aggregation/row-only scenarios (2026-11-16T15:43:38Z)
- d0b24bee955595231245396b93ef94ed0a63e406 docs(wild-zh6): add-declared-bump-derivation proposal (2026-11-16T15:28:12Z)
- 6f1b4615bae895090afda1982b77479ba1b2a7f6 docs: apply issue-review fixes to README/release tickets (2026-11-16T12:03:52Z)
- 3f08fb3d94d4a8800b891ef14a7f2274777d5ee8 docs: apply issue-review fixes to README/release tickets (2026-11-16T11:50:20Z)
(178 more omitted)

## Health + confidence

Health: **amber** — basis: signals — owner: none — reason: orphan_commits: 13 commits in the 14-day window link no tracker id or open work-item path: 1b380f7b2a406e9ad95003d276b9b76e02ea8356 (docs: file README front-door and release tickets); 286aa8617a9b1945510e7cc7f93692aae91cdab6 (beads: file evaluation findings from cotorreo/pinky investigation (oracle, drift, experiments, abstention re-measure)); 2c344a0870ba99a12d0d59393c86e252faede5bb (docs(brief): pretender debt fix brief (wild) — orchestrator artifact); 30179a825c2ddd350366e551ebf60ea51bcf4239 (beads: review fixes — files/base_commit metadata, lane+complexity labels, quantified Must gates on evaluation tickets); 3f08fb3d94d4a8800b891ef14a7f2274777d5ee8 (docs: apply issue-review fixes to README/release tickets); 453c26f1349b5fb9cb0f3693ef7fe57a7644b311 (refactor(quality): cut mutable-binding ratio in macro_demands format scan); 5c1c661e5d562b9294c706e6a3a9244e78432c9a (fix(quality): fix scanner parse error and cut panicking-call debt in harness/obligations); 6f1b4615bae895090afda1982b77479ba1b2a7f6 (docs: apply issue-review fixes to README/release tickets); 768f15677660a41b16942c75def4cb62b41c1acf (test(quality): break lazy test clusters (pretender 0.10 file checks)); 7b1f6c93115dff7bcbbce8d6f390e44a78aba9f4 (beads: file tmpfs-quota + stale-global-oracle findings from eval-batch orchestration); 84630305e2cfd397b89736b40568e20b8f5ee326 (fix(orchestration): tests-pass oracle uses user pytest shim — brew python3 lacks the module); b048b2467a4a14c3172c394a3c6e4f4d424edc25 (fix(specs): re-point 11 deployed scenarios to post-768f156 test names — lazy-cluster refactor consolidated macro tests without updating contracts); b6311bda71e3dc155aee8fb3db4f90bead46cdf2 (refactor(heldout): drop dead pool-wide break_count/ok_count in cmd_report); spec_change_without_bead: openspec changes link no tracker id: `add-conveys-clause` changed 2 days ago, `add-declared-bump-derivation` changed 2 days ago, `add-on-absent-fallible` changed 2 days ago, `add-wild-contract-bundle-convention` changed 2 days ago
- signal: orphan commits — 13 commits in the 14-day window link no tracker id or open work-item path: 1b380f7b2a406e9ad95003d276b9b76e02ea8356 (docs: file README front-door and release tickets); 286aa8617a9b1945510e7cc7f93692aae91cdab6 (beads: file evaluation findings from cotorreo/pinky investigation (oracle, drift, experiments, abstention re-measure)); 2c344a0870ba99a12d0d59393c86e252faede5bb (docs(brief): pretender debt fix brief (wild) — orchestrator artifact); 30179a825c2ddd350366e551ebf60ea51bcf4239 (beads: review fixes — files/base_commit metadata, lane+complexity labels, quantified Must gates on evaluation tickets); 3f08fb3d94d4a8800b891ef14a7f2274777d5ee8 (docs: apply issue-review fixes to README/release tickets); 453c26f1349b5fb9cb0f3693ef7fe57a7644b311 (refactor(quality): cut mutable-binding ratio in macro_demands format scan); 5c1c661e5d562b9294c706e6a3a9244e78432c9a (fix(quality): fix scanner parse error and cut panicking-call debt in harness/obligations); 6f1b4615bae895090afda1982b77479ba1b2a7f6 (docs: apply issue-review fixes to README/release tickets); 768f15677660a41b16942c75def4cb62b41c1acf (test(quality): break lazy test clusters (pretender 0.10 file checks)); 7b1f6c93115dff7bcbbce8d6f390e44a78aba9f4 (beads: file tmpfs-quota + stale-global-oracle findings from eval-batch orchestration); 84630305e2cfd397b89736b40568e20b8f5ee326 (fix(orchestration): tests-pass oracle uses user pytest shim — brew python3 lacks the module); b048b2467a4a14c3172c394a3c6e4f4d424edc25 (fix(specs): re-point 11 deployed scenarios to post-768f156 test names — lazy-cluster refactor consolidated macro tests without updating contracts); b6311bda71e3dc155aee8fb3db4f90bead46cdf2 (refactor(heldout): drop dead pool-wide break_count/ok_count in cmd_report)
- signal: spec change without bead — openspec changes link no tracker id: `add-conveys-clause` changed 2 days ago, `add-declared-bump-derivation` changed 2 days ago, `add-on-absent-fallible` changed 2 days ago, `add-wild-contract-bundle-convention` changed 2 days ago

## Sources & freshness

| source | status | observed_at | staleness | detail |
| --- | --- | --- | --- | --- |
| beads | present | 2026-11-16T21:33:17Z | fresh | 7 malformed line(s) skipped in .beads/issues.jsonl |
| git | present | 2026-11-16T15:43:39Z | fresh | none |
| openspec | present | 2026-11-16T15:43:27Z | fresh | none |
| whisper | present | 2026-11-16T15:52:14Z | fresh | none |
| curation | present | 2026-11-18T21:12:09Z | fresh | none |

Curation: updated_at 2026-11-18T21:12:09Z; confirmed_at none.

Freshness: generated_at 2026-11-18T21:12:09Z; per-source observed_at and staleness are listed above.
