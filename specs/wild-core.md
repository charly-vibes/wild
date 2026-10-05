---
id: wild.core
kind: intent
statement: THE wild core SHALL represent each software contract as a content-addressed set of typed slots and decide accretion between revisions as a category with checkable laws.
---

# Wild core

The Contract IR and the accretion relation. A contract has slots with polarity (out provides, in requires), openness, limits, defaults, laws, and facets. Revision `v'` accretes `v` when provides grow and requires shrink. Accretions form a thin category (a preorder); restricting to a consumer's demand is a functor. A non-accretion must start a new lineage.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| identity_content_addressed | invariant | `revision.id == hash(canonical(contract)); equal ids imply identical contracts` | [[wild.core]] |
| canonical_form_stable | invariant | `canonical(c) is independent of slot order, whitespace, extractor, host, and clock` | [[wild.core]] |
| hash_algorithm_in_identity | invariant | `an identity names its hash algorithm; identities under different algorithms are never equal` | [[wild.core]] |
| lineage_name_versionless | invariant | `lineage.name is namespaced, non-empty, and has no version component` | [[wild.core]] |
| name_meaning_immutable | invariant | `for a slot name n and revisions r < r' of one lineage: type(n, r) == type(n, r') and laws(n, r) ⊆ laws(n, r')` | [[wild.core]] |
| slot_shapes_closed | invariant | `slot shape ∈ {scalar, record, sum, sequence, map, function, opaque}; new shapes only under a new Revision` | [[wild.core]] |
| accretion_monotone | invariant | `accretes(v, v') iff for every slot: provides(v) ⊆ provides(v') and requires(v') ⊆ requires(v), polarity-aware` | [[wild.core]] |
| polarity_openness_declared | invariant | `every record and sum declares open or closed (default closed); a closed output sum growing, opening, or becoming unrestricted is a break; an input sum growing is an accretion; an input sum losing tolerance is a break` | [[wild.core]] |
| limits_are_slots | invariant | `declared limits (size, cardinality, timeout) are slots; tightening a provided limit or loosening a required limit is a break` | [[wild.core]] |
| defaults_are_slots | invariant | `defaults and environment assumptions are slots; a changed provided default is a break` | [[wild.core]] |
| opaque_is_frozen | invariant | `any change to an opaque slot is a break` | [[wild.core]] |
| facets_independent | invariant | `compat(v, v') is the conjunction over facets of compat_facet(v, v'); facets ∈ {api, abi, layout, serialization, behavior, dialect, environment, license}; the facet set grows only under a new Revision` | [[wild.core]] |
| data_artifacts_have_contracts | invariant | `content files, templates, and generated feature files consumed by code carry a contract checked like an API, including arity and size limits` | [[wild.core]] |
| tombstones_preserve_names | invariant | `a dropped requires leaves a tombstone; re-adding the name must accrete the tombstoned slot` | [[wild.core]] |
| accretion_is_category | invariant | `accretions have identities and compose; composing accretions yields an accretion; the relation is reflexive and transitive` | [[wild.core]] |
| check_against_ancestors | invariant | `a candidate revision is checked against every ancestor in its lineage, not only its predecessor` | [[wild.core]] |
| demand_restriction_functorial | invariant | `restricting a contract to a demand set preserves accretion and composes: restrict(restrict(c, D1), D2) == restrict(c, D1 ∩ D2)` | [[wild.core]] |
| break_requires_new_lineage | invariant | `a non-accretion may be published only under a new lineage name` | [[wild.core]] |
| stability_tiers | invariant | `lineage stability ∈ {stable, experimental, deprecated}; only experimental lineages may be retracted` | [[wild.core]] |
| sunset_computable | invariant | `a contract with a sunset schedule exposes the earliest date at which its provides shrink, queryable before that date` | [[wild.core]] |
| fork_merge_pushout | invariant | `merging two forks of a lineage is defined iff their changes do not collide on a name with different meaning; otherwise the merge is refused and the colliding names listed` | [[wild.core]] |

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
| canonicalize | drafted | canonical | [[wild.core.canonical_form_stable]] |
| identify | canonical | identified | [[wild.core.identity_content_addressed]] ∧ [[wild.core.hash_algorithm_in_identity]] |
| accrete | identified | accretive | [[wild.core.accretion_monotone]] ∧ [[wild.core.check_against_ancestors]] |
| break | identified | lineage_break | [[wild.core.break_requires_new_lineage]] |
| reject | identified | rejected | [[wild.core.name_meaning_immutable]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| hash_matches_content | unit | [[wild.core.identity_content_addressed]] | `arbitrary_contract()` | `id(c) == hash(canonical(c))` |
| canonical_is_order_independent | unit | [[wild.core.canonical_form_stable]] | `arbitrary_contract(), permutation_of_slots()` | `canonical(c) == canonical(permute(c))` |
| algorithms_never_collide | unit | [[wild.core.hash_algorithm_in_identity]] | `same_bytes_hashed_with_two_algorithms()` | `id_a != id_b` |
| versioned_lineage_name_rejected | unit | [[wild.core.lineage_name_versionless]] | `lineage_name_with_version_suffix("acme.billing.v2")` | `check(name) == failed` |
| redefined_meaning_rejected | unit | [[wild.core.name_meaning_immutable]] | `(r, r')` with a slot type changed under the same name | `check(r, r') == failed` |
| unknown_shape_rejected | unit | [[wild.core.slot_shapes_closed]] | `slot_with_shape("tensor")` | `check(slot) == failed` |
| removed_provide_is_break | unit | [[wild.core.accretion_monotone]] | `contract_pair_with(provide_removed: true)` | `accretes(v, v') == false` |
| closed_output_growth_is_break | unit | [[wild.core.polarity_openness_declared]] | `closed_output_sum_with_added_variant()` | `accretes == false`; the same addition in input position yields true |
| tightened_limit_is_break | unit | [[wild.core.limits_are_slots]] | `provided_limit_lowered(500 → 200)` | `accretes == false` |
| changed_default_is_break | unit | [[wild.core.defaults_are_slots]] | `provided_default_changed(30 → 5)` | `accretes == false` |
| opaque_change_is_break | unit | [[wild.core.opaque_is_frozen]] | `opaque_slot_with_changed_content()` | `accretes == false` |
| facet_break_blocks_compat | unit | [[wild.core.facets_independent]] | `pair_with_break_in_exactly_one_facet()` | `compat == failed` |
| feature_file_arity_checked | unit | [[wild.core.data_artifacts_have_contracts]] | `template_defining_21_fields_fed_20_inputs()` | `check == failed` |
| tombstone_blocks_name_reuse | unit | [[wild.core.tombstones_preserve_names]] | `drop_then_readd_input_with_narrower_type()` | `check(readd) == failed` |
| accretion_category_laws | law | [[wild.core.accretion_is_category]] | `arbitrary_contract_chain(length: 3)` | **identity:** `accretes(v, v)` and `compose(id, f) == f` **associativity:** `compose(compose(f, g), h) == compose(f, compose(g, h))` |
| skipped_ancestor_break_caught | unit | [[wild.core.check_against_ancestors]] | `chain_v1_v2_v3_where_v3_breaks_v1_only()` | `check(v3) == failed` |
| restriction_functor_laws | law | [[wild.core.demand_restriction_functorial]] | `arbitrary_contract(), two_demand_sets()` | **identity:** `restrict(c, all_slots) == c` **associativity:** `restrict(restrict(c, D1), D2) == restrict(c, D1 ∩ D2)` |
| break_in_lineage_rejected | unit | [[wild.core.break_requires_new_lineage]] | `breaking_revision_under_same_lineage()` | `publish == rejected` |
| retracting_stable_rejected | unit | [[wild.core.stability_tiers]] | `retract_request_on_stable_lineage()` | `retract == rejected` |
| scheduled_shrink_reported | unit | [[wild.core.sunset_computable]] | `contract_with_sunset(date: d)` | `earliest_break(c) == d` |
| colliding_merge_refused | unit | [[wild.core.fork_merge_pushout]] | `two_forks_defining_same_name_differently()` | `merge == refused ∧ colliding names listed` |

## Notes

Exhaustive small-scope testing (76 single-slot states, 438,976 triples) found four rule gaps in an early checker: optional inputs becoming required, open/closed flips, unrestricted versus restricted sums, and dropped names returning with a new meaning. They are encoded above as `polarity_openness_declared` and `tombstones_preserve_names`. The relation is a conjunction over names, so the single-name result extends to many slots by construction; this was argued, not tested.

The category is thin (at most one morphism between two revisions), so associativity and identity hold structurally; the properties guard the implementation, not the mathematics.
