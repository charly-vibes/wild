# Bootstrap fixtures — wild-aoq.5

Immutable development fixtures for the controlled update evaluation harness
(`openspec/changes/add-update-evaluation-harness`). They replay two genuine
native Cargo update outcomes — a compatible out-of-range major refused by the
declared range, and a breaking in-range patch that resolves and then fails the
consumer's tests — plus four declaration-only checker/protection cases. There
is no Wild binary here: expected checker and protection outcomes are
declarations, never claimed runtime verification.

## Layout

- `registry/index/de/pt/dept` — frozen git-index-style catalog: one JSON line
  per committed `dept` version (name, version, dependency list, sha256
  checksum). This is the canonical provenance record for the catalog.
- `registry/index/dept/<version>/dept-<version>.crate` — the committed
  `.crate` files backing each catalog line.
- `registry/index/config.json` — catalog metadata; the `dl` template mirrors
  the committed store layout.
- `consumer/` — the replayed consumer crate (`dept = "~1.2"`), committed with
  `Cargo.lock` pinned to the 1.2.3 baseline.
- `consumer/registry-mirror/` — byte-identical local-registry projection of
  the frozen catalog (same `.crate` files, same index entry) used by the
  offline replay through Cargo's own registry machinery.

## Why a registry-mirror

The replay must run fully offline from a fresh `CARGO_HOME`, and offline Cargo
can neither fetch a git index nor perform file-URL downloads. A `[source]`
`local-registry` is pure filesystem yet keeps full registry semantics —
checksum verification, version-range enforcement by Cargo's resolver, and the
genuine `--precise` refusal for range-excluded targets. Path replacement
(`[patch]`/`paths`) is deliberately absent: ranges are enforced by real Cargo
resolution, never bypassed.

## Toolchain

Recorded in `cases.json` under `toolchain.rustc` (exact `rustc --version`
output). The committed identity is authoritative; a toolchain drift must
append a new fixture version, never rewrite this one.

## Versioning policy

Fixture commitments are immutable. Changing an expectation appends a new
version of the affected artifact (and a new catalog line where applicable)
with justification in the change proposal; history is never rewritten. The
digests in `cases.json` are the integrity contract checked by
`tests/test_initial_update_fixtures.py`. These are development fixtures, not
the sealed evaluation set.
