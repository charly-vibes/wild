---
id: wild.bridge
kind: intent
statement: THE wild bridge SHALL connect incompatible lineages through checked adapters and SHALL describe uncontracted third-party software through labelled overlays, without raising its verdict above what was evidenced.
---

# Wild bridge

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

Where accretion ends, adapters begin. A break ships as a new lineage plus an explicitly directed adapter when one can be built; adapters are morphisms that compose, declare what they lose, and pass round-trip laws. Third-party software without contracts is handled by overlays, tests-as-laws, and legacy version claims recorded at the weakest tier.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| break_requires_adapter | invariant | `a new lineage derived from an old one declares either registered directed adapters or unbridged status with a reason; publication of an unbridged lineage is allowed, but demanded cross-lineage boundaries without adapters refuse composition` | [[wild.bridge]] |
| adapter_is_morphism | invariant | `an adapter names source and target revision hashes and its artifact digest; A → B followed by B → C composes to A → C; identity and associativity hold for the declared mappings and observable equivalence` | [[wild.bridge]] |
| adapter_composition_coherent | invariant | `a composed adapter and any direct adapter must agree on the recorded law-suite domain modulo declared loss; a counterexample refuses coherence, and sample agreement is labelled sampled rather than universal equality` | [[wild.bridge]] |
| adapter_loss_declared | invariant | `every adapter declares lossless or lists the slots it loses` | [[wild.bridge]] |
| adapter_round_trip_law | invariant | `a lossless adapter declares a reverse adapter and round-trip equality on its declared domain in both directions; validation labels proof, exhaustive, or sampled coverage and never promotes samples to universal losslessness` | [[wild.bridge]] |
| unknown_fields_preserved | invariant | `read-modify-write preserves unknown slots as opaque payloads except losses explicitly enumerated in a lossy adapter; a consumer requiring any declared lost slot refuses that adapter` | [[wild.bridge]] |
| adapter_draft_generated | invariant | `adapt(old, new) emits a draft covering every derivable mapping and a TODO for each slot it cannot derive` | [[wild.bridge]] |
| adapter_validated_on_samples | invariant | `a draft adapter is publishable only when all mappings are resolved, losses and law method are declared, and its required validation suite passes; unresolved mappings are not publishable` | [[wild.bridge]] |
| adapter_forms_closed | invariant | `adapter form ∈ {facade_library, wire_proxy, data_upcaster, component_wrapper}; adding a form requires a new wire schema version` | [[wild.bridge]] |
| opt_in_cross_lineage | invariant | `a consumer whose demand accretes in a newer lineage may adopt it without an adapter; adoption is opt-in per consumer` | [[wild.bridge]] |
| overlay_contracts | invariant | `a consumer may publish an overlay contract for an uncontracted upstream, bound to the upstream's artifact digest and labelled inferred` | [[wild.bridge]] |
| inferred_is_conservative | invariant | `inferred contracts report the observed domain and do not claim a complete upstream schema; known unsupported constructs are opaque and absent observations remain Unknown; observations alone cannot establish PassDeclared structural assurance` | [[wild.bridge]] |
| legacy_semver_as_attestation | invariant | `a legacy version bump is an unverified metadata claim unless its publisher signs a scoped, expiring v1 attestation; it never establishes structural or law assurance` | [[wild.bridge]] |
| tests_are_default_laws | invariant | `for an uncontracted upstream, the dependent's passing integration tests are recorded as laws of the dependent` | [[wild.bridge]] |
| uncontracted_edges_unknown | invariant | `an uncontracted edge has Unknown structural assurance; a digest-bound explicit overlay may establish declared assurance for covered slots, while tests add only method-labelled law evidence for their exercised domain` | [[wild.bridge]] |
| standards_are_lineages | invariant | `revisions of protocols and schemas published by standards bodies are lineages and are checked by the same accretion relation` | [[wild.bridge]] |

## Model

### States

- `break_found`
- `adapter_drafted`
- `adapter_validated`
- `adapter_published`
- `consumer_migrated`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| draft_adapter | break_found | adapter_drafted | [[wild.bridge.adapter_draft_generated]] |
| validate | adapter_drafted | adapter_validated | [[wild.bridge.adapter_validated_on_samples]] ∧ [[wild.bridge.adapter_round_trip_law]] |
| publish_adapter | adapter_validated | adapter_published | [[wild.bridge.adapter_loss_declared]] ∧ [[wild.bridge.adapter_forms_closed]] |
| migrate | adapter_published | consumer_migrated | [[wild.bridge.opt_in_cross_lineage]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| break_without_adapter_disclosed | unit | [[wild.bridge.break_requires_adapter]] | `new_lineage_without_registered_adapter()` | `publish records unbridged ∧ cross_lineage_binding == refused` |
| adapter_category_laws | law | [[wild.bridge.adapter_is_morphism]] | `arbitrary_adapter_chain(length: 3)` | **identity:** `compose(id, a) == a` **associativity:** `compose(compose(a, b), c) == compose(a, compose(b, c))` |
| composed_matches_direct | unit | [[wild.bridge.adapter_composition_coherent]] | `adapters_a_b_and_direct_ab_disagreeing()` | `check == failed ∧ mismatch reported` |
| lossy_adapter_must_list_loss | unit | [[wild.bridge.adapter_loss_declared]] | `adapter_with_dropped_slot_declared_lossless()` | `check == failed` |
| lossless_needs_round_trip | unit | [[wild.bridge.adapter_round_trip_law]] | `lossless_adapter_failing_round_trip()` | `validate == failed` |
| round_trip_keeps_unknown_slots | unit | [[wild.bridge.unknown_fields_preserved]] | `record_with_slots_outside_demand()` | `unknown_slots(after) == unknown_slots(before) minus explicitly accepted declared losses` |
| draft_marks_underivable_slots | unit | [[wild.bridge.adapter_draft_generated]] | `contract_pair_with_one_unmappable_slot()` | `draft has exactly one TODO` |
| unvalidated_adapter_unpublishable | unit | [[wild.bridge.adapter_validated_on_samples]] | `draft_adapter_failing_laws()` | `publish_adapter == rejected` |
| unknown_adapter_form_rejected | unit | [[wild.bridge.adapter_forms_closed]] | `adapter_declaring_form("magic")` | `check == failed` |
| unaffected_consumer_adopts_unaided | unit | [[wild.bridge.opt_in_cross_lineage]] | `break_in_slot_a_consumer_never_uses()` | `consumer_can_adopt == true ∧ adoption requires consent` |
| overlay_is_labelled_inferred | unit | [[wild.bridge.overlay_contracts]] | `overlay_for_uncontracted_upstream()` | `overlay.label == inferred ∧ overlay.digest == upstream.digest` |
| unobserved_slots_are_opaque | unit | [[wild.bridge.inferred_is_conservative]] | `traffic_covering_half_of_the_api()` | `coverage names observed domain ∧ unobserved domain == Unknown` |
| semver_never_above_attestation | unit | [[wild.bridge.legacy_semver_as_attestation]] | `dependency_without_contract_declaring_patch()` | `claim.source == legacy_version ∧ structural_assurance == Unknown` |
| tests_become_laws | unit | [[wild.bridge.tests_are_default_laws]] | `dependent_with_passing_integration_test_on_uncontracted_upstream()` | `dependent.laws includes the test` |
| uncovered_edge_is_unknown | unit | [[wild.bridge.uncontracted_edges_unknown]] | `edge_to_uncontracted_provider_without_overlay_or_law()` | `edge.assurance == Unknown` |
| spec_revision_checked_like_package | unit | [[wild.bridge.standards_are_lineages]] | `protocol_revision_that_removes_a_feature_added_in_the_prior_revision()` | `accretes == false` |

## Notes

Evidence behind this spec: simulation round 1 showed that a dependent with an integration law catches a mislabelled change in an uncontracted upstream, and one without such a law does not (hence `tests_are_default_laws`); consumers who never used a removed slot could adopt the new lineage unaided (hence `opt_in_cross_lineage`). Catalog cases: PodSecurityPolicy replacement and ISO 20022 translation (lossy adapters), unknown-field dropping on read-modify-write, and a protocol spec that removed a feature added one revision earlier.

Known limits: overlays and inferred contracts are only as good as their evidence; adapters between genuinely incompatible models (AngularJS to Angular) may be infeasible, in which case the break stays unbridged and is reported.

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Break requires adapter

The system SHALL satisfy `break_requires_adapter` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Break without adapter disclosed
- **GIVEN** the fixture domain `new_lineage_without_registered_adapter()`
- **WHEN** the `break_requires_adapter` check runs
- **THEN** `publish records unbridged ∧ cross_lineage_binding == refused`

### Rule: Adapter is morphism

The system SHALL satisfy `adapter_is_morphism` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Adapter category laws
- **GIVEN** the fixture domain `arbitrary_adapter_chain(length: 3)`
- **WHEN** the `adapter_is_morphism` check runs
- **THEN** **identity:** `compose(id, a) == a` **associativity:** `compose(compose(a, b), c) == compose(a, compose(b, c))`

### Rule: Adapter composition coherent

The system SHALL satisfy `adapter_composition_coherent` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Composed matches direct
- **GIVEN** the fixture domain `adapters_a_b_and_direct_ab_disagreeing()`
- **WHEN** the `adapter_composition_coherent` check runs
- **THEN** `check == failed ∧ mismatch reported`

### Rule: Adapter loss declared

The system SHALL satisfy `adapter_loss_declared` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Lossy adapter must list loss
- **GIVEN** the fixture domain `adapter_with_dropped_slot_declared_lossless()`
- **WHEN** the `adapter_loss_declared` check runs
- **THEN** `check == failed`

### Rule: Adapter round trip law

The system SHALL satisfy `adapter_round_trip_law` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Lossless needs round trip
- **GIVEN** the fixture domain `lossless_adapter_failing_round_trip()`
- **WHEN** the `adapter_round_trip_law` check runs
- **THEN** `validate == failed`

### Rule: Unknown fields preserved

The system SHALL satisfy `unknown_fields_preserved` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Round trip keeps unknown slots
- **GIVEN** the fixture domain `record_with_slots_outside_demand()`
- **WHEN** the `unknown_fields_preserved` check runs
- **THEN** `unknown_slots(after) == unknown_slots(before) minus explicitly accepted declared losses`

### Rule: Adapter draft generated

The system SHALL satisfy `adapter_draft_generated` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Draft marks underivable slots
- **GIVEN** the fixture domain `contract_pair_with_one_unmappable_slot()`
- **WHEN** the `adapter_draft_generated` check runs
- **THEN** `draft has exactly one TODO`

### Rule: Adapter validated on samples

The system SHALL satisfy `adapter_validated_on_samples` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unvalidated adapter unpublishable
- **GIVEN** the fixture domain `draft_adapter_failing_laws()`
- **WHEN** the `adapter_validated_on_samples` check runs
- **THEN** `publish_adapter == rejected`

### Rule: Adapter forms closed

The system SHALL satisfy `adapter_forms_closed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unknown adapter form rejected
- **GIVEN** the fixture domain `adapter_declaring_form("magic")`
- **WHEN** the `adapter_forms_closed` check runs
- **THEN** `check == failed`

### Rule: Opt in cross lineage

The system SHALL satisfy `opt_in_cross_lineage` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unaffected consumer adopts unaided
- **GIVEN** the fixture domain `break_in_slot_a_consumer_never_uses()`
- **WHEN** the `opt_in_cross_lineage` check runs
- **THEN** `consumer_can_adopt == true ∧ adoption requires consent`

### Rule: Overlay contracts

The system SHALL satisfy `overlay_contracts` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Overlay is labelled inferred
- **GIVEN** the fixture domain `overlay_for_uncontracted_upstream()`
- **WHEN** the `overlay_contracts` check runs
- **THEN** `overlay.label == inferred ∧ overlay.digest == upstream.digest`

### Rule: Inferred is conservative

The system SHALL satisfy `inferred_is_conservative` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unobserved slots are opaque
- **GIVEN** the fixture domain `traffic_covering_half_of_the_api()`
- **WHEN** the `inferred_is_conservative` check runs
- **THEN** `coverage names observed domain ∧ unobserved domain == Unknown`

### Rule: Legacy semver as attestation

The system SHALL satisfy `legacy_semver_as_attestation` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Semver never above attestation
- **GIVEN** the fixture domain `dependency_without_contract_declaring_patch()`
- **WHEN** the `legacy_semver_as_attestation` check runs
- **THEN** `claim.source == legacy_version ∧ structural_assurance == Unknown`

### Rule: Tests are default laws

The system SHALL satisfy `tests_are_default_laws` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Tests become laws
- **GIVEN** the fixture domain `dependent_with_passing_integration_test_on_uncontracted_upstream()`
- **WHEN** the `tests_are_default_laws` check runs
- **THEN** `dependent.laws includes the test`

### Rule: Uncontracted edges unknown

The system SHALL satisfy `uncontracted_edges_unknown` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Uncovered edge is unknown
- **GIVEN** the fixture domain `edge_to_uncontracted_provider_without_overlay_or_law()`
- **WHEN** the `uncontracted_edges_unknown` check runs
- **THEN** `edge.assurance == Unknown`

### Rule: Standards are lineages

The system SHALL satisfy `standards_are_lineages` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Spec revision checked like package
- **GIVEN** the fixture domain `protocol_revision_that_removes_a_feature_added_in_the_prior_revision()`
- **WHEN** the `standards_are_lineages` check runs
- **THEN** `accretes == false`

#### Acceptance case: Infeasible adapter leaves a disclosed boundary
- **GIVEN** a new lineage cannot be adapted to its predecessor
- **WHEN** it is published with unbridged status and reason
- **THEN** publication succeeds but composition across the unbridged demanded boundary refuses

#### Acceptance case: Lossless requires both directions
- **GIVEN** an A to B adapter has no reverse mapping
- **WHEN** it claims lossless round-trip validation
- **THEN** validation refuses the incomplete claim

#### Acceptance case: Declared loss affects consumer selection
- **GIVEN** an adapter loses slot x and preserves unknown slot y
- **WHEN** a consumer demands x
- **THEN** composition refuses that adapter; consumers accepting declared loss retain y through read-modify-write

## Requirements

### Requirement: Wild bridge design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild bridge design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation
