---
id: spec
kind: intent
statement: THE wild core SHALL represent each software contract as a content-addressed set of typed slots and decide accretion between revisions as a category with checkable laws.
---

# Wild core

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

The Contract IR and the accretion relation. A contract has slots with polarity (out provides, in requires), openness, limits, defaults, laws, and facets. Revision `v'` accretes `v` when provides grow and requires shrink. Accretions form a thin category (a preorder); restricting to a consumer's demand is a functor. A non-accretion must start a new lineage.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| identity_content_addressed | invariant | `revision.id == hash(canonical(contract)); equal ids imply identical contracts` | [[spec]] |
| canonical_form_stable | invariant | `canonical(c) is independent of slot order, whitespace, extractor, host, and clock` | [[spec]] |
| hash_algorithm_in_identity | invariant | `an identity names its hash algorithm; identities under different algorithms are never equal` | [[spec]] |
| lineage_name_versionless | invariant | `lineage.name is namespaced, non-empty, and has no version component` | [[spec]] |
| name_meaning_immutable | invariant | `within a lineage, slot name, facet, polarity, and semantic meaning are immutable; types may evolve only by the variance rules in docs/wild-formats-v1.md; law definitions are immutable and law sets only grow` | [[spec]] |
| slot_shapes_closed | invariant | `v1 slot shape ∈ {scalar, record, sum, sequence, map, function, opaque}; adding a shape requires a new IR schema version, not merely a new contract hash` | [[spec]] |
| accretion_monotone | invariant | `accretes(v, v') iff every old output remains with a subtype, each retained input accepts a supertype, no new required input appears, tombstones persist, and defaults, limits, laws, and facets satisfy docs/wild-formats-v1.md` | [[spec]] |
| polarity_openness_declared | invariant | `every record and sum declares open or closed (default closed); a closed output sum growing, opening, or becoming unrestricted is a break; an input sum growing is an accretion; an input sum losing tolerance is a break` | [[spec]] |
| limits_are_slots | invariant | `declared limits (size, cardinality, timeout) are slots; tightening a provided limit or loosening a required limit is a break` | [[spec]] |
| defaults_are_slots | invariant | `defaults and environment assumptions are slots; a changed provided default is a break` | [[spec]] |
| opaque_is_frozen | invariant | `any change to an opaque slot is a break` | [[spec]] |
| facets_independent | invariant | `compat(v, v') is the conjunction over facets of compat_facet(v, v'); facets ∈ {api, abi, layout, serialization, behavior, dialect, environment, license}; adding a facet kind requires a new IR schema version` | [[spec]] |
| data_artifacts_have_contracts | invariant | `content files, templates, and generated feature files consumed by code carry a contract checked like an API, including arity and size limits` | [[spec]] |
| tombstones_preserve_names | invariant | `a dropped requires leaves a tombstone; re-adding the name must accrete the tombstoned slot` | [[spec]] |
| accretion_is_category | invariant | `accretions have identities and compose; composing accretions yields an accretion; the relation is reflexive and transitive` | [[spec]] |
| check_against_ancestors | invariant | `a candidate revision is checked against every ancestor in its lineage, not only its predecessor` | [[spec]] |
| demand_restriction_functorial | invariant | `restricting a contract to a demand set preserves accretion and composes: restrict(restrict(c, D1), D2) == restrict(c, D1 ∩ D2)` | [[spec]] |
| break_requires_new_lineage | invariant | `a non-accretion may be published only under a new lineage name` | [[spec]] |
| stability_tiers | invariant | `lineage stability ∈ {stable, experimental, deprecated}; only experimental lineages may be retracted` | [[spec]] |
| sunset_computable | invariant | `a contract with a sunset schedule exposes the earliest date at which its provides shrink, queryable before that date` | [[spec]] |
| fork_merge_pushout | invariant | `a merge is published only if its contract accretes every branch ancestor and has no conflicting meaning, default, limit, or law definition; unresolved conflicts list names and are refused; an unmerged fork has no implicit newest revision` | [[spec]] |

## Model

### States

- `drafted`
- `canonical`
- `identified`
- `accretive`
- `lineage_break`
- `rejected`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| canonicalize | drafted | canonical | [[spec.canonical_form_stable]] |
| identify | canonical | identified | [[spec.identity_content_addressed]] ∧ [[spec.hash_algorithm_in_identity]] |
| accrete | identified | accretive | [[spec.accretion_monotone]] ∧ [[spec.check_against_ancestors]] |
| break | identified | lineage_break | [[spec.break_requires_new_lineage]] |
| reject | identified | rejected | violation of [[spec.name_meaning_immutable]] or invalid v1 IR |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| hash_matches_content | unit | [[spec.identity_content_addressed]] | `arbitrary_contract()` | `id(c) == hash(canonical(c))` |
| canonical_is_order_independent | unit | [[spec.canonical_form_stable]] | `arbitrary_contract(), permutation_of_slots()` | `canonical(c) == canonical(permute(c))` |
| algorithms_never_collide | unit | [[spec.hash_algorithm_in_identity]] | `same_bytes_hashed_with_two_algorithms()` | `id_a != id_b` |
| versioned_lineage_name_rejected | unit | [[spec.lineage_name_versionless]] | `lineage_name_with_version_suffix("acme.billing.v2")` | `check(name) == failed` |
| redefined_meaning_rejected | unit | [[spec.name_meaning_immutable]] | `(r, r')` with a changed slot meaning or a narrowed input type | `check(r, r') == failed; variance-safe type refinement with unchanged meaning passes` |
| unknown_shape_rejected | unit | [[spec.slot_shapes_closed]] | `slot_with_shape("tensor")` | `check(slot) == failed` |
| removed_provide_is_break | unit | [[spec.accretion_monotone]] | `contract_pair_with(provide_removed: true)` | `accretes(v, v') == false` |
| closed_output_growth_is_break | unit | [[spec.polarity_openness_declared]] | `closed_output_sum_with_added_variant()` | `accretes == false`; the same addition in input position yields true |
| tightened_limit_is_break | unit | [[spec.limits_are_slots]] | `provided_limit_lowered(500 → 200)` | `accretes == false` |
| changed_default_is_break | unit | [[spec.defaults_are_slots]] | `provided_default_changed(30 → 5)` | `accretes == false` |
| opaque_change_is_break | unit | [[spec.opaque_is_frozen]] | `opaque_slot_with_changed_content()` | `accretes == false` |
| facet_break_blocks_compat | unit | [[spec.facets_independent]] | `pair_with_break_in_exactly_one_facet()` | `compat == failed` |
| feature_file_arity_checked | unit | [[spec.data_artifacts_have_contracts]] | `template_defining_21_fields_fed_20_inputs()` | `check == failed` |
| tombstone_blocks_name_reuse | unit | [[spec.tombstones_preserve_names]] | `drop_then_readd_input_with_narrower_type()` | `check(readd) == failed` |
| accretion_category_laws | law | [[spec.accretion_is_category]] | `arbitrary_contract_chain(length: 3)` | **identity:** `accretes(v, v)` and `compose(id, f) == f` **associativity:** `compose(compose(f, g), h) == compose(f, compose(g, h))` |
| skipped_ancestor_break_caught | unit | [[spec.check_against_ancestors]] | `chain_v1_v2_v3_where_v3_breaks_v1_only()` | `check(v3) == failed` |
| restriction_functor_laws | law | [[spec.demand_restriction_functorial]] | `arbitrary_contract(), two_demand_sets()` | **identity:** `restrict(c, all_slots) == c` **associativity:** `restrict(restrict(c, D1), D2) == restrict(c, D1 ∩ D2)` |
| break_in_lineage_rejected | unit | [[spec.break_requires_new_lineage]] | `breaking_revision_under_same_lineage()` | `publish == rejected` |
| retracting_stable_rejected | unit | [[spec.stability_tiers]] | `retract_request_on_stable_lineage()` | `retract == rejected` |
| scheduled_shrink_reported | unit | [[spec.sunset_computable]] | `contract_with_sunset(date: d)` | `earliest_break(c) == d` |
| colliding_merge_refused | unit | [[spec.fork_merge_pushout]] | `two_forks_defining_same_name_differently()` | `merge == refused ∧ colliding names listed` |

## Notes

Exhaustive small-scope testing (76 single-slot states, 438,976 triples) found four rule gaps in an early checker: optional inputs becoming required, open/closed flips, unrestricted versus restricted sums, and dropped names returning with a new meaning. They are encoded above as `polarity_openness_declared` and `tombstones_preserve_names`. The relation is a conjunction over names, so the single-name result extends to many slots by construction; this was argued, not tested.

The category is thin (at most one morphism between two revisions), so associativity and identity hold structurally; the properties guard the implementation, not the mathematics.

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Identity content addressed

The system SHALL satisfy `identity_content_addressed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Hash matches content
- **GIVEN** the fixture domain `arbitrary_contract()`
- **WHEN** the `identity_content_addressed` check runs
- **THEN** `id(c) == hash(canonical(c))`

### Rule: Canonical form stable

The system SHALL satisfy `canonical_form_stable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Canonical is order independent
- **GIVEN** the fixture domain `arbitrary_contract(), permutation_of_slots()`
- **WHEN** the `canonical_form_stable` check runs
- **THEN** `canonical(c) == canonical(permute(c))`

### Rule: Hash algorithm in identity

The system SHALL satisfy `hash_algorithm_in_identity` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Algorithms never collide
- **GIVEN** the fixture domain `same_bytes_hashed_with_two_algorithms()`
- **WHEN** the `hash_algorithm_in_identity` check runs
- **THEN** `id_a != id_b`

### Rule: Lineage name versionless

The system SHALL satisfy `lineage_name_versionless` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Versioned lineage name rejected
- **GIVEN** the fixture domain `lineage_name_with_version_suffix("acme.billing.v2")`
- **WHEN** the `lineage_name_versionless` check runs
- **THEN** `check(name) == failed`

### Rule: Name meaning immutable

The system SHALL satisfy `name_meaning_immutable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Redefined meaning rejected
- **GIVEN** the fixture domain `(r, r')` with a changed slot meaning or a narrowed input type
- **WHEN** the `name_meaning_immutable` check runs
- **THEN** `check(r, r') == failed; variance-safe type refinement with unchanged meaning passes`

### Rule: Slot shapes closed

The system SHALL satisfy `slot_shapes_closed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unknown shape rejected
- **GIVEN** the fixture domain `slot_with_shape("tensor")`
- **WHEN** the `slot_shapes_closed` check runs
- **THEN** `check(slot) == failed`

### Rule: Accretion monotone

The system SHALL satisfy `accretion_monotone` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Removed provide is break
- **GIVEN** the fixture domain `contract_pair_with(provide_removed: true)`
- **WHEN** the `accretion_monotone` check runs
- **THEN** `accretes(v, v') == false`

### Rule: Polarity openness declared

The system SHALL satisfy `polarity_openness_declared` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Closed output growth is break
- **GIVEN** the fixture domain `closed_output_sum_with_added_variant()`
- **WHEN** the `polarity_openness_declared` check runs
- **THEN** `accretes == false`; the same addition in input position yields true

### Rule: Limits are slots

The system SHALL satisfy `limits_are_slots` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Tightened limit is break
- **GIVEN** the fixture domain `provided_limit_lowered(500 → 200)`
- **WHEN** the `limits_are_slots` check runs
- **THEN** `accretes == false`

### Rule: Defaults are slots

The system SHALL satisfy `defaults_are_slots` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Changed default is break
- **GIVEN** the fixture domain `provided_default_changed(30 → 5)`
- **WHEN** the `defaults_are_slots` check runs
- **THEN** `accretes == false`

### Rule: Opaque is frozen

The system SHALL satisfy `opaque_is_frozen` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Opaque change is break
- **GIVEN** the fixture domain `opaque_slot_with_changed_content()`
- **WHEN** the `opaque_is_frozen` check runs
- **THEN** `accretes == false`

### Rule: Facets independent

The system SHALL satisfy `facets_independent` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Facet break blocks compat
- **GIVEN** the fixture domain `pair_with_break_in_exactly_one_facet()`
- **WHEN** the `facets_independent` check runs
- **THEN** `compat == failed`

### Rule: Data artifacts have contracts

The system SHALL satisfy `data_artifacts_have_contracts` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Feature file arity checked
- **GIVEN** the fixture domain `template_defining_21_fields_fed_20_inputs()`
- **WHEN** the `data_artifacts_have_contracts` check runs
- **THEN** `check == failed`

### Rule: Tombstones preserve names

The system SHALL satisfy `tombstones_preserve_names` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Tombstone blocks name reuse
- **GIVEN** the fixture domain `drop_then_readd_input_with_narrower_type()`
- **WHEN** the `tombstones_preserve_names` check runs
- **THEN** `check(readd) == failed`

### Rule: Accretion is category

The system SHALL satisfy `accretion_is_category` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Accretion category laws
- **GIVEN** the fixture domain `arbitrary_contract_chain(length: 3)`
- **WHEN** the `accretion_is_category` check runs
- **THEN** **identity:** `accretes(v, v)` and `compose(id, f) == f` **associativity:** `compose(compose(f, g), h) == compose(f, compose(g, h))`

### Rule: Check against ancestors

The system SHALL satisfy `check_against_ancestors` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Skipped ancestor break caught
- **GIVEN** the fixture domain `chain_v1_v2_v3_where_v3_breaks_v1_only()`
- **WHEN** the `check_against_ancestors` check runs
- **THEN** `check(v3) == failed`

### Rule: Demand restriction functorial

The system SHALL satisfy `demand_restriction_functorial` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Restriction functor laws
- **GIVEN** the fixture domain `arbitrary_contract(), two_demand_sets()`
- **WHEN** the `demand_restriction_functorial` check runs
- **THEN** **identity:** `restrict(c, all_slots) == c` **associativity:** `restrict(restrict(c, D1), D2) == restrict(c, D1 ∩ D2)`

### Rule: Break requires new lineage

The system SHALL satisfy `break_requires_new_lineage` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Break in lineage rejected
- **GIVEN** the fixture domain `breaking_revision_under_same_lineage()`
- **WHEN** the `break_requires_new_lineage` check runs
- **THEN** `publish == rejected`

### Rule: Stability tiers

The system SHALL satisfy `stability_tiers` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Retracting stable rejected
- **GIVEN** the fixture domain `retract_request_on_stable_lineage()`
- **WHEN** the `stability_tiers` check runs
- **THEN** `retract == rejected`

### Rule: Sunset computable

The system SHALL satisfy `sunset_computable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Scheduled shrink reported
- **GIVEN** the fixture domain `contract_with_sunset(date: d)`
- **WHEN** the `sunset_computable` check runs
- **THEN** `earliest_break(c) == d`

### Rule: Fork merge pushout

The system SHALL satisfy `fork_merge_pushout` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Colliding merge refused
- **GIVEN** the fixture domain `two_forks_defining_same_name_differently()`
- **WHEN** the `fork_merge_pushout` check runs
- **THEN** `merge == refused ∧ colliding names listed`

#### Acceptance case: Canonical identity rejects ambiguous JSON
- **GIVEN** a contract JSON document with a duplicate object key or floating-point value
- **WHEN** canonicalization runs
- **THEN** the input is refused before hashing; permuted valid slot arrays yield identical bytes

#### Acceptance case: Variance preserves semantic identity
- **GIVEN** an input integer slot changes from interval [0,10] to [0,20] with unchanged meaning
- **WHEN** accretion is checked
- **THEN** the refinement passes; changing meaning or narrowing to [0,5] rejects

#### Acceptance case: Tombstone reactivation cannot introduce a requirement
- **GIVEN** a previously removed input is present only as a tombstone
- **WHEN** the candidate reintroduces it as required
- **THEN** accretion rejects even when its type accepts the old domain

## Requirements

### Requirement: Prototype accretion pipeline

The prototype tier pipeline SHALL run the round-1 accretion scenarios end to end and emit a machine-readable verdict record per scenario, so declared round-1 outcomes remain executable while `wild` itself is unbuilt; the prototype uses a smaller type model and does not establish full v1 conformance.

#### Scenario: Prototype accretion pipeline reports round-1 verdicts
- **GIVEN** the round-1 scenario fixtures encoded in `prototype/wild_sim.py`
- **WHEN** the prototype simulation runs
- **THEN** it exits 0 and emits a JSON array of verdict records, each carrying an `id` and a decision `trace` matching the declared expected terminal state
- **AND** known undeclared-behavior escapes remain reported rather than being silently converted to passing safety claims
- **AND** the gate executes this behavior as a declared contract test

### Requirement: Wild core design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild core design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation
