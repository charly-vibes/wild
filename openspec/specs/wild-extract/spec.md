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

The local extractor SHALL implement the rust-cargo-local-1 profile defined in this change's design, bind every result to supplied source/build inputs and extractor identity, and emit existing v1 contracts plus separate provenance and completeness records. It SHALL perform no network access and SHALL perform no writes to the source bundle. Equivalent supported declaration structure SHALL yield identical semantic contract bytes independently of checkout location.

#### Scenario: Repeated extraction and formatting
- **GIVEN** two bundles with equivalent supported declarations, with only whitespace and checkout location different
- **WHEN** the pinned extractor processes both under the same profile and build context
- **THEN** semantic contract bytes match while raw input identities and source provenance remain accurately distinct

### Requirement: Unknown inventory prevents complete claims

Unknown declaration inventory SHALL prevent complete extraction claims.

#### Scenario: Generated export cannot disappear
- **GIVEN** a macro or build script can generate exported declarations unavailable to the profile
- **WHEN** extraction runs
- **THEN** it reports the construct and incomplete inventory and does not invent a complete contract

#### Scenario: Changed build input requires new extraction
- **GIVEN** a prior report and changed feature selection, target, toolchain, or dependency source
- **WHEN** the prior extraction is submitted for the new bundle
- **THEN** input binding fails and a fresh extraction is required

### Requirement: Text-like scalar support set

The profile's signature subset SHALL treat `String` as a supported owned-text scalar (`text-owned`) and `&str` and `&String` as a supported borrowed-text scalar (`text-borrowed`), each emitted without interval fields; mutable text references, bare `str`, and other text-like constructs SHALL remain unsupported and disclosed.

#### Scenario: Text-taking public functions become genuine slots
- **GIVEN** a provider whose public functions take or return text (arguments of `&str`, `String`, or `&String`, and a `String` return)
- **WHEN** extraction runs
- **THEN** the functions surface as function-type slots whose arguments and results carry the `text-borrowed`/`text-owned` scalars with no interval fields, `&String` normalizes to `text-borrowed`, and the report claims complete inventory with no diagnostics

#### Scenario: Mutable and bare text stays unsupported
- **GIVEN** a provider with a public function taking `&mut str` (or bare `str`, `char`, `Cow<str>`)
- **WHEN** extraction runs
- **THEN** the report retains the unsupported-construct gap, the function surfaces as an opaque slot, and inventory is incomplete

### Requirement: Public enum variants inventory as named slots

A public enum without cfg gating SHALL inventory each of its variants as a named slot under the enum's qualified meaning (`<crate>::<Enum>::<Variant>`) instead of a single opaque enum item, following the identity law (crate identity plus qualified path, never line numbers); cfg-gated variants and generic public enums SHALL keep the honest gap.

#### Scenario: Public enum variants become named slots
- **GIVEN** a provider whose public enum declares two variants and a consumer that constructs a dep-qualified variant
- **WHEN** extraction runs
- **THEN** each variant inventories as a named slot under the enum's qualified meaning, the single opaque enum item does not appear, the variant construction resolves as supported demand, and the extraction claims complete inventory with no diagnostics

### Requirement: Impl blocks accounted per construct

Impl blocks SHALL be accounted per construct: public inherent impl methods SHALL inventory as type-qualified opaque slots (`<crate>::<module>::<Type>::<method>`), plain-private impl items SHALL carry no public API surface, and trait impls together with restricted-visibility (`pub(crate)`/`pub(in)`) impl items SHALL keep named unsupported-construct gaps; impl bodies SHALL be walked so demands inside them are never silently dropped.

#### Scenario: Trait impls and restricted impl items are disclosed per construct
- **GIVEN** a provider with an inherent impl exposing a public method, a private method, and a `pub(crate)` method, plus two trait impls on the same type
- **WHEN** extraction runs
- **THEN** the public method inventories as a type-qualified opaque slot, the private method carries no public API surface, and the report retains named unsupported-construct gaps for the `pub(crate)` method and each trait impl — with no blanket impl-block gap

### Requirement: Explicit consumer demand coverage

The extractor SHALL resolve supported direct consumer usages to provider slots and SHALL disclose every unsupported usage mechanism encountered in the selected source domain. Incomplete demand SHALL prevent scoped-substitution acceptance. Restricting consumer demand SHALL NOT discard required inputs of any selected provider or its transitive dependencies.

#### Scenario: Used and unused removals differ
- **GIVEN** a complete supported consumer demands function a but not function b
- **WHEN** a candidate removes b while retaining a and all required dependency bindings
- **THEN** the scoped structural check can pass although a whole-provider accretion check reports the removal

#### Scenario: Hidden usage blocks a scoped claim
- **GIVEN** the consumer contains an unresolved macro, a method call whose receiver is outside the bounded resolution shapes, or a function-pointer flow
- **WHEN** the known direct demand would otherwise pass
- **THEN** the report retains the gap and refuses scoped acceptance with Unknown structural assurance

### Requirement: Whitelisted std macro demand profile

Macro invocations in expression or statement position whose head is a whitelisted std macro with a closed, argument-confined expansion and whose token trees parse as a comma-separated expression list SHALL be part of the supported demand profile: their arguments SHALL be descended and any demands found there recorded like direct calls, and they SHALL NOT emit an incomplete-demand gap.

#### Scenario: Argument-confined std macro does not block a scoped claim
- **GIVEN** a consumer whose code contains a whitelisted std macro invocation in statement position (e.g. `println!("v={}", 1);`) alongside a direct dependency-qualified provider call
- **WHEN** extraction runs
- **THEN** the std macro emits no incomplete-demand gap and the provider call still resolves to a provider slot

#### Scenario: Demands inside supported macro arguments are recorded
- **GIVEN** a whitelisted macro invocation in expression or statement position whose arguments reference provider functions (e.g. `assert_eq!(a(), b())`) and no other consumer code calls those functions
- **WHEN** extraction runs
- **THEN** the demands for a and b are recorded exactly like direct calls

### Requirement: Unsupported macro demand stays disclosed

Any other macro invocation in expression or statement position SHALL keep the incomplete-demand disclosure rather than being silently skipped.

#### Scenario: Unsupported macro remains disclosed
- **GIVEN** a macro invocation in expression or statement position with an unlisted head, or a whitelisted macro whose tokens do not parse as a comma-separated expression list
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap and refuses scoped acceptance with Unknown structural assurance

#### Scenario: format_args! does not block a scoped claim
- **GIVEN** a consumer whose code contains a routed `format_args!` invocation with positional arguments (e.g. `writer.write_fmt(format_args!("hello {}", "world"));`) alongside a direct dependency-qualified provider call
- **WHEN** extraction runs
- **THEN** the `format_args!` invocation emits no incomplete-demand gap and the provider call still resolves to a provider slot

#### Scenario: Demands inside format_args! arguments are recorded
- **GIVEN** a routed `format_args!` invocation with positional arguments referencing provider functions (e.g. `writer.write_fmt(format_args!("v={} plus {}", add_one(1), 2));`) and no other consumer code calls `add_one`
- **WHEN** extraction runs
- **THEN** the demand for `add_one` is recorded exactly like a direct call

#### Scenario: Demands inside format_args! named-argument values are recorded
- **GIVEN** a routed `format_args!` invocation whose named-argument value references a provider function (e.g. `take_args(format_args!("{x} then {x}", x = add_one(1)));`) and no other consumer code calls `add_one`
- **WHEN** extraction runs
- **THEN** the demand for `add_one` is recorded exactly like a direct call and no incomplete-demand gap is emitted

### Requirement: Format capture naming a provider item is disclosed

A whitelisted macro invocation whose format string implicitly captures an identifier that names a provider item SHALL keep the incomplete-demand disclosure.

#### Scenario: Format capture naming a provider item is disclosed
- **GIVEN** a consumer with a whitelisted macro invocation whose format string implicitly captures an identifier naming a provider value item — directly (`use provider::MAX;` followed by `println!("max={MAX}");`) or through a consumer-side alias (`use provider::MAX as LIMIT;` followed by `take_args(format_args!("{LIMIT}"));`) — and no other consumer code references that provider item
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap and refuses scoped acceptance with Unknown structural assurance

### Requirement: Bounded method-call resolution

A method call whose receiver resolves in the bounded shapes — a path expression resolving through the bounded demand rules, or a call expression whose head resolves to an inventoried constructor or free function with a recorded syntactic return type — SHALL create the demand `<crate>::<Type>::<method>`: resolution against the inventoried impl-method or typed slots yields supported demand, and a method absent from the inventory SHALL keep the incomplete-demand gap naming the full path.

#### Scenario: Resolved method call becomes supported demand
- **GIVEN** a consumer whose method call's receiver is a call resolving to an inventoried same-crate constructor with a recorded syntactic return type (e.g. `Meter::new().tick()` where `new` returns `Meter`)
- **WHEN** extraction runs
- **THEN** the demand `Meter::tick` is recorded and resolves against the inventoried type-qualified impl-method slot with no incomplete-demand gap

#### Scenario: Method absent from inventory keeps gap
- **GIVEN** a consumer whose method call's receiver resolves in the bounded shapes but whose method is absent from the inventory (e.g. `Meter::new().tock()`)
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming the full `<crate>::<Type>::<method>` path and refuses scoped acceptance with Unknown structural assurance

### Requirement: Unbounded method-call receivers stay disclosed

A method-call receiver outside the bounded shapes — a multi-hop chain beyond one resolved hop, field access, macro output, or an unknown identifier — SHALL keep the incomplete-demand gap naming the receiver.

#### Scenario: Unbounded method receiver keeps gap
- **GIVEN** a consumer with a multi-hop method chain beyond one resolved hop (e.g. `Meter::new().tick().untick()`)
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming the receiver, and the one-hop demand inside the chain is still recorded

### Requirement: Enum-variant demand resolution

Enum-variant demand paths SHALL resolve as supported demand when the variant is inventoried; unknown variant paths SHALL keep the incomplete-demand gap naming the path.

#### Scenario: Variant demand paths resolve
- **GIVEN** a consumer that constructs a dep-qualified inventoried variant (e.g. `provider::Mode::Slow(1)`) and a same-crate inventoried variant in expression position (e.g. `let f = Flavor::Sour;`)
- **WHEN** extraction runs
- **THEN** both demands are recorded as supported and no incomplete-demand gap is emitted

#### Scenario: Unknown variant paths keep the gap
- **GIVEN** a consumer referencing `provider::Mode::Huge` and a same-crate `Flavor::Salty`, neither inventoried
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming each path and refuses scoped acceptance with Unknown structural assurance

