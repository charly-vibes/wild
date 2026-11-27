# Changelog

Notable user-visible changes to wild. Format: [Keep a Changelog](https://keepachangelog.com/) style, one section per release.

## [Unreleased]

### Added

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
