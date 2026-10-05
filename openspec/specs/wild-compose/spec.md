---
id: spec
kind: intent
statement: THE wild composer SHALL decide whether components at given revisions compose into a well-formed assembly, select revisions without search, and emit a certificate an independent verifier can re-check.
---

# Wild compose

An assembly is components plus bindings from required slots to provided slots. It is well-formed when every required slot is bound by a compatible provide. Substituting a component by an accretion of itself preserves well-formedness, which is what makes resolution a lookup instead of a search. Verdicts carry certificates that a separate verifier checks from content hashes.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| assembly_is_bindings | invariant | `an assembly is a set of component revisions plus bindings from each required slot to a provided slot` | [[spec]] |
| binding_well_formed | invariant | `a binding is well-formed iff provider type ⊆ consumer type and the provider's variants fit the consumer; an open or unrestricted provider sum binds only to an open consumer` | [[spec]] |
| required_slots_bound | invariant | `every required input of every component is bound by a well-formed binding` | [[spec]] |
| substitution_preserves_assembly | invariant | `replacing a component with an accretion of itself keeps a well-formed assembly well-formed` | [[spec]] |
| scoped_substitution | invariant | `replacing a component with a revision that accretes on every slot the assembly uses keeps the assembly well-formed, even if the full accretion check fails` | [[spec]] |
| resolution_by_lineage | invariant | `resolution selects the newest revision per package and lineage that satisfies demand, without search` | [[spec]] |
| resolver_deterministic | invariant | `the same registry snapshot and demand yield the same selection and certificate` | [[spec]] |
| lineage_copies_listed | invariant | `when consumers demand different lineages of one package, each lineage is resolved separately and the copies are listed` | [[spec]] |
| scoped_merge_proposed | invariant | `a consumer may be proposed a newer lineage when its demand accretes there; the move is a proposal and is never applied automatically` | [[spec]] |
| boundary_needs_adapter | invariant | `values crossing between lineages need a registered adapter; otherwise the boundary is reported unbridged` | [[spec]] |
| singleton_declared | invariant | `a component declared singleton appears under exactly one lineage per assembly; a violation is a composition failure` | [[spec]] |
| relation_slots | invariant | `declared relations between contracts (timeout ordering, paired revisions) are checked at composition` | [[spec]] |
| certificate_lists_bindings | invariant | `a certificate lists, per binding, the consumer revision, provider revision, and demanded slots` | [[spec]] |
| certificate_complete | invariant | `a certificate missing a binding of the assembly is rejected` | [[spec]] |
| certificate_tamper_evident | invariant | `a corrupted hash or dropped binding fails verification; a substituted provider verifies only if it is compatible with the consumer's demand` | [[spec]] |
| verifier_reads_only_certificate | invariant | `the verifier reads only the certificate and content-addressed contracts and never calls the resolver` | [[spec]] |
| verification_linear | advisory | `verification time grows linearly with the number of bindings` | [[spec]] |
| coverage_reported | invariant | `a composition verdict reports the share of bindings verified per tier; bindings to uncontracted providers are Unknown` | [[spec]] |
| verdict_is_meet | invariant | `the assembly verdict is the meet of its binding verdicts` | [[spec]] |
| composition_is_category | invariant | `assemblies compose associatively with the empty assembly as identity` | [[spec]] |

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
| resolve | demanded | resolved | [[spec.resolution_by_lineage]] ∧ [[spec.resolver_deterministic]] |
| certify | resolved | certified | [[spec.certificate_lists_bindings]] |
| verify | certified | verified | [[spec.certificate_complete]] ∧ [[spec.verifier_reads_only_certificate]] |
| flag_boundary | resolved | unbridged | [[spec.boundary_needs_adapter]] |
| bridge | unbridged | certified | [[spec.certificate_lists_bindings]] ∧ requires a wild-bridge `adapter_is_morphism` |
| refuse_unbound | resolved | refused | [[spec.required_slots_bound]] |
| refuse_invalid | certified | refused | [[spec.binding_well_formed]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| assembly_lists_every_binding | unit | [[spec.assembly_is_bindings]] | `arbitrary_assembly()` | `bindings cover all required slots` |
| open_provider_needs_open_consumer | unit | [[spec.binding_well_formed]] | `open_provider_sum_bound_to_closed_consumer()` | `well_formed == false` |
| unbound_required_slot_rejected | unit | [[spec.required_slots_bound]] | `assembly_with_one_unbound_required_input()` | `well_formed == false` |
| accretion_substitution_sound | unit | [[spec.substitution_preserves_assembly]] | `well_formed_assembly_and_accepted_accretion()` | `well_formed(after) == true` |
| scoped_substitution_sound | unit | [[spec.scoped_substitution]] | `assembly_and_change_accreting_on_used_slots()` | `well_formed(after) == true` |
| resolution_is_chain_max | unit | [[spec.resolution_by_lineage]] | `arbitrary_ecosystem_and_demand()` | `selection == newest per lineage ∧ search_nodes == 0` |
| resolution_reproducible | unit | [[spec.resolver_deterministic]] | `same_snapshot_resolved_twice()` | `selection(a) == selection(b) ∧ cert(a) == cert(b)` |
| copies_are_listed | unit | [[spec.lineage_copies_listed]] | `consumers_on_two_lineages_of_one_package()` | `report lists both copies` |
| merge_is_a_proposal | unit | [[spec.scoped_merge_proposed]] | `consumer_whose_demand_accretes_in_newer_lineage()` | `proposal listed ∧ selection unchanged` |
| unbridged_boundary_reported | unit | [[spec.boundary_needs_adapter]] | `value_crossing_lineages_without_adapter()` | `status == unbridged` |
| second_lineage_of_singleton_fails | unit | [[spec.singleton_declared]] | `singleton_resolved_under_two_lineages()` | `composition == failed` |
| timeout_relation_checked | unit | [[spec.relation_slots]] | `backend_idle_timeout_below_balancer_timeout()` | `composition == failed` |
| certificate_names_all_fields | unit | [[spec.certificate_lists_bindings]] | `arbitrary_certificate()` | `each binding has consumer ∧ provider ∧ demand` |
| missing_binding_rejected | unit | [[spec.certificate_complete]] | `certificate_with_one_binding_dropped()` | `verify == rejected` |
| corruption_detected | unit | [[spec.certificate_tamper_evident]] | `certificate_with_last_hash_digit_changed()` | `verify == rejected` |
| verifier_has_no_resolver_dependency | unit | [[spec.verifier_reads_only_certificate]] | `verifier_module_dependency_graph()` | `no edge to resolver` |
| verification_cost_linear | unit | [[spec.verification_linear]] | `certificates_of_size([100, 1000, 10000])` | `time ratio ≈ size ratio` |
| uncontracted_binding_is_unknown | unit | [[spec.coverage_reported]] | `assembly_with_one_uncontracted_provider()` | `binding.verdict == Unknown ∧ coverage lists it` |
| verdict_equals_meet | unit | [[spec.verdict_is_meet]] | `bindings_with_mixed_verdicts()` | `assembly.verdict == meet(bindings)` |
| assembly_composition_laws | law | [[spec.composition_is_category]] | `three_arbitrary_assemblies()` | **identity:** `compose(empty, a) == a` **associativity:** `compose(compose(a, b), c) == compose(a, compose(b, c))` |

## Notes

Simulation evidence (toy model, assumed parameters): 30,000 random four-component assemblies, 10,215 accepted accretions, zero assemblies broken by substitution; 22% of changes rejected by the full check were harmless to the specific assembly, which is the case for `scoped_substitution`. In a synthetic ecosystem (30 packages, 8 versions each), lineage resolution broke zero dependencies and needed no search, while a single-version semver resolver found no solution in 16.5% to 99% of cases depending on break rate and mislabelling. With truthful labels, lineage resolution and semver-with-duplicates coincide, so the contribution is machine-checked labels. A verifier re-checked about 41 bindings per assembly in about 1 ms and rejected all 750 corrupted-hash and 750 dropped-binding certificates.

Known limits: the wiring rule was tightened after the first run found 21 unsound cases involving open sums; that is a model decision, recorded in `binding_well_formed`. Assemblies in the tests had four components and four names (small-scope).
