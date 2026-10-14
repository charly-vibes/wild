# Change: Add the contract-bundle release convention and the ddl shadow verdict path

## Why

Rung 2 of the adoption ladder needs published contract evidence before anything
can gate on it. The rung-1 audits measured the honest ceiling of the current
extractor over real release history: both audit runs
(`results/adopt-audit-cdp4-1841.txt` and the post-wild-158 re-run
`results/adopt-audit-158-1.txt`) replayed all 12 consecutive testaruda release
pairs (0.1.0→0.5.5) and observed **12/12 abstained** (verdict unknown,
refuse/Unknown, exit 1) with determinism pass in both runs. The post-wild-158
gap composition is measured and ordered: (1) method calls on non-bounded
receivers (locals, literals, std objects — wild-8j4), (2) std/external-crate
references outside the supplied bundle (wild-90d), (3) trait impls (named
gaps), (4) non-scalar signature fns (unchanged). Diagnostic volume grew
honestly with disclosure (0.5.5: 81 → 414 incomplete-demand; blanket
unsupported-construct impl gaps 0/12 pairs). The convention below therefore
states abstention behavior from measured data, not optimism: Unknown stays a
first-class outcome and bundle presence never implies verdict compatibility.

Today nothing carries the contract from the release tree to the consumer:
`ddl upgrade` decides on semver bump class and release age alone, and
`wild check` is only runnable when the operator hand-supplies both bundles.
This change specifies the artifact convention that binds a release's contract
to the exact bytes it was built from (digest-bound end to end), the
base-contract cache that makes the installed side available at check time, and
the shadow rendering of the wild verdict beside the existing release decision —
gating nothing.

## What Changes

- **Contract bundle convention (D1)**: a contract bundle is a directory
  shipped as a release asset (tar+gzip default; a plain directory is the
  local/dev shape) containing exactly `contract.json` (canonical local-1
  extraction output of the release tree, `wild extract`) and `manifest.toml`
  recording `tool`, `version`, `commit` (the exact git tree the artifact was
  built from), `profile = "rust-cargo-local-1"`, `contract_sha256`
  (sha256 of the canonical `contract.json` bytes), `extractor_version`, and
  `extracted_at`. The manifest is the digest-bound trust-chain head; anything
  absent from the manifest is unverifiable by construction.
- **Release-CI stamping + consumer refusal law (D2)**: the tool's release CI
  extracts from the exact tree it builds (same checkout as the published
  artifact), stamps `contract_sha256`, and attaches the bundle to the release.
  The consumer (ddl) refuses a bundle whose recomputed
  sha256(contract.json) ≠ `manifest.contract_sha256`, or whose `commit` does
  not match the release being upgraded to — named diagnostic, never silent
  acceptance.
- **Base-contract caching (D3)**: at install/upgrade commit time ddl caches
  the base bundle under the ddl state dir (`contracts/<tool>/<version>/`) and
  records the contract digest in the ddl lock entry. A missing or corrupt
  cached base is Unknown with the named diagnostic `missing-base-contract` —
  never fabricated, never silently skipped.
- **Shadow verdict path (D4)**: `ddl upgrade` fetches the candidate bundle,
  runs `wild check` candidate-vs-installed-base, and renders the wild verdict
  (compatible / incompatible / unknown + named reasons) beside the existing
  semver/age decision in the same output table. Exit codes and gating behavior
  are unchanged — the verdict gates nothing (advisory rendering only).
  Integration point: `dulce_de_leche::installer::upgrade_tool` /
  `upgrade_all_tools` (observed at `src/main.rs::cmd_upgrade`).
- **Pilot ordering (D5)**: testaruda end-to-end first (its 13-version corpus
  and the existing audit harness `experiments/wild_adopt_audit.py` cross-check
  shadow verdicts), then fleet-wide per-repo `release.yml` edits (owner-named
  follow-up tickets, filed in this slice; no other repo is edited here).

No breaking change: the bundle adds a release asset; `wild check`'s input
contract (v1 envelopes) is unchanged; ddl's decision semantics are unchanged.

## Impact

- Affected specs: `wild-registry` (ADDED requirements: contract bundle release
  artifact; base-contract caching), `wild-adopt` (ADDED requirement: shadow
  verdict rendering beside the release decision)
- Affected code (future rung-2 implementation lane, not this slice): each
  fleet tool's release CI (pilot: testaruda), ddl
  (`src/installer.rs` upgrade path, cache under the ddl state dir)
- Measured evidence: `results/adopt-audit-cdp4-1841.txt`,
  `results/adopt-audit-158-1.txt` (12/12 pairs abstained in both;
  determinism pass in both)
