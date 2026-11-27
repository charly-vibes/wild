# faq

# FAQ & troubleshooting

## Is `wild` production-ready?

No. Wild is a **prototype**: a design with a Rust implementation of the
`wild extract` and `wild check` subcommands (runtime-tested, see
`tests/runtime/`), plus Python simulations and small real-project
experiments. The manual (`docs/wild-manual.md`) marks which parts of the
intended interface are implemented. The simulations use small synthetic
models and say nothing about real registries.

## Why is the crates.io package called `wild-vibes`?

The `wild` crate name on crates.io belongs to an unrelated glob-expansion
crate. The publishable package is therefore [`wild-vibes`](https://crates.io/crates/wild-vibes);
the binary, the repository, and the wire-format identities remain `wild`:

```sh
cargo install wild-vibes   # installs the `wild` binary
```

## What wire formats does it speak?

[Wild v1 formats](wild-formats-v1.md) is the normative design protocol for
contracts, manifests, locks, sidecars, policy and certificate bundles; the
JSON Schema (`schemas/wild-v1.schema.json`) and structural examples
(`schemas/examples-v1.json`) cover it. The separately versioned **local-1
protocol** (`docs/wild-local-v1.md`) is what the implemented `extract`,
`check`, and `update` commands actually speak today. The Python prototypes
implement smaller models and do not implement the v1 protocol.

## Every command prints a JSON envelope — what do the fields mean?

Every command emits a v1 envelope on stdout carrying `decision` (`accept` /
`refuse`), `assurance`, `slots`, `coverage`, the `checker` identity, and
`diagnostics`. Exit codes map to outcomes: **0 = accept, 1 = refuse
(unknown/reject), 2 = error** (malformed input or failed orchestration).

## My command failed with exit 2 and a `input-mismatch` diagnostic

The request file could not be read or was malformed local-1. Check that the
`--request` file exists, is valid JSON, and matches the local-1 schema; the
usage line on stderr shows the exact accepted flags
(`wild extract --request <file> --output <dir>`,
`wild check --request <file> --format json --report <file>`).

## My extraction `refuse`d with `Unknown` assurance

The extraction completed but the inventory was incomplete or diagnostics
were non-empty, so wild will not claim `PassDeclared`. Read the
`diagnostics` array in the envelope and the `extraction-report` written to
the requested `--output` directory.

## Wild refuses because base digests changed

`wild check` and `wild update plan` bind requests to per-file sha256
commitments of the supplied bundles. If the bundle drifted after the
request was made, the command refuses (e.g. `base-changed`). Re-extract to
produce a fresh request against the current bytes.
