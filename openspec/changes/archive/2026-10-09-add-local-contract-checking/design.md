# Local checking design

## Context and goals

The first useful unit is a named consumer boundary checked against an exact candidate artifact. Deterministic means identical supplied inputs yield identical canonical semantic results; it does not mean extraction recovers intent or tests establish universal behavior. Reuse [v1 semantics](../../../docs/wild-formats-v1.md) and [v1 schema](../../../schemas/wild-v1.schema.json).

## Initial profile: rust-cargo-local-1

Use Rust for the runtime and Cargo for the host build. A pinned parser inventories source without executing it. The first profile supports ordinary modules, public free functions, and direct dependency-qualified function calls, including explicit non-glob import aliases when unambiguous. Supported function signatures use unit, bool, i8/i16/i32, and u8/u16/u32. These fit the v1 integer representation exactly. Slot ids derive from crate identity and qualified path, not line numbers. The API facet records source-level callable shape; it does not promise ABI or layout compatibility. Require identical Rust primitive type spelling in this profile; v1 value-set subtyping alone cannot establish that a Rust caller compiles.

Inventory other public declarations as opaque when their boundaries are known. Unsupported generics, traits, methods, returned-object calls, function-pointer flows, glob reexports, macros, FFI, cfg-dependent analysis, build scripts, and generated sources produce explicit gaps. If a construct could introduce declarations or usages the parser cannot inventory, mark the relevant extraction/demand incomplete. Unchanged opaque signatures do not cure missing demand. Merely scanning identifier strings never establishes resolution or completeness. A completely supported fixture can pass; unsupported projects still receive scoped diagnostics. Extending this profile requires new conformance fixtures before broader completeness claims.

Source bundles include normalized relative paths and raw file digests, Cargo manifests/lock, dependency source identities, toolchain/Cargo digests, target, edition, feature selection, and extractor configuration. Files used by the compiler but unavailable to extraction remain visible gaps. The miner receives immutable supplied files with network and writes disabled. Cargo/build execution belongs to a different sandbox, not extraction. Host metadata alone is not a contract for an unanalysed dependency.

Use parser-normalized declaration structure for supported semantic facts, with locations in a separate provenance report. Formatting and absolute checkout paths do not change semantic hashes; raw artifact hashes and provenance still change. Opaque fingerprints remain conservative under existing v1 rules. No incremental cache in the first slice: a full run is the reference implementation.

## Authored obligations and trusted invocation

An accepted obligation names a stable id, consumer/boundary scope, origin (human or agent), predicate/suite digest, and accepting project authority record. Executable suites use v1 law and law_result fields. Declared structural overlays use v1 contracts tied to exact artifacts and explicit coverage; prose is a proposed requirement, not executable evidence. An overlay contradicting mined facts cannot take precedence silently. A proposed correction needs an accepted transition and new evidence. Keep obligations in a separate local document so adding author metadata does not change the v1 contract wire grammar.

Trusted execution receives immutable base and candidate bundles and a separately supplied invocation commitment covering the accepted obligations, original test harnesses, scope, policy, checker, fixtures, environment, budgets, and explicit evaluation time. CI supplies this commitment from its trusted base/configuration, never from candidate-selected paths. A local caller can use the same mechanism, but its report cannot claim independent CI enforcement. Accepting an obligation transition requires the project's existing authority outside the candidate; bind old/new digests, reason, affected consumers, and disposition. Compatibility-preserving edits need no new permission step.

Evaluate the candidate against accepted base obligations first. Added tests/laws are proposals until accepted. Deletions, scope reductions, policy edits, checker replacements, or regenerated candidate contracts cannot remove failures. Authorized intent changes produce a distinct intentional-change disposition, not backward-compatibility success. Run a submitted migration against the original intended outcomes; whether it changes consumer implementation is reported separately by the update workflow.

Law execution supplies fixed fixtures, seed, budgets, and sandbox capabilities. The initial supported backend must enforce no network, no ambient files, controlled environment/time, and no uncontrolled child execution. If it cannot, return inconclusive. Ordinary Cargo build/test logs are useful independent checks but are not automatically v1 law evidence. Build subprocesses run in the update sandbox; law executables run in the stricter law sandbox. Sampled pass remains sampled even if repeatable.

## Commands and data contract

Proposed commands:

```text
wild extract --request extraction.json --output facts/
wild check --request check.json --format json --report report.json
```

The separate local protocol version is local-1; each record has version, kind, and rejects unknown fields/versions. Create its JSON Schema and examples as the first implementation deliverable. Hash local records using v1 canonical JSON rules. This is not a v1 wire-kind extension.

| Record | Required content |
| --- | --- |
| Extraction request | Source bundle commitment, profile id, toolchain/target/features/options, extractor digest; all filesystem references confined to the supplied bundle |
| Check request | Base/candidate bundle commitments, selected consumer and boundary ids, accepted-obligation document digest, policy/checker/harness/fixture digests, environment, budgets, evaluation time, optional externally authorized transition record |
| Obligation record | Stable id, scope, origin, structural contract or executable suite digest, accepting authority record, accepted/proposed state; no unchecked prose predicate treated as executable |
| Local report | Input commitments, schema/profile/tool versions, v1 envelope, generated document digests, completeness/gaps and provenance, obligation changes, law results, stable diagnostics, execution status, evaluation outcome, and disposition |

Use the existing v1 envelope on stdout in JSON mode; extra local information goes in the explicitly requested report file. Reports write only to requested output locations, never source/manifests/CI. Diagnostics use codes such as incomplete-demand, unsupported-construct, obligation-change, input-mismatch, and law-inconclusive. No bare unqualified "compatible" result.

Outcome mapping preserves v1 semantics: an executed policy acceptance is accept; a computed structural/law counterexample or definite policy prohibition is reject; unmet requirements due only to missing/inconclusive evidence are unknown; malformed input or failed orchestration is error. A definite counterexample takes precedence over an unrelated gap, with both reported. Both reject and unknown map to envelope decision refuse and exit 1. Errors use exit 2 and refuse, never an accepting envelope. Law timeout/crash is inconclusive/unknown if the runner successfully captures that result; a failed runner is error. Successful accepted checks exit 0. Structural assurance remains Reject/Unknown/PassDeclared independently of law and operational status. Unsupported CLI profile selection is an input error; an unsupported construct in a recognized profile is a coverage gap.

## Boundaries with existing design

This standalone local check does not activate adoption gate/native modes, create a historical baseline acknowledgement, or skip an adoption-level transition. Existing observe/shadow/gate rules remain unchanged. A local accepted-base commitment is distinct from the adoption layer's expiring debt acknowledgements. No certificate claims registry ancestry, publication, or complete v1 conformance. Unknown required trust/attestation evidence cannot be synthesized to make a policy pass.

## Risks and acceptance

The deliberately narrow parser profile may abstain on most real libraries. E1 measures that limitation before broadening the implementation; synthetic success cannot establish adoption value. The first fixture pair must include an unused removed public function and a used removed function, a hidden macro-generated usage, tampered obligations, equivalent formatting, and changed artifact/harness bytes. If authored laws add no value over ordinary tests, the product can ship mining-only; the interface need not force contract authoring.

## Spec integration

Add the proposed requirements without replacing the existing design-contract gates or claiming unimplemented general rules now execute. During apply, register executable scenarios with espectacular only as their real tests land. Keep the dual-format Constraints/Properties/Rule sections aligned with the scoped new runtime requirements during integration. Broader guarantees outside rust-cargo-local-1 stay future design cases.
