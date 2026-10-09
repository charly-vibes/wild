# Semantic conformance and hierarchical composition

Date: 2026-10-09. Research project: semantic-composition. Tracking: wild-9co.
Status: investigation protocol and bounded findings; no architecture adoption or runtime implementation approval.

## Question and current answer

Can an assembly become a reusable component whose public obligations survive internal replacement, including implementations in different languages?

Current answer: Wild specifies structural assembly/substitution and evidence envelopes. It does not yet implement a v1 runtime or define a recursive composite boundary. A manually authored boundary with independent law evaluation is a plausible experiment, not an empirically selected architecture. Automatic derivation of public behavior from children needs an additional refinement theory and checker.

Compare hierarchy and semantic assurance independently. A flat assembly can have an excellent end-to-end oracle; a nested composite can have none. Packaging alone must never earn a behavioral advantage in the matrix.

## Evidence ledger

Paths in this table are relative to the repository root unless prefixed Specodelic. Hashes and working-tree state are in [source-manifest.json](evidence/source-manifest.json). Source reports are preserved under [sources](evidence/sources/semantic-assessment.md), including the [hierarchical report](evidence/sources/hierarchical-assessment.md). Reports describe unpinned web snapshots; their original identities remain unknown.

| ID | Source and exact locus | Established answer | Limit |
| --- | --- | --- | --- |
| E01 | docs/wild-formats-v1.md:27–54, Contract IR and subtyping | Meaning is declared; accretion preserves structure, law definitions and scope. | No implication that implementations satisfy retained laws. |
| E02 | docs/wild-formats-v1.md:56–68; openspec/specs/wild-compose/spec.md, composition_is_category | Composition is a flat union modulo renaming, with closure, singleton and relation checks. | “Exposed interfaces” has no explicit boundary mapping in the v1 assembly schema. |
| E03 | schemas/wild-v1.schema.json:400, law; :672, assembly | Law = id/suite/slots; assembly = roots/components/bindings; unknown fields forbidden. | No first-class nested assembly/public-contract field. |
| E04 | docs/wild-formats-v1.md:70–100 | Evidence binds artifacts and harnesses; policy is reevaluated; missing proof stays inconclusive. | Assembly-scoped wrapper evidence linkage is not defined as a new wire construct. |
| E05 | prototype/wild_cat_sim.py, laws / well_formed / certify / verify | Executable toy accretion, provider existence, and certificate checks. | laws checks accretion reflexivity/transitivity, not associativity of nested public interfaces; hashes are truncated toy identities. |
| E06 | tests/test_prototype_smoke.py:28–48; prototype/wild_sim.py, cases 3b/3c/3d/4c | Same-shape behavioral failures escape without applicable laws/evidence. | Dictionary-based simulations, not real reservation components. |
| E07 | openspec/changes/add-local-contract-checking/design.md, Authored obligations and trusted invocation | Existing proposal protects accepted obligations, scope and harness from the candidate. | Proposed Rust/Cargo slice; not implemented Wild runtime. |
| E08 | experiments/update_eval.py, module contract and cmd_run | Validation/summary infrastructure exists; run scaffolding is distinct from experiment execution. | Not a semantic compatibility checker. Source was already modified by other work; snapshot hash is recorded. |
| E09 | Specodelic src/kernel.rs:1–45; src/compile.rs, kernel_binding_of_row; tests/kernel_binding.rs:1–15 | Kernel evaluates finite specification instances; binding strings are carried opaquely. | A kernel result is not evidence that an application trace conforms. Source inspection only; sibling tests not executed. |
| E10 | Specodelic src/compile.rs, FRAGMENT_LANGUAGES / validate_fragments; specs/compile.md, fragment_guard_rejected | Rust fragments have an executable path; py/ts tags do not establish corresponding emitters; executable Rust transition guards are rejected in this revision. | Do not claim generic cross-language transition semantics. Current local source, not a v0.7.0 release audit. |
| E11 | evidence/probe.py and probe-results.json | Six bounded schedules distinguish atomic from stale commits despite identical toy interface shape. | Illustrative finite model; no real concurrency, time, network, Rust/Python equivalence or v1 certificate. |

Wild source base: 60b860bc4a215f8a0825a21e3079b5afbaeee359, dirty tree. Specodelic source base: 21f6f3feb1516f56dbb64edee180d710610b6290, clean at capture. The local source checks resolve some report UNKNOWNs; they do not retroactively identify the reports' original snapshots.

## Semantic levels to evaluate

| Level | Inputs and interpretation | Permitted claim | Required refusal/unknown boundary |
| --- | --- | --- | --- |
| S0: declared structure | Slots, types, demands, meanings, closure | Declared structural compatibility | No behavioral claim from names, shape or equal hashes |
| S1: independent boundary laws | Accepted oracle, event projection, implementation/closure, fixed fixtures and schedules | Pass/counterexample within the recorded method and domain | Missing adapter or unobserved required event cannot pass |
| S2: bounded semantic profile | Explicit input/event/state vocabulary and total interpretation for a supported fragment | Conformance to that profile within finite bounds | Unsupported timing, concurrency, state or predicate stays unknown |
| S3: derived refinement | Child assumptions/guarantees, parent model, abstraction relation, composition proof | Only the property actually established under stated assumptions | Child structural passes or cyclic assumptions cannot substitute for a proof |

Specodelic graph checks can support mapping integrity at any level; they are not S2 application semantics by themselves. Preserving ids or compiling opaque bindings does not create an observation adapter. A law-suite artifact should commit to the oracle/profile it executes; this investigation proposes no new v1 fields.

## Two-layer example and executed answer

Boundary: one reservation, initially held. Coordinator exposes confirm and expire; storage exposes read and commit. Public observations are successful terminal responses tagged with the same reservation id. Requirement: no execution produces both successful confirmation and successful expiration for that reservation. Internal reads are hidden; terminal responses must not be hidden.

The probe enumerates all six interleavings of two operations, each with read before commit. Atomic storage compares the current state at commit; stale storage trusts its prior read. Both have the same toy interface. Atomic storage violates the public requirement on 0/6 schedules; stale storage violates it on 4/6. The toy shape checker accepts the identical declared contracts.

This answers a narrow question: interface identity is insufficient for this parent safety property. It does not show that wrappers outperform flat assemblies: the same oracle catches the violation in either representation. It also does not prove liveness, linearizability, correctness under retries or real language memory models. A successful replacement still needs a second conforming implementation, not merely running the baseline twice; case C02 specifies that future comparison.

Reproduce from the repository root:

```sh
python .wai/projects/semantic-composition/research/evidence/probe.py
python -m pytest -q tests/test_spec_corpus.py tests/test_prototype_smoke.py -k 'not cat_sim'
```

The preceding discussion executed 22 focused tests successfully. The saved probe additionally records all 76 toy contract states / 438,976 triples, 1,000 generated substitutions (seed 11), and ten toy certificate studies (seed 9). These are separate scopes and must not be aggregated into a runtime conformance percentage.

## Candidate observation protocol

This is an experiment design, not normative Wild syntax. Freeze accepted intent, oracle, fixtures, input serialization, environment and checker before evaluating candidates. Record call/return event kind, operation, reservation id, result, and deterministic scheduler step. Declare whether step order is total and which internal events the projection hides. Preserve public success, failure and timeout distinctions. Malformed, missing or ambiguous events invalidate the observation; they must not become an empty passing trace.

For the finite safety pilot, define admissible traces explicitly and test inclusion in the allowed set after projection. Trace inclusion alone does not establish progress: add a separate completion/deadlock obligation, with bounded outcomes distinct from unbounded liveness. A timeout is inconclusive execution unless the protocol explicitly makes it an observable domain outcome.

Cross-language equivalence requires two actual implementations and independently maintained adapters/oracle. Compare identical input domains and observation semantics, not identical generated source. First preserve the reservation semantics in one language; a two-language pilot is separate from the first Cargo product slice.

## Candidate composite identity and closure

For the experiment, keep public contract identity separate from implementation/assembly identity. The evidence record should commit to the exact internal assembly, public boundary mapping, observation adapter, accepted oracle/profile, harness, fixtures, checker and execution bounds. This is proposed external experiment metadata; a claim of conforming v1 wrapper evidence needs a later protocol decision. Do not pass an assembly digest into a field defined as a raw implementation artifact digest.

Reevaluate public laws when a covered internal artifact, mapping, adapter or oracle changes; reuse only checks whose complete inputs are unchanged. Recompute current policy with current validity inputs. No measured incremental-rebuild benefit is claimed.

Flattening must preserve real instance identity and explicit sharing. Two wrappers referencing the same singleton must not silently create two instances. Conversely, two distinct singleton instances must not become one merely because their contract hashes match. Shared-instance and evidence-commitment cases are retained provisionally pending human judgment from the Rule-of-5 pass; the experiment can measure them without selecting a final representation.

## Decision boundary

See the [approach matrix](../designs/matrix/problem.md), [case matrix](../designs/2026-10-09-case-matrix.md), and [review](../reviews/2026-10-09-rule-of-5.md). No architecture is selected. Authored wrappers are the first experimental candidate; flattening with the same oracle is the control. Advance to first-class composites only if explicit packaging produces a measured benefit and passes the same failure cases. Advance to derived refinement only when assumptions, abstraction and a checkable proof obligation are defined.

Task status lives in Beads wild-9co and its children; this document records knowledge and evaluation criteria, not a duplicate task list.
