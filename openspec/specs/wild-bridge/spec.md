---
id: spec
kind: intent
statement: THE wild bridge SHALL connect incompatible lineages through checked adapters and SHALL describe uncontracted third-party software through labelled overlays, without raising its verdict above what was evidenced.
---

# Wild bridge

Where accretion ends, adapters begin. A break ships as a new lineage plus an adapter back to the old one; adapters are morphisms that compose, declare what they lose, and pass round-trip laws. Third-party software without contracts is handled by overlays, tests-as-laws, and legacy version claims recorded at the weakest tier.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| break_requires_adapter | invariant | `a new lineage L' derived from L is published only with a registered adapter L → L'` | [[spec]] |
| adapter_is_morphism | invariant | `adapters have identities and compose associatively` | [[spec]] |
| adapter_composition_coherent | invariant | `a composed adapter equals the direct adapter when one is registered; a mismatch is reported` | [[spec]] |
| adapter_loss_declared | invariant | `every adapter declares lossless or lists the slots it loses` | [[spec]] |
| adapter_round_trip_law | invariant | `a declared-lossless adapter has a round-trip law that passes on recorded samples` | [[spec]] |
| unknown_fields_preserved | invariant | `read-modify-write through any adapter or generated client preserves slots outside its demand` | [[spec]] |
| adapter_draft_generated | invariant | `adapt(old, new) emits a draft covering every derivable mapping and a TODO for each slot it cannot derive` | [[spec]] |
| adapter_validated_on_samples | invariant | `a draft adapter is publishable only after its laws pass on recorded samples` | [[spec]] |
| adapter_forms_closed | invariant | `adapter form ∈ {facade_library, wire_proxy, data_upcaster, component_wrapper}; new forms only under a new Revision` | [[spec]] |
| opt_in_cross_lineage | invariant | `a consumer whose demand accretes in a newer lineage may adopt it without an adapter; adoption is opt-in per consumer` | [[spec]] |
| overlay_contracts | invariant | `a consumer may publish an overlay contract for an uncontracted upstream, bound to the upstream's artifact digest and labelled inferred` | [[spec]] |
| inferred_is_conservative | invariant | `contracts inferred from traffic or probes mark unobserved slots opaque and reach tier Observed at most` | [[spec]] |
| legacy_semver_as_attestation | invariant | `where a dependency has no contract, its declared version bump is recorded at the attestation tier and never above` | [[spec]] |
| tests_are_default_laws | invariant | `for an uncontracted upstream, the dependent's passing integration tests are recorded as laws of the dependent` | [[spec]] |
| uncontracted_edges_unknown | invariant | `an edge to an uncontracted provider is Unknown unless an overlay or a law covers the demanded slots` | [[spec]] |
| standards_are_lineages | invariant | `revisions of protocols and schemas published by standards bodies are lineages and are checked by the same accretion relation` | [[spec]] |

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
| draft_adapter | break_found | adapter_drafted | [[spec.adapter_draft_generated]] |
| validate | adapter_drafted | adapter_validated | [[spec.adapter_validated_on_samples]] ∧ [[spec.adapter_round_trip_law]] |
| publish_adapter | adapter_validated | adapter_published | [[spec.adapter_loss_declared]] ∧ [[spec.adapter_forms_closed]] |
| migrate | adapter_published | consumer_migrated | [[spec.opt_in_cross_lineage]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| break_without_adapter_rejected | unit | [[spec.break_requires_adapter]] | `new_lineage_without_registered_adapter()` | `publish == rejected` |
| adapter_category_laws | law | [[spec.adapter_is_morphism]] | `arbitrary_adapter_chain(length: 3)` | **identity:** `compose(id, a) == a` **associativity:** `compose(compose(a, b), c) == compose(a, compose(b, c))` |
| composed_matches_direct | unit | [[spec.adapter_composition_coherent]] | `adapters_a_b_and_direct_ab_disagreeing()` | `check == failed ∧ mismatch reported` |
| lossy_adapter_must_list_loss | unit | [[spec.adapter_loss_declared]] | `adapter_with_dropped_slot_declared_lossless()` | `check == failed` |
| lossless_needs_round_trip | unit | [[spec.adapter_round_trip_law]] | `lossless_adapter_failing_round_trip()` | `validate == failed` |
| round_trip_keeps_unknown_slots | unit | [[spec.unknown_fields_preserved]] | `record_with_slots_outside_demand()` | `read_modify_write(r) ⊇ unknown_slots(r)` |
| draft_marks_underivable_slots | unit | [[spec.adapter_draft_generated]] | `contract_pair_with_one_unmappable_slot()` | `draft has exactly one TODO` |
| unvalidated_adapter_unpublishable | unit | [[spec.adapter_validated_on_samples]] | `draft_adapter_failing_laws()` | `publish_adapter == rejected` |
| unknown_adapter_form_rejected | unit | [[spec.adapter_forms_closed]] | `adapter_declaring_form("magic")` | `check == failed` |
| unaffected_consumer_adopts_unaided | unit | [[spec.opt_in_cross_lineage]] | `break_in_slot_a_consumer_never_uses()` | `consumer_can_adopt == true ∧ adoption requires consent` |
| overlay_is_labelled_inferred | unit | [[spec.overlay_contracts]] | `overlay_for_uncontracted_upstream()` | `overlay.label == inferred ∧ overlay.digest == upstream.digest` |
| unobserved_slots_are_opaque | unit | [[spec.inferred_is_conservative]] | `traffic_covering_half_of_the_api()` | `unobserved slots are opaque ∧ tier ≤ Observed` |
| semver_never_above_attestation | unit | [[spec.legacy_semver_as_attestation]] | `dependency_without_contract_declaring_patch()` | `tier(dep) == attestation` |
| tests_become_laws | unit | [[spec.tests_are_default_laws]] | `dependent_with_passing_integration_test_on_uncontracted_upstream()` | `dependent.laws includes the test` |
| uncovered_edge_is_unknown | unit | [[spec.uncontracted_edges_unknown]] | `edge_to_uncontracted_provider_without_overlay_or_law()` | `edge.verdict == Unknown` |
| spec_revision_checked_like_package | unit | [[spec.standards_are_lineages]] | `protocol_revision_that_removes_a_feature_added_in_the_prior_revision()` | `accretes == false` |

## Notes

Evidence behind this spec: simulation round 1 showed that a dependent with an integration law catches a mislabelled change in an uncontracted upstream, and one without such a law does not (hence `tests_are_default_laws`); consumers who never used a removed slot could adopt the new lineage unaided (hence `opt_in_cross_lineage`). Catalog cases: PodSecurityPolicy replacement and ISO 20022 translation (lossy adapters), unknown-field dropping on read-modify-write, and a protocol spec that removed a feature added one revision earlier.

Known limits: overlays and inferred contracts are only as good as their evidence; adapters between genuinely incompatible models (AngularJS to Angular) may be infeasible, in which case the break stays unbridged and is reported.
