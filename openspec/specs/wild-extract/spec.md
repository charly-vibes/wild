---
id: wild.extract
kind: intent
statement: THE wild extraction layer SHALL turn schemas, source code, and data artifacts of any ecosystem into Contract IR through pluggable, deterministic extractors that never drop a construct silently.
---

# Wild extract

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

The language-blind core sees only IR. Everything ecosystem-specific lives in extractors (schemas, source APIs, feature files, templates) and in law harnesses that run recorded properties against an implementation. Anything an extractor cannot express becomes an opaque, frozen slot and is reported.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| extractor_contract | extension_point | `for every conforming extractor E: extract(source) yields ContractIR, is deterministic, and reports coverage listing every unextracted construct` | [[wild.extract]] |
| law_harness | extension_point | `run(suite, implementation, seed, fixtures, budgets) yields the v1 LawResult; it declares proof, exhaustive, or sampled method and returns pass, counterexample, or inconclusive with all content digests` | [[wild.extract]] |
| extraction_total | invariant | `every parsed declaration relevant to an exported contract maps to a typed or opaque slot; unsupported syntax yields a source-range diagnostic and incomplete extraction, never an invented complete contract` | [[wild.extract]] |
| extractor_deterministic | invariant | `the same supplied source bundle, extractor artifact digest, options, and IR version yield the same canonical IR bytes; imported schemas and generated artifacts must be supplied and hashed as inputs` | [[wild.extract]] |
| extractor_isolated | invariant | `extractors read only the source they are given and perform no network or write access` | [[wild.extract]] |
| ir_versioned | invariant | `emitted IR names its schema version; the core refuses IR of an unknown version` | [[wild.extract]] |
| data_plane_extractors | invariant | `schemas, templates, and feature files have extractors under the same contract as code extractors` | [[wild.extract]] |
| ecosystems_pluggable | invariant | `supporting a new ecosystem requires an extractor only, with no change to the core` | [[wild.extract]] |
| extractor_coverage_reported | advisory | `each extraction reports the share of constructs mapped to opaque slots` | [[wild.extract]] |
| failure_reported | effect | `an unreadable source emits a failure report naming the source and the cause` | [[wild.extract]] |
| extractor_noise_reported | advisory | `each extractor reports false breaks / independently adjudicated candidate breaks, sample size, history range, and adjudication source; zero adjudications yield Unknown, not a zero rate` | [[wild.extract]] |

## Model

### States

- `source_read`
- `parsed`
- `mapped`
- `reported`
- `failed` (emits: [[wild.extract.failure_reported]])

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| parse | source_read | parsed | [[wild.extract.extractor_isolated]] |
| map | parsed | mapped | [[wild.extract.extraction_total]] |
| report | mapped | reported | [[wild.extract.extractor_deterministic]] ∧ [[wild.extract.ir_versioned]] |
| fail_read | source_read | failed | source unreadable under [[wild.extract.extractor_isolated]] |
| fail_parse | parsed | failed | violation of [[wild.extract.extraction_total]] |
| fail_map | mapped | failed | violation of [[wild.extract.extractor_deterministic]] or [[wild.extract.ir_versioned]] |

## Properties

| id | kind | derives_from | generator | predicate | observes |
| -- | ---- | ------------ | --------- | --------- | -------- |
| extractor_reports_coverage | unit | [[wild.extract.extractor_contract]] | `extractor_output_with_unmapped_construct()` | `coverage lists the construct` |  |
| harness_deterministic_given_seed | unit | [[wild.extract.law_harness]] | `harness_run_twice_with_same_seed()` | `result(a) == result(b) or result.status == inconclusive with nondeterminism diagnostic` |  |
| no_silent_drop | unit | [[wild.extract.extraction_total]] | `source_with_unsupported_construct()` | `slot_for(construct) is opaque` |  |
| same_source_same_bytes | unit | [[wild.extract.extractor_deterministic]] | `source_extracted_twice()` | `bytes(a) == bytes(b)` |  |
| extractor_has_no_side_effects | unit | [[wild.extract.extractor_isolated]] | `extractor_run_with_network_and_writes_blocked()` | `extract completes ∧ no write attempted` |  |
| unknown_ir_version_refused | unit | [[wild.extract.ir_versioned]] | `ir_with_version("99")` | `core == refused` |  |
| feature_file_extracts_like_code | unit | [[wild.extract.data_plane_extractors]] | `feature_file_with_known_arity()` | `ir.arity == known_arity` |  |
| new_ecosystem_needs_no_core_change | unit | [[wild.extract.ecosystems_pluggable]] | `extractor_for_new_ecosystem_added()` | `core_diff == empty` |  |
| opaque_share_reported | unit | [[wild.extract.extractor_coverage_reported]] | `source_with_known_opaque_count(3 of 10)` | `report.opaque_share == 0.3` |  |
| unreadable_source_reported | unit | [[wild.extract.failure_reported]] | `source_path_that_does_not_exist()` | `report names the source ∧ the cause` | [[wild.extract.failure_reported]] |
| noise_rate_reported | unit | [[wild.extract.extractor_noise_reported]] | `extraction_run_over_known_history()` | `report has false_break_rate_ppm and adjudicated_breaks; zero denominator yields null` |  |

## Notes

The IR is a common denominator, so extraction is lossy by nature; opaque slots are frozen, which can raise false breaks. That is why noise is measured and reported rather than hidden. Facet-specific extraction (ABI, layout, serialization) arrives as additional extractors under the same contract.

The shared v1 IR, canonical form, consumer manifest, lockfile, sidecar, certificate, and law-result formats are normative in `docs/wild-formats-v1.md` and `schemas/wild-v1.schema.json`. Ecosystem-specific extraction must declare its supported syntax and demand-analysis limits before it can claim complete coverage.

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Extractor contract

The system SHALL satisfy `extractor_contract` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Extractor reports coverage
- **GIVEN** the fixture domain `extractor_output_with_unmapped_construct()`
- **WHEN** the `extractor_contract` check runs
- **THEN** `coverage lists the construct`

### Rule: Law harness

The system SHALL satisfy `law_harness` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Harness deterministic given seed
- **GIVEN** the fixture domain `harness_run_twice_with_same_seed()`
- **WHEN** the `law_harness` check runs
- **THEN** `result(a) == result(b) or result.status == inconclusive with nondeterminism diagnostic`

### Rule: Extraction total

The system SHALL satisfy `extraction_total` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: No silent drop
- **GIVEN** the fixture domain `source_with_unsupported_construct()`
- **WHEN** the `extraction_total` check runs
- **THEN** `slot_for(construct) is opaque`

### Rule: Extractor deterministic

The system SHALL satisfy `extractor_deterministic` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Same source same bytes
- **GIVEN** the fixture domain `source_extracted_twice()`
- **WHEN** the `extractor_deterministic` check runs
- **THEN** `bytes(a) == bytes(b)`

### Rule: Extractor isolated

The system SHALL satisfy `extractor_isolated` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Extractor has no side effects
- **GIVEN** the fixture domain `extractor_run_with_network_and_writes_blocked()`
- **WHEN** the `extractor_isolated` check runs
- **THEN** `extract completes ∧ no write attempted`

### Rule: Ir versioned

The system SHALL satisfy `ir_versioned` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unknown ir version refused
- **GIVEN** the fixture domain `ir_with_version("99")`
- **WHEN** the `ir_versioned` check runs
- **THEN** `core == refused`

### Rule: Data plane extractors

The system SHALL satisfy `data_plane_extractors` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Feature file extracts like code
- **GIVEN** the fixture domain `feature_file_with_known_arity()`
- **WHEN** the `data_plane_extractors` check runs
- **THEN** `ir.arity == known_arity`

### Rule: Ecosystems pluggable

The system SHALL satisfy `ecosystems_pluggable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: New ecosystem needs no core change
- **GIVEN** the fixture domain `extractor_for_new_ecosystem_added()`
- **WHEN** the `ecosystems_pluggable` check runs
- **THEN** `core_diff == empty`

### Rule: Extractor coverage reported

The system SHALL satisfy `extractor_coverage_reported` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Opaque share reported
- **GIVEN** the fixture domain `source_with_known_opaque_count(3 of 10)`
- **WHEN** the `extractor_coverage_reported` check runs
- **THEN** `report.opaque_share == 0.3`

### Rule: Failure reported

The system SHALL satisfy `failure_reported` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unreadable source reported
- **GIVEN** the fixture domain `source_path_that_does_not_exist()`
- **WHEN** the `failure_reported` check runs
- **THEN** `report names the source ∧ the cause`

### Rule: Extractor noise reported

The system SHALL satisfy `extractor_noise_reported` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Noise rate reported
- **GIVEN** the fixture domain `extraction_run_over_known_history()`
- **WHEN** the `extractor_noise_reported` check runs
- **THEN** `report has false_break_rate_ppm and adjudicated_breaks; zero denominator yields null`

#### Acceptance case: Incomplete parser cannot claim complete inventory
- **GIVEN** unsupported syntax prevents inventory of exported declarations
- **WHEN** extraction runs
- **THEN** it emits source-range diagnostics with incomplete coverage, not a fabricated complete contract

#### Acceptance case: No adjudications means unknown false-break rate
- **GIVEN** history has zero independently adjudicated candidate breaks
- **WHEN** the noise report is generated
- **THEN** the rate is Unknown and the denominator is reported as zero
## Requirements
### Requirement: Wild extract design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild extract design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation

### Requirement: Bounded deterministic Rust extraction

The local extractor SHALL implement the rust-cargo-local-1 profile defined in this change's design, bind every result to supplied source/build inputs and extractor identity, and emit existing v1 contracts plus separate provenance and completeness records. It SHALL perform no network access or writes to the source bundle. Equivalent supported declaration structure SHALL yield identical semantic contract bytes independently of checkout location. Unknown declaration inventory SHALL prevent complete extraction claims.

#### Scenario: Repeated extraction and formatting
- **GIVEN** two bundles with equivalent supported declarations, with only whitespace and checkout location different
- **WHEN** the pinned extractor processes both under the same profile and build context
- **THEN** semantic contract bytes match while raw input identities and source provenance remain accurately distinct

#### Scenario: Generated export cannot disappear
- **GIVEN** a macro or build script can generate exported declarations unavailable to the profile
- **WHEN** extraction runs
- **THEN** it reports the construct and incomplete inventory and does not invent a complete contract

#### Scenario: Changed build input requires new extraction
- **GIVEN** a prior report and changed feature selection, target, toolchain, or dependency source
- **WHEN** the prior extraction is submitted for the new bundle
- **THEN** input binding fails and a fresh extraction is required

### Requirement: Explicit consumer demand coverage

The extractor SHALL resolve supported direct consumer usages to provider slots and SHALL disclose every unsupported usage mechanism encountered in the selected source domain. Incomplete demand SHALL prevent scoped-substitution acceptance. Restricting consumer demand SHALL NOT discard required inputs of any selected provider or its transitive dependencies.

#### Scenario: Used and unused removals differ
- **GIVEN** a complete supported consumer demands function a but not function b
- **WHEN** a candidate removes b while retaining a and all required dependency bindings
- **THEN** the scoped structural check can pass although a whole-provider accretion check reports the removal

#### Scenario: Hidden usage blocks a scoped claim
- **GIVEN** the consumer contains an unresolved macro, returned-object method call, or function-pointer flow
- **WHEN** the known direct demand would otherwise pass
- **THEN** the report retains the gap and refuses scoped acceptance with Unknown structural assurance

