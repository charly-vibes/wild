# Wild local-1 protocol

The local-1 protocol is the separately versioned wire format for bounded
local contract checking (beads wild-mh5.1, change
`add-local-contract-checking`). It is **not** a v1 wire-kind extension:
local records are self-describing, each carries `version: "local-1"` and a
`kind`, and unknown versions, kinds, or fields are refused. Local record
identity uses the canonical JSON rules of
[wild-formats-v1.md](wild-formats-v1.md) unchanged.

The machine-readable schema is
[wild-local-v1.schema.json](../schemas/wild-local-v1.schema.json). The
reader applies the same v1 refusal rules to every local record: duplicate
object keys, floating-point numbers, integers outside the exact range,
unpaired surrogates, leading byte-order marks, and raw control characters
are refused before any interpretation. Examples for every record kind live
in [examples-local.json](../schemas/examples-local.json).

## Records

| Record | kind | Required content |
| --- | --- | --- |
| Extraction request | `extraction-request` | Profile id (`rust-cargo-local-1`), bundle root, per-file raw sha256 commitments, target, toolchain, feature selection, extractor identity; every filesystem reference confined to the supplied bundle |
| Extraction report | `extraction-report` | Profile id, `complete_inventory` flag, stable diagnostics (`incomplete-demand`, `unsupported-construct`, `input-mismatch`) |
| Demand | `demand` | Ordered entries naming consumer crate, resolved callee, optional local alias, and the bound provider slot id |
| Provenance | `provenance` | Bundle root, per-file raw digests, source locations for supported slots and demand sites |

Slot ids derive from crate identity (package name plus version) and the
qualified declaration path — never from line numbers. Semantic contract
bytes are identical across checkout locations and formatting; provenance
and raw digests stay location- and byte-accurate. Opaque inventories
fingerprint declaration structure, not source text.

## Command and exit mapping

```text
wild extract --request extraction.json --output facts/
```

The command writes only the requested output directory (contract.json,
demand.json, provenance.json, report.json), performs no network access,
and never writes to the source bundle. Stdout carries the v1 envelope;
extra local information lives in the requested report artifacts.

Outcome mapping preserves the v1 envelope semantics:

| Outcome | Envelope decision | Exit |
| --- | --- | --- |
| Complete supported inventory | accept | 0 |
| Gaps: incomplete demand or unsupported constructs | refuse (Unknown) | 1 |
| Malformed input, digest mismatch, changed build input, out-of-bundle reference | refuse (error-class, `input-mismatch`) | 2 |

A changed feature selection, target, toolchain, or dependency source
invalidates the old request's raw digests; resubmission fails with
`input-mismatch` and a fresh extraction is required. Changed build inputs
never silently rebind.

## Scope

This slice implements the extraction half of local-1. The check command,
obligations, trusted invocation, and law execution are future slices; the
local-1 report kind for `wild check` is defined by
`openspec/changes/add-local-contract-checking/design.md` and lands with
its implementing ticket.
