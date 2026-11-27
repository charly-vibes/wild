# Changelog

Notable user-visible changes to wild. Format: [Keep a Changelog](https://keepachangelog.com/) style, one section per release.

## [Unreleased]

### Added

- `wild bump --base <ref>` subcommand (bd wild-zh6, change
  add-declared-bump-derivation): maintainer-side declared-bump generator —
  derives exactly one bump class from the spec-corpus delta between the
  base release and the candidate tree at the openspec requirement level
  (ADDED-only → minor/accretes; any MODIFIED/REMOVED/RENAMED →
  major/revokes; aggregated multi-change deltas classify once; empty or
  row-only deltas → patch; a missing base corpus yields Unknown with the
  `missing_base_corpus` diagnostic and never a fabricated class). The
  override is upward-only: raising records the reason, lowering is refused
  with `bump_class_lowering_refused` and the proposal stands. `--out`
  writes a local-1 `declared-bump-record`; the adopt audit driver takes
  `--claims` and lists declared-vs-computed agreement/disagreement per
  release, excluding absent claims from counts. Advisory output only —
  every computed outcome exits 0 (shadow never blocks).

- Release contract bundles attached by wild's own release workflow (bd
  wild-zjv): every GitHub release now carries
  `wild-<version>-contract-bundle.tar.gz` — the `wild extract` contract of
  the exact tagged checkout plus a digest-bound `manifest.toml` (tool,
  version, commit, profile, contract_sha256, extractor_version,
  extracted_at). The publish job runs the pinned `wild-vibes` extractor
  before provenance generation, so the bundle digest is bound into
  `provenance.json`; the `scripts/make-contract-bundle.sh` step attaches on
  extract exit 0/1 (honest Unknown gap accounting never blocks the release)
  and fails on exit 2. See the README "Contract bundle" section for the
  verification one-liner.

- `wild feedback <kind>` subcommand (bd wild-8g8): adopt the
  `genesis::feedback` contract additively — kind validation over
  bug/feature/question/chore/aix-gap, stdin or `--from-last-error` body
  derivation, home-path/secret redaction, an environment bundle, and a
  local report file as the network-free filing outcome. Output goes
  through the shared emit() funnel, so stdout stays the genesis shell.

### Changed

- All stdout output (every subcommand, exit 0/1/2) is now a genesis envelope: a
  shell with `ok`, `envelope_version`, `cli_version`, `envelope_kind`, `warnings`,
  `meta`, and `data` — where `data` is the v1 envelope, byte-identical to the
  previous standalone shape (bd wild-lof). Consumers reading the v1 payload
  unwrap `.data`; exit codes, file-output contracts, and `--version`/`-V`
  plain lines are unchanged.

## [0.2.1] - 2026-11-27

### Added

- First GitHub Releases: five binaries (linux/darwin amd64+arm64, windows
  amd64), checksums.txt, provenance.json (bd wild-bsp).
- Contract bundle convention pilot (bd wild-xc4): `wild extract` bundles
  attach to releases; manifest is the digest-bound trust chain.

### Changed

- v1 open-by-default with justified closure (bd wild-g7o): `open` omitted
  resolves open; closure requires a justification; accretion keeps both ids.
