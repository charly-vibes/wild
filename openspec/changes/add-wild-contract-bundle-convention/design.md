# Design: add-wild-contract-bundle-convention

Context: the rung-1 audits give measured coverage claims. Both audit runs
replayed the 12 consecutive testaruda release pairs
(`results/adopt-audit-cdp4-1841.txt`, pre-wild-158, and
`results/adopt-audit-158-1.txt`, post-wild-158): 12/12 abstained
(verdict unknown, refuse/Unknown, exit 1), 0 consistent, 0 disagreement,
0 errored, determinism (repeated extraction byte identity) pass in both runs.
Post-wild-158 residual gap ordering (measured): non-bounded-receiver method
calls (wild-8j4), std/external references outside the bundle (wild-90d),
trait impls, non-scalar signature fns. The lead pre-approved rulings D1–D7;
this design records how each ruling lands in the spec deltas.

## Decisions

### D1 — bundle convention, exactly two files

A contract bundle is a directory containing exactly:

- `contract.json` — canonical local-1 extraction output (`wild extract`) of
  the release tree.
- `manifest.toml` — `{tool, version, commit, profile = "rust-cargo-local-1",
  contract_sha256, extractor_version, extracted_at}` where `commit` is the
  exact git tree the artifact was built from and `contract_sha256` =
  sha256(canonical contract.json bytes).

Shipped shape: tar+gzip of that directory as a release asset
(`<tool>-<version>-contract-bundle.tar.gz`); a plain directory is the
local/dev shape. The manifest is the digest-bound trust-chain head: anything
absent from the manifest is unverifiable by construction. This keeps the
bundle within the existing digest-binding invariants of wild-registry
(`sidecar_binds_artifact_digest`, `lock_pins_hashes`) — the manifest is the
pre-registry sidecar; nothing new is invented where a v1 format already
answers.

### D2 — release-CI stamping and the consumer refusal law

The tool's release CI runs `wild extract` on the exact checkout that produced
the published binary (same tree, same job), stamps `contract_sha256` and
`commit` into `manifest.toml`, packs, and attaches. Consumer refusal law
(wild-registry delta, wildcard-bundle scenario pair):

- recomputed sha256(contract.json) ≠ `manifest.contract_sha256` → refuse with
  a named diagnostic (`bundle-digest-mismatch`);
- `manifest.commit` ≠ the commit of the release being upgraded to → refuse
  (`bundle-commit-mismatch`).

Never silent acceptance; the refusal names which check failed.

### D3 — base-contract caching

At install/upgrade commit time, ddl caches the base bundle under the ddl
state dir as `contracts/<tool>/<version>/` and records the contract digest in
the ddl lock entry (extending `lock_pins_hashes`, which already pins contract
hash per contracted entry). Missing or corrupt cached base → `wild check`
cannot run → Unknown verdict with the named diagnostic
`missing-base-contract`. Never fabricated, never silently skipped — this
matches wild-tiers' `evidence_confidence_conservative` and the adopt layer's
observed rule that missing evidence stays unknown.

### D4 — shadow verdict path, advisory rendering only

`ddl upgrade` fetches the candidate bundle, verifies it per D2, loads the
cached base bundle per D3, runs `wild check` candidate-vs-installed-base, and
renders the wild verdict (compatible / incompatible / unknown + named
reasons) as an extra column beside the existing semver/age decision in the
same output table. Integration point: `dulce_de_leche::installer::upgrade_tool`
/ `upgrade_all_tools` (observed at `src/main.rs::cmd_upgrade`). Exit codes and
gating behavior are unchanged in rung 2 — the verdict gates nothing; the wild
verdict rows in the table are advisory. Unknown is rendered as Unknown with
its reasons, exactly like wild check's own output discipline.

### D5 — pilot ordering

Pilot = testaruda end-to-end first: release-CI bundle attach on
charly-vibes/testaruda, then `experiments/wild_adopt_audit.py` cross-checks
the shadow verdicts against the 13-version corpus verdicts already measured
in the rung-1 audit artifacts. Then fleet-wide: one follow-up ticket per
fleet tool needing release-CI edits, owner slot named per repo (filed in
this slice; no other repo edited here). Tools with no structural extraction
path (openspec, bd) are out of bundle scope — they stay authored-laws-only
and gate last.

### D6 — spec home

Deltas live in this change; deployed-spec homes chosen per openspec
conventions:

- `wild-registry` — the artifact class (bundle shape, manifest, stamping,
  refusal law, base-contract caching). Fits because the bundle is the
  digest-bound artifact record the registry/lock layer already pins.
- `wild-adopt` — the shadow-verdict consumption side (rendering beside the
  release decision, gates nothing). Fits because `shadow_never_blocks` and
  `observe_is_read_only` already live there.

Expected abstention behavior is stated honestly in the deltas: bundle
presence does not imply verdict compatibility; with today's measured gap
profile (non-bounded receivers, std-awareness, trait impls, non-scalar
signatures) Unknown is the expected outcome for real releases and stays a
first-class rendered verdict.

### D7 — open questions (surfaced, not blocking)

Recorded in the design doc's Open questions section with recommended
defaults; none block this change.

## Alternatives considered

- *Bundle inside the release binary metadata (embedded)* — rejected: keeps
  the trust chain opaque to offline verification and couples extract version
  to binary format; a sidecar asset stays independently verifiable.
- *Store extracted contracts in the wild registry immediately* — rejected for
  rung 2: registry publication is rung-3/4 machinery; the bundle convention
  must work without registry adoption (matches wild-adopt
  `history_reconstructed` / no-upstream-adoption stance).
- *Gate upgrades on the shadow verdict now* — rejected: rung 3 scope per the
  brief; the rung-1 measurements show a 100% abstention rate today, so
  gating now would block every upgrade on extractor blindness — the exact
  failure the shadow-first ordering exists to avoid.
