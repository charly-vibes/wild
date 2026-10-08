---
id: wild.compose
kind: intent
statement: THE wild composer SHALL decide whether components at given revisions compose into a well-formed assembly, select revisions by deterministic lineage lookup within the supported model, and emit a certificate an independent verifier can re-check.
---

# Wild compose

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

An assembly is components plus bindings from required slots to provided slots. It is well-formed when every required slot is bound by a compatible provide. Substituting a component by an accretion of itself preserves well-formedness, which is what makes resolution a lookup instead of a search. Verdicts carry certificates that a separate verifier checks from content hashes.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| assembly_is_bindings | invariant | `an assembly is a set of component revisions plus bindings from each required slot to a provided slot` | [[wild.compose]] |
| binding_well_formed | invariant | `a binding is well-formed iff the v1 subtype relation holds for provider output and consumer input, limits and defaults satisfy demand, and facets and relations pass; an open provider sum binds only to an open consumer` | [[wild.compose]] |
| required_slots_bound | invariant | `every required input of every component is bound by a well-formed binding` | [[wild.compose]] |
| substitution_preserves_assembly | invariant | `replacing a component with an accretion of itself keeps a well-formed assembly well-formed` | [[wild.compose]] |
| scoped_substitution | invariant | `scoped replacement preserves every demanded output AND validates all required inputs of the replacement and its transitive dependency closure; restricting demand never hides newly introduced required inputs` | [[wild.compose]] |
| resolution_by_lineage | invariant | `for a finite registry snapshot with one accepted tip per lineage, resolve traverses dependency closure using deterministic newest-tip lookup; missing tips, unmerged forks, singleton conflicts, or relation failures refuse selection without backtracking; dependency cycles reach a fixed point and are checked as a whole` | [[wild.compose]] |
| resolver_deterministic | invariant | `the same registry snapshot and demand yield the same selection and certificate` | [[wild.compose]] |
| lineage_copies_listed | invariant | `when consumers demand different lineages of one package, each lineage is resolved separately and the copies are listed` | [[wild.compose]] |
| scoped_merge_proposed | invariant | `a consumer may be proposed a newer lineage when its demand accretes there; the move is a proposal and is never applied automatically` | [[wild.compose]] |
| boundary_needs_adapter | invariant | `values crossing between lineages need a registered adapter; otherwise the boundary is reported unbridged` | [[wild.compose]] |
| singleton_declared | invariant | `a component declared singleton appears under exactly one lineage per assembly; a violation is a composition failure` | [[wild.compose]] |
| relation_slots | invariant | `v1 equal and less_equal relations over declared scalar slots are checked after closure; missing values, incomparable types, and failed relations refuse composition; the resolver does not search older revisions to satisfy relations` | [[wild.compose]] |
| certificate_lists_bindings | invariant | `the v1 certificate names the assembly commitment, component instances, bindings, demanded slots, policy, checker, and content-addressed proof records; the bundle contains every referenced contract and proof` | [[wild.compose]] |
| certificate_complete | invariant | `verification compares the certificate assembly hash to the caller-supplied expected commitment, reconstructs closure from all component manifests, and rejects missing roots, components, demands, or required bindings` | [[wild.compose]] |
| certificate_tamper_evident | invariant | `a corrupted hash or dropped binding fails verification; a substituted provider verifies only if it is compatible with the consumer's demand` | [[wild.compose]] |
| verifier_reads_only_certificate | invariant | `the verifier reads the v1 bundle, caller-supplied assembly commitment, policy, trust roots, and evaluation time; it never calls the resolver or network` | [[wild.compose]] |
| verification_linear | advisory | `verification performs O(B + S + P) indexed visits over bindings B, reachable contract/schema nodes S, and proof bytes P, excluding explicitly budgeted proof execution; benchmarking reports all three sizes and checker version` | [[wild.compose]] |
| coverage_reported | invariant | `a composition verdict reports the share of bindings verified per tier; bindings to uncontracted providers are Unknown` | [[wild.compose]] |
| verdict_is_meet | invariant | `assembly structural assurance is the meet of binding assurance; required law, evidence, and attestation policy is evaluated for every binding; empty assemblies have PassDeclared assurance and vacuous coverage` | [[wild.compose]] |
| composition_is_category | invariant | `compose is disjoint union of component instances and bindings with matching exposed interfaces; it is defined only when bindings, singleton constraints, and relations pass; empty assembly is identity and associativity holds where both sides are defined` | [[wild.compose]] |

## Model

### States

- `demanded`
- `resolved`
- `certified`
- `verified`
- `unbridged`
- `refused`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| resolve | demanded | resolved | [[wild.compose.resolution_by_lineage]] ∧ [[wild.compose.resolver_deterministic]] |
| certify | resolved | certified | [[wild.compose.certificate_lists_bindings]] |
| verify | certified | verified | [[wild.compose.certificate_complete]] ∧ [[wild.compose.verifier_reads_only_certificate]] |
| flag_boundary | resolved | unbridged | [[wild.compose.boundary_needs_adapter]] |
| bridge | unbridged | certified | [[wild.compose.certificate_lists_bindings]] ∧ requires a wild-bridge `adapter_is_morphism` |
| refuse_unbound | resolved | refused | [[wild.compose.required_slots_bound]] |
| refuse_invalid | certified | refused | [[wild.compose.binding_well_formed]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| assembly_lists_every_binding | unit | [[wild.compose.assembly_is_bindings]] | `arbitrary_assembly()` | `bindings cover all required slots` |
| open_provider_needs_open_consumer | unit | [[wild.compose.binding_well_formed]] | `open_provider_sum_bound_to_closed_consumer()` | `well_formed == false` |
| unbound_required_slot_rejected | unit | [[wild.compose.required_slots_bound]] | `assembly_with_one_unbound_required_input()` | `well_formed == false` |
| accretion_substitution_sound | unit | [[wild.compose.substitution_preserves_assembly]] | `well_formed_assembly_and_accepted_accretion()` | `well_formed(after) == true` |
| scoped_substitution_sound | unit | [[wild.compose.scoped_substitution]] | `assembly_and_change_accreting_on_used_slots()` | `well_formed(after) == true` |
| resolution_is_chain_max | unit | [[wild.compose.resolution_by_lineage]] | `finite_snapshot_with_unique_tips_and_demand()` | `selection == accepted tips ∧ backtracking_nodes == 0 or refusal lists violated constraints` |
| resolution_reproducible | unit | [[wild.compose.resolver_deterministic]] | `same_snapshot_resolved_twice()` | `selection(a) == selection(b) ∧ cert(a) == cert(b)` |
| copies_are_listed | unit | [[wild.compose.lineage_copies_listed]] | `consumers_on_two_lineages_of_one_package()` | `report lists both copies` |
| merge_is_a_proposal | unit | [[wild.compose.scoped_merge_proposed]] | `consumer_whose_demand_accretes_in_newer_lineage()` | `proposal listed ∧ selection unchanged` |
| unbridged_boundary_reported | unit | [[wild.compose.boundary_needs_adapter]] | `value_crossing_lineages_without_adapter()` | `status == unbridged` |
| second_lineage_of_singleton_fails | unit | [[wild.compose.singleton_declared]] | `singleton_resolved_under_two_lineages()` | `composition == failed` |
| timeout_relation_checked | unit | [[wild.compose.relation_slots]] | `backend_idle_timeout_below_balancer_timeout()` | `composition == failed` |
| certificate_names_all_fields | unit | [[wild.compose.certificate_lists_bindings]] | `arbitrary_certificate()` | `each binding has consumer ∧ provider ∧ demand` |
| missing_binding_rejected | unit | [[wild.compose.certificate_complete]] | `certificate_with_one_binding_dropped()` | `verify == rejected` |
| corruption_detected | unit | [[wild.compose.certificate_tamper_evident]] | `certificate_with_last_hash_digit_changed()` | `verify == rejected` |
| verifier_has_no_resolver_dependency | unit | [[wild.compose.verifier_reads_only_certificate]] | `verifier_module_dependency_graph()` | `no edge to resolver` |
| verification_cost_linear | unit | [[wild.compose.verification_linear]] | `certificates_of_size([100, 1000, 10000])` | `indexed visits ≤ k * (bindings + schema_nodes + proof_bytes) for recorded checker constant k` |
| uncontracted_binding_is_unknown | unit | [[wild.compose.coverage_reported]] | `assembly_with_one_uncontracted_provider()` | `binding.verdict == Unknown ∧ coverage lists it` |
| verdict_equals_meet | unit | [[wild.compose.verdict_is_meet]] | `bindings_with_mixed_verdicts()` | `assembly.assurance == meet(binding.assurance) ∧ policy checks each binding` |
| assembly_composition_laws | law | [[wild.compose.composition_is_category]] | `three_assemblies_with_jointly_compatible_interfaces()` | **identity:** `compose(empty, a) == a` **associativity:** `compose(compose(a, b), c) == compose(a, compose(b, c))` |

## Notes

Simulation evidence (toy model, assumed parameters): 30,000 random four-component assemblies, 10,215 accepted accretions, zero assemblies broken by substitution; 22% of changes rejected by the full check were harmless to the specific assembly, which is the case for `scoped_substitution`. In a synthetic ecosystem (30 packages, 8 versions each), lineage resolution broke zero dependencies and needed no search, while a single-version semver resolver found no solution in 16.5% to 99% of cases depending on break rate and mislabelling. With truthful labels, lineage resolution and semver-with-duplicates coincide, so the contribution is machine-checked labels. A verifier re-checked about 41 bindings per assembly in about 1 ms and rejected all 750 corrupted-hash and 750 dropped-binding certificates.

Known limits: the wiring rule was tightened after the first run found 21 unsound cases involving open sums; that is a model decision, recorded in `binding_well_formed`. Assemblies in the tests had four components and four names (small-scope).

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Assembly is bindings

The system SHALL satisfy `assembly_is_bindings` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Assembly lists every binding
- **GIVEN** the fixture domain `arbitrary_assembly()`
- **WHEN** the `assembly_is_bindings` check runs
- **THEN** `bindings cover all required slots`

### Rule: Binding well formed

The system SHALL satisfy `binding_well_formed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Open provider needs open consumer
- **GIVEN** the fixture domain `open_provider_sum_bound_to_closed_consumer()`
- **WHEN** the `binding_well_formed` check runs
- **THEN** `well_formed == false`

### Rule: Required slots bound

The system SHALL satisfy `required_slots_bound` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unbound required slot rejected
- **GIVEN** the fixture domain `assembly_with_one_unbound_required_input()`
- **WHEN** the `required_slots_bound` check runs
- **THEN** `well_formed == false`

### Rule: Substitution preserves assembly

The system SHALL satisfy `substitution_preserves_assembly` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Accretion substitution sound
- **GIVEN** the fixture domain `well_formed_assembly_and_accepted_accretion()`
- **WHEN** the `substitution_preserves_assembly` check runs
- **THEN** `well_formed(after) == true`

### Rule: Scoped substitution

The system SHALL satisfy `scoped_substitution` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Scoped substitution sound
- **GIVEN** the fixture domain `assembly_and_change_accreting_on_used_slots()`
- **WHEN** the `scoped_substitution` check runs
- **THEN** `well_formed(after) == true`

### Rule: Resolution by lineage

The system SHALL satisfy `resolution_by_lineage` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Resolution is chain max
- **GIVEN** the fixture domain `finite_snapshot_with_unique_tips_and_demand()`
- **WHEN** the `resolution_by_lineage` check runs
- **THEN** `selection == accepted tips ∧ backtracking_nodes == 0 or refusal lists violated constraints`

### Rule: Resolver deterministic

The system SHALL satisfy `resolver_deterministic` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Resolution reproducible
- **GIVEN** the fixture domain `same_snapshot_resolved_twice()`
- **WHEN** the `resolver_deterministic` check runs
- **THEN** `selection(a) == selection(b) ∧ cert(a) == cert(b)`

### Rule: Lineage copies listed

The system SHALL satisfy `lineage_copies_listed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Copies are listed
- **GIVEN** the fixture domain `consumers_on_two_lineages_of_one_package()`
- **WHEN** the `lineage_copies_listed` check runs
- **THEN** `report lists both copies`

### Rule: Scoped merge proposed

The system SHALL satisfy `scoped_merge_proposed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Merge is a proposal
- **GIVEN** the fixture domain `consumer_whose_demand_accretes_in_newer_lineage()`
- **WHEN** the `scoped_merge_proposed` check runs
- **THEN** `proposal listed ∧ selection unchanged`

### Rule: Boundary needs adapter

The system SHALL satisfy `boundary_needs_adapter` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unbridged boundary reported
- **GIVEN** the fixture domain `value_crossing_lineages_without_adapter()`
- **WHEN** the `boundary_needs_adapter` check runs
- **THEN** `status == unbridged`

### Rule: Singleton declared

The system SHALL satisfy `singleton_declared` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Second lineage of singleton fails
- **GIVEN** the fixture domain `singleton_resolved_under_two_lineages()`
- **WHEN** the `singleton_declared` check runs
- **THEN** `composition == failed`

### Rule: Relation slots

The system SHALL satisfy `relation_slots` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Timeout relation checked
- **GIVEN** the fixture domain `backend_idle_timeout_below_balancer_timeout()`
- **WHEN** the `relation_slots` check runs
- **THEN** `composition == failed`

### Rule: Certificate lists bindings

The system SHALL satisfy `certificate_lists_bindings` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Certificate names all fields
- **GIVEN** the fixture domain `arbitrary_certificate()`
- **WHEN** the `certificate_lists_bindings` check runs
- **THEN** `each binding has consumer ∧ provider ∧ demand`

### Rule: Certificate complete

The system SHALL satisfy `certificate_complete` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Missing binding rejected
- **GIVEN** the fixture domain `certificate_with_one_binding_dropped()`
- **WHEN** the `certificate_complete` check runs
- **THEN** `verify == rejected`

### Rule: Certificate tamper evident

The system SHALL satisfy `certificate_tamper_evident` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Corruption detected
- **GIVEN** the fixture domain `certificate_with_last_hash_digit_changed()`
- **WHEN** the `certificate_tamper_evident` check runs
- **THEN** `verify == rejected`

### Rule: Verifier reads only certificate

The system SHALL satisfy `verifier_reads_only_certificate` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verifier has no resolver dependency
- **GIVEN** the fixture domain `verifier_module_dependency_graph()`
- **WHEN** the `verifier_reads_only_certificate` check runs
- **THEN** `no edge to resolver`

### Rule: Verification linear

The system SHALL satisfy `verification_linear` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verification cost linear
- **GIVEN** the fixture domain `certificates_of_size([100, 1000, 10000])`
- **WHEN** the `verification_linear` check runs
- **THEN** `indexed visits ≤ k * (bindings + schema_nodes + proof_bytes) for recorded checker constant k`

### Rule: Coverage reported

The system SHALL satisfy `coverage_reported` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Uncontracted binding is unknown
- **GIVEN** the fixture domain `assembly_with_one_uncontracted_provider()`
- **WHEN** the `coverage_reported` check runs
- **THEN** `binding.verdict == Unknown ∧ coverage lists it`

### Rule: Verdict is meet

The system SHALL satisfy `verdict_is_meet` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verdict equals meet
- **GIVEN** the fixture domain `bindings_with_mixed_verdicts()`
- **WHEN** the `verdict_is_meet` check runs
- **THEN** `assembly.assurance == meet(binding.assurance) ∧ policy checks each binding`

### Rule: Composition is category

The system SHALL satisfy `composition_is_category` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Assembly composition laws
- **GIVEN** the fixture domain `three_assemblies_with_jointly_compatible_interfaces()`
- **WHEN** the `composition_is_category` check runs
- **THEN** **identity:** `compose(empty, a) == a` **associativity:** `compose(compose(a, b), c) == compose(a, compose(b, c))`

#### Acceptance case: Scoped change adds an unbound dependency
- **GIVEN** the replacement preserves demanded output a and introduces required input b
- **WHEN** scoped substitution evaluates the replacement closure
- **THEN** it refuses when b has no compatible provider

#### Acceptance case: Deleting a root subtree changes the commitment
- **GIVEN** the caller supplies the expected assembly hash for roots a and b
- **WHEN** a certificate omits root b and its entire subtree
- **THEN** verification refuses the commitment mismatch before evaluating bindings

#### Acceptance case: Missing proof cannot establish law assurance
- **GIVEN** a policy requires a law result whose implementation blob is absent
- **WHEN** offline verification evaluates the bundle
- **THEN** it reports Unknown or inconclusive and refuses that policy, without network access

#### Acceptance case: Empty assembly coverage is vacuous
- **GIVEN** an assembly has no roots, components, or bindings
- **WHEN** composition runs
- **THEN** assurance is PassDeclared; coverage is 0/0 with null ratio

#### Acceptance case: Unmerged forks do not have a newest revision
- **GIVEN** two accepted fork tips are incomparable
- **WHEN** lineage lookup runs
- **THEN** it refuses with both tip hashes until an explicit accretive merge is recorded

#### Acceptance case: Relation failure does not trigger hidden search
- **GIVEN** the accepted tips violate a declared timeout relation but older revisions would pass
- **WHEN** resolution completes closure and checks relations
- **THEN** it refuses with the relation id; no older candidate is selected

## Requirements

### Requirement: Wild compose design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild compose design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation
