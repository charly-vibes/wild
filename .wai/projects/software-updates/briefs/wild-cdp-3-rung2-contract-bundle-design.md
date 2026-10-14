# Brief: wild-cdp.3 — rung 2 design: contract-bundle convention + ddl shadow verdict path

## Why
Delegation rationale: DESIGN lane — design before code; the deliverable is an
openspec change proposal + a design document, NOT implementation. The rung-1
audit evidence now exists in two runs (`results/adopt-audit-cdp4-1841.txt` and
`results/adopt-audit-158-1.txt`, post-wild-158), so the convention's coverage
claims and gap expectations rest on measured corpus data, not optimism. The
subagent writes the design; the lead verifies, ships, and routes remaining
rulings to the user.

## Ticket
- **ID**: wild-cdp.3 (P2, claimed in this run; epic wild-cdp rung 2; bd metadata
  pins the change name: `openspec/changes/add-wild-contract-bundle-convention`)
- **Desired outcome**:
  1. `openspec/changes/add-wild-contract-bundle-convention/` — proposal.md,
     tasks.md, and design.md in the wild repo specifying all four components
     below with spec deltas that `spk lint` + `openspec validate --strict` accept.
  2. Design summary committed at
     `.wai/projects/software-updates/designs/2026-10-14-wild-cdp-3-rung-2-design.md`
     (decisions, measured-evidence citations, open questions for the user).
  3. Per-tool pilot follow-up tickets filed in bd (one per fleet tool needing
     release-CI edits; owner named per repo).

## Design rulings (PRE-APPROVED by lead — design as stated; open questions surfaced, not invented)

- **D1 — bundle convention.** A contract bundle is a directory shipped as a
  release asset (tar+gzip default; a plain directory is the local/dev shape)
  containing exactly:
  - `contract.json` — canonical local-1 extraction output (`wild extract`) of
    the release tree;
  - `manifest.toml` — `{tool, version, commit, profile = "rust-cargo-local-1",
    contract_sha256, extractor_version, extracted_at}` where `commit` is the
    exact git tree the artifact was built from and `contract_sha256` =
    sha256(canonical contract.json bytes).
  The manifest is the digest-bound trust chain head; anything absent from the
  manifest is unverifiable by construction.

- **D2 — release-CI stamping.** The tool's release CI extracts from the exact
  tree it builds (same checkout as the published artifact), stamps
  `contract_sha256`, and attaches the bundle to the release. Refusal law for the
  consumer side: ddl refuses a bundle whose recomputed sha256(contract.json) !=
  `manifest.contract_sha256`, or whose `commit` doesn't match the release being
  upgraded to — named diagnostic, never silent acceptance.

- **D3 — base-contract caching.** At install/upgrade commit time, ddl caches the
  base bundle under the ddl state dir (`contracts/<tool>/<version>/`); the
  contract digest is recorded in the ddl lock entry. Missing or corrupt cached
  base = wild check runs → Unknown verdict with named diagnostic
  (`missing-base-contract`); never fabricated, never silently skipped.

- **D4 — shadow verdict path.** `ddl upgrade` fetches the candidate bundle,
  runs `wild check` candidate-vs-installed-base, and renders the wild verdict
  (compatible / incompatible / unknown + named reasons) beside the existing
  semver/age decision in the same output table. Exit codes and gating behavior
  unchanged — the verdict gates nothing in rung 2 (advisory rendering only).
  Integration point: `dulce_de_leche::installer::upgrade_tool` /
  `upgrade_all_tools` (observed at `src/main.rs::cmd_upgrade`); the design names
  the exact insertion shape but changes no ddl code in this slice.

- **D5 — pilot ordering.** Pilot = testaruda end-to-end first (13-version
  corpus, existing audit harness `experiments/wild_adopt_audit.py` cross-checks
  the shadow verdicts), then fleet-wide. Per-repo `release.yml` edits need repo
  owners → file one bd follow-up ticket per tool with the owner slot named;
  do NOT edit other repos in this slice.

- **D6 — spec home.** The deltas live in the change above; the subagent picks
  the deployed-spec home per openspec conventions (candidate: `wild-registry`
  for the artifact class; `wild-adopt`/`wild-deploy` for the shadow-verdict
  consumption side) — every [[link]] must resolve corpus-wide and `spk lint`
  must pass. Measured evidence cited in the change: post-wild-158 residual gap
  ordering (type-inference receivers wild-8j4, std/external awareness wild-90d,
  trait impls, non-scalar signatures) — the convention MUST state expected
  abstention behavior honestly (bundle presence does not imply verdict
  compatibility; Unknown stays a first-class outcome).

- **D7 — open questions for the user** (surface in the design doc's
  "Open questions" section with a recommended default each; do not block on
  them): bundle asset format alternatives; cache location/bundling with
  existing ddl state; whether shadow verdicts should later gate (rung 3 scope).

## Exact commands
- `openspec validate --all --strict` (with change open: 11 expected)
- `spk lint openspec` (0 findings)
- `ah check` (overlay mode on the new change; structural no-toml findings for
  new scenarios are the expected pre-archive steady state — contracts bind at
  archive, do not fabricate TOMLs for a design-only change)
- `JUST_TEMPDIR=/tmp just ci` exit 0

## Commit protocol
- Commit the change + design doc in the wild repo (atomic, one or two commits);
  do NOT push and do NOT `bd close` — the orchestrator owns ship.

## Out of scope
Any ddl-repo code change, any release.yml edit, rung-3 gating semantics,
implementation of the shadow path, testaruda repo changes.
