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
| Check request | `check-request` | Profile id, consumer scope, base and candidate bundle commitments (per-file sha256), target, toolchain, features, fixed policy literal, trusted obligations reference, checker identity, optional trusted transition record; every filesystem reference confined to the supplied bundles |
| Check report | `check-report` | Consumer scope, policy, per-slot verdicts, obligation verdicts, obligation changes, transition echo, invocation commitment, per-side extraction summaries, disposition, decision, assurance, stable diagnostics |
| Obligations document | `obligations` | Accepted and proposed obligation records: stable id, consumer/boundary scope, origin (`human` or `agent`), state, accepting authority (name plus digest), and a digest-bound predicate (structural contract record or executable law suite digest); prose is never an executable predicate |
| Transition record | `transition` (check-request field) | Externally authorized old-to-new obligation change: old and new digest, reason, affected consumers, authority digest; supplied by the trusted caller, never by the candidate |

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

## Protected context

The check request binds accepted obligations through a separate trusted
document referenced by `{digest, path}`: the checker digest-verifies the
document before use and the candidate never supplies or selects accepted
context. Each accepted obligation is evaluated against the candidate
regardless of any candidate-sourced signal:

- a structural predicate binds its contract record by content digest; the
  base side must carry the bound slots with the exact accepted types
  (a stale document that no longer describes the trusted base is an
  error-class refusal), and the candidate must carry them with accreting
  types — a narrowed type is a definite weakening reported as
  `obligation-change` with a proposed-weakening change record;
- a law predicate binds executable suite bytes by digest; the base bundle
  must contain the suite (else error), a candidate that drops the suite is
  a definite weakening with a proposed-deletion change record, and a
  retained law without execution evidence stays `law-inconclusive` unknown
  until genuinely checked;
- proposed-state obligations are reported with their origin but never
  enforced — candidate additions remain proposals and cannot replace
  accepted obligations;
- an externally authorized transition binds old and new commitment digests
  with reason, affected consumers, and authority; when the accepted
  replacement obligation matches the candidate exactly and all unchanged
  obligations still hold, the disposition is
  `accepted-intentional-change` — never backward-compatibility success;
  a transition that names no accepted replacement is an error-class
  refusal.

The report's `invocation_commitment` records enforcement as `local` (a
local caller cannot claim independent CI enforcement) and pins the
obligations/checker/policy/bundle digests; harness, fixture, budget, and
evaluation-time commitments are present as explicit nulls until their
slices land, so the report shape does not change again.

## Scope

This slice implements the extraction half of local-1 plus the protected-
context check half: scoped structural checking, accepted-obligation
enforcement from a trusted external document, and externally authorized
obligation transitions. Law execution (running retained suites under a
bounded harness) and the full invocation commitment (harnesses, fixtures,
budgets, evaluation time) remain future slices; their report fields exist
as explicit nulls. The local-1 report kind for `wild check` is defined by
`openspec/changes/add-local-contract-checking/design.md`.
