## ADDED Requirements

### Requirement: Contract bundle release artifact

A contract bundle SHALL be a directory containing exactly `contract.json` (the canonical local-1 extraction output of the release tree, produced by `wild extract` under profile `rust-cargo-local-1`) and `manifest.toml` recording `tool`, `version`, `commit` (the exact git tree the artifact was built from), `profile`, `contract_sha256` (the sha256 of the canonical `contract.json` bytes), `extractor_version`, and `extracted_at`. The shipped shape SHALL be a tar+gzip archive of that directory attached as a release asset; a plain directory SHALL be the local/dev shape. The manifest SHALL be the digest-bound trust-chain head: anything absent from the manifest SHALL be unverifiable by construction. The tool's release CI SHALL extract from the exact tree it builds (the same checkout that produced the published artifact), stamp `contract_sha256`, and attach the bundle to the release. A consumer SHALL refuse a bundle whose recomputed sha256 of `contract.json` differs from `manifest.contract_sha256` (diagnostic `bundle-digest-mismatch`), and SHALL refuse a bundle whose `manifest.commit` does not match the commit of the release being upgraded to (diagnostic `bundle-commit-mismatch`); every refusal SHALL name its diagnostic and SHALL never accept silently.

#### Scenario: Release CI stamps from the build tree

- **GIVEN** a release job that builds a tool artifact and runs `wild extract` in the same checkout
- **WHEN** the attached contract bundle is unpacked
- **THEN** `manifest.toml` records that checkout's exact commit, the `contract_sha256` equals the sha256 of the shipped `contract.json`, and the profile is `rust-cargo-local-1`

#### Scenario: Digest mismatch refused

- **GIVEN** a contract bundle whose `contract.json` bytes differ from the bytes hashed at stamping time
- **WHEN** the consumer verifies the bundle before use
- **THEN** the bundle is refused with the named diagnostic `bundle-digest-mismatch` and is never silently accepted

#### Scenario: Commit mismatch refused

- **GIVEN** a contract bundle whose `manifest.commit` names a different tree than the release being upgraded to
- **WHEN** the consumer verifies the bundle against the target release
- **THEN** the bundle is refused with the named diagnostic `bundle-commit-mismatch` and is never silently accepted

### Requirement: Base-contract caching for installed tools

At install or upgrade commit time, the consuming package manager SHALL cache the installed tool's contract bundle under its state directory as `contracts/<tool>/<version>/` and SHALL record the contract digest in the lock entry for that tool, extending the existing contract-hash pinning of contracted lock entries. A missing or corrupt cached base contract SHALL NOT be fabricated or silently skipped: the compatibility check SHALL run without it only by yielding the Unknown verdict with the named diagnostic `missing-base-contract`, and every cached base used by a check SHALL be digest-verified the same way as a fetched bundle.

#### Scenario: Cached base enables later candidate checks

- **GIVEN** a tool installed at a version whose bundle was cached at install time with the digest recorded in the lock entry
- **WHEN** a later candidate upgrade is checked against the installed base
- **THEN** the check uses the cached base bundle, verifies its digest against the recorded lock-entry digest, and reports the verdict on real evidence

#### Scenario: Missing or corrupt cached base stays unknown

- **GIVEN** a tool installed before bundle caching existed, or a cached base whose bytes no longer match the recorded digest
- **WHEN** a candidate upgrade is checked against the installed base
- **THEN** the verdict is Unknown with the named diagnostic `missing-base-contract` (or the named digest-mismatch diagnostic), and no fabricated or assumed base contract is ever used
