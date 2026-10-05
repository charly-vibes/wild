---
id: wild
kind: intent
statement: THE wild SHALL decide, by tiered and computable checks instead of asserted version numbers, whether one revision of a software contract may replace another.
---

# Wild

A language-blind tool for versioning software contracts. A contract is a set of named slots (requires and provides, each with polarity), laws, limits, and facets. Revisions are content-addressed and form a chain inside a lineage. A change that is not an accretion must start a new lineage and ship an adapter. Compatibility is decided by tiers ordered by cost: identity, shape, laws, evidence, attestation. The first three are exact and deterministic; the last two are graded or human.

This spec is written in specodelic format and follows `specs/specodelic.md`. Prose is never inspected by the parser.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| identity_content_addressed | invariant | `revision.id == hash(canonical(contract)); equal ids ⇒ identical contracts` | [[wild]] |
| canonical_form_stable | invariant | `canonical(c) is independent of slot order, whitespace, extractor, host, and clock` | [[wild]] |
| lineage_name_versionless | invariant | `lineage.name is namespaced, non-empty, and contains no version component` | [[wild]] |
| name_meaning_immutable | invariant | `∀ slot name n, revisions r < r' in one lineage: type(n, r) == type(n, r') ∧ laws(n, r) ⊆ laws(n, r')` | [[wild]] |
| accretion_monotone | invariant | `accretes(v, v') ⟺ ∀ slot: provides(v) ⊆ provides(v') ∧ requires(v') ⊆ requires(v)` | [[wild]] |
| polarity_openness_declared | invariant | `∀ record/sum slot: openness ∈ {open, closed} declared (default closed); adding a variant is a break in output position and an accretion in input position` | [[wild]] |
| limits_are_slots | invariant | `declared limits (size, cardinality, timeout) are slots; tightening a provided limit or loosening a required limit is a break` | [[wild]] |
| opaque_is_frozen | invariant | `∀ slot of kind opaque: any change to its content is a break` | [[wild]] |
| facets_independent | invariant | `compat(v, v') == ∧ over facets of compat_facet(v, v'); facet set grows only under a new Revision (append_only_variants)` | [[wild]] |
| sunset_computable | invariant | `a contract with a sunset schedule exposes the earliest date at which provides shrink, queryable before that date` | [[wild]] |
| accretion_is_category | invariant | `accretion morphisms have identities and compose; composition of accretions is an accretion` | [[wild]] |
| check_against_ancestors | invariant | `a candidate revision is checked against every ancestor in its lineage, not only its predecessor` | [[wild]] |
| break_requires_new_lineage | invariant | `¬accretes(v, v') ⇒ publish is permitted only under a new lineage name` | [[wild]] |
| break_requires_adapter | invariant | `new lineage L' derived from L is published only with a registered adapter L → L'` | [[wild]] |
| adapter_is_morphism | invariant | `adapters have identities and compose associatively; composed adapters equal the direct adapter when one is registered` | [[wild]] |
| adapter_loss_declared | invariant | `every adapter declares lossless or lists the slots it loses; a declared-lossless adapter has a round-trip law` | [[wild]] |
| unknown_fields_preserved | invariant | `read-modify-write through any generated client or adapter preserves slots outside its demand set` | [[wild]] |
| laws_cumulative | invariant | `laws(v') ⊇ ⋃ laws(ancestors); every ancestor law passes against v' implementation` | [[wild]] |
| law_runs_deterministic | invariant | `same (contract, implementation, seed) ⇒ same law result; seeds are recorded in the report` | [[wild]] |
| registry_append_only | invariant | `registry is a Merkle-chained log; no revision is deleted or mutated after publish` | [[wild]] |
| lock_pins_hashes | invariant | `every lockfile entry is lineage@hash; mutable tags and aliases never resolve` | [[wild]] |
| namespace_ownership | invariant | `each lineage name maps to one owner key; key rotation is recorded as a signed entry` | [[wild]] |
| demand_scoped_updates | invariant | `an update is blocked iff a demanded slot changes incompatibly; changes to undemanded slots are reported but never block` | [[wild]] |
| resolve_chain_max | invariant | `within one lineage, resolution selects the greatest revision satisfying demand without search` | [[wild]] |
| baseline_grandfathers | invariant | `in baseline mode, breaks present at the baseline revision are recorded; new breaks are rejected` | [[wild]] |
| fail_fast_ordering | invariant | `tiers run in order identity < shape < laws < evidence < attestation; a run stops at the first Reject` | [[wild]] |
| exact_tiers_pure | invariant | `tiers identity, shape, laws are pure: same inputs ⇒ same verdict, with no network or clock access` | [[wild]] |
| evidence_cannot_override_exact | invariant | `evidence may raise a Pass confidence; it never turns a Reject from an exact tier into Pass` | [[wild]] |
| verdict_lattice | invariant | `verdicts form a lattice Reject < Unknown < PassDeclared < PassLawChecked < PassObserved with meet and join; policy names the minimum required tier` | [[wild]] |
| evidence_confidence_conservative | advisory | `reported confidence is the minimum over contributing observations, never a product` | [[wild]] |
| contradiction_triggers_repair | invariant | `observed behavior contradicting the declared contract creates a repair draft; the contract is never edited silently` | [[wild]] |
| attestation_expiring | invariant | `an attestation carries signer, scope, and expiry; an expired attestation counts as Unknown` | [[wild]] |
| extractor_contract | extension_point | `∀ extractor E conforming: extract(source) → ContractIR, deterministic, and reports coverage listing every unextracted construct` | [[wild]] |
| extraction_total | invariant | `every source construct maps to a slot or to an opaque slot; none is dropped silently` | [[wild]] |
| extractor_coverage_reported | advisory | `each extraction reports the share of constructs mapped to opaque slots` | [[wild]] |
| law_harness | extension_point | `∀ harness H conforming: run(suite, implementation, seed) → LawResult, deterministic given the seed` | [[wild]] |
| output_envelope | invariant | `every command emits a JSON envelope with tier, verdict, and slot ids; the human rendering is derived from the same data` | [[wild]] |
| honest_verdict_labels | invariant | `a verdict names the highest tier passed; the bare word compatible is never emitted` | [[wild]] |
| open_world_disclosed | advisory | `every compatibility report lists known consumers and states that undeclared consumers are not covered` | [[wild]] |

## Model

### States

- `draft`
- `extracted`
- `identified`
- `shape_checked`
- `law_checked`
- `published`
- `observed`
- `attested`
- `rejected`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| extract | draft | extracted | [[wild.extraction_total]] |
| identify | extracted | identified | [[wild.identity_content_addressed]] ∧ [[wild.lineage_name_versionless]] |
| shape_check | identified | shape_checked | [[wild.accretion_monotone]] ∧ [[wild.check_against_ancestors]] |
| law_check | shape_checked | law_checked | [[wild.laws_cumulative]] |
| publish | law_checked | published | [[wild.break_requires_adapter]] ∧ [[wild.registry_append_only]] |
| observe | published | observed | [[wild.evidence_cannot_override_exact]] |
| attest | observed | attested | [[wild.attestation_expiring]] |
| repair | observed | draft | [[wild.contradiction_triggers_repair]] |
| reject_identity | extracted | rejected | [[wild.fail_fast_ordering]] |
| reject_shape | identified | rejected | [[wild.fail_fast_ordering]] |
| reject_laws | shape_checked | rejected | [[wild.fail_fast_ordering]] |
| reject_publish | law_checked | rejected | [[wild.fail_fast_ordering]] |
| revise | rejected | draft | [[wild.identity_content_addressed]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| hash_matches_content | unit | [[wild.identity_content_addressed]] | `arbitrary_contract()` | `id(c) == hash(canonical(c))` |
| canonical_is_order_independent | unit | [[wild.canonical_form_stable]] | `arbitrary_contract(), permutation_of_slots()` | `canonical(c) == canonical(permute(c))` |
| versioned_lineage_name_rejected | unit | [[wild.lineage_name_versionless]] | `lineage_name_with_version_suffix("acme.billing.v2")` | `check(name) == failed` |
| redefined_slot_meaning_rejected | unit | [[wild.name_meaning_immutable]] | `(r, r')` with a slot's type changed under the same name | `check(r, r') == failed` |
| removed_provide_is_break | unit | [[wild.accretion_monotone]] | `contract_pair_with(provide_removed: true)` | `accretes(v, v') == false` |
| output_variant_addition_is_break | unit | [[wild.polarity_openness_declared]] | `closed_output_sum_with_added_variant()` | `accretes(v, v') == false`; the same addition in input position yields `true` |
| tightened_limit_is_break | unit | [[wild.limits_are_slots]] | `provided_limit_lowered(500 → 200)` | `accretes(v, v') == false` |
| opaque_change_is_break | unit | [[wild.opaque_is_frozen]] | `opaque_slot_with_changed_content()` | `accretes(v, v') == false` |
| facet_break_blocks_compat | unit | [[wild.facets_independent]] | `pair_with_break_in_exactly_one_facet()` | `compat(v, v') == failed` |
| scheduled_shrink_reported | unit | [[wild.sunset_computable]] | `contract_with_sunset(date: d)` | `earliest_break(c) == d` |
| accretion_category_laws | law | [[wild.accretion_is_category]] | `arbitrary_contract_chain(length: 3)` | **identity:** `accretes(v, v)` and `compose(id, f) == f` **associativity:** `compose(compose(f, g), h) == compose(f, compose(g, h))` |
| skipped_ancestor_break_caught | unit | [[wild.check_against_ancestors]] | `chain_v1_v2_v3_where_v3_breaks_v1_only()` | `check(v3) == failed` |
| break_in_same_lineage_rejected | unit | [[wild.break_requires_new_lineage]] | `breaking_revision_published_under_same_lineage()` | `publish(r) == rejected` |
| break_without_adapter_rejected | unit | [[wild.break_requires_adapter]] | `new_lineage_without_registered_adapter()` | `publish(r) == rejected` |
| adapter_category_laws | law | [[wild.adapter_is_morphism]] | `arbitrary_adapter_chain(length: 3)` | **identity:** `compose(id, a) == a` **associativity:** `compose(compose(a, b), c) == compose(a, compose(b, c))` **naturality:** `adapt(extract(x)) == extract(adapt_source(x))` |
| lossy_adapter_must_list_loss | unit | [[wild.adapter_loss_declared]] | `adapter_with_dropped_slot_declared_lossless()` | `check(adapter) == failed` |
| round_trip_keeps_unknown_slots | unit | [[wild.unknown_fields_preserved]] | `record_with_slots_outside_demand()` | `read_modify_write(r) ⊇ unknown_slots(r)` |
| ancestor_law_failure_rejected | unit | [[wild.laws_cumulative]] | `revision_whose_impl_violates_an_ancestor_law()` | `law_check(r) == failed` |
| law_run_reproducible | unit | [[wild.law_runs_deterministic]] | `(contract, impl, seed)` run twice | `run(a) == run(b)` |
| mutation_of_published_rejected | unit | [[wild.registry_append_only]] | `registry_with_attempted_rewrite()` | `append(log, rewrite) == rejected` |
| alias_in_lock_rejected | unit | [[wild.lock_pins_hashes]] | `lockfile_entry_using_tag("latest")` | `check(lock) == failed` |
| foreign_owner_publish_rejected | unit | [[wild.namespace_ownership]] | `publish_to_lineage_with_a_different_key()` | `publish(r) == rejected` |
| undemanded_change_does_not_block | unit | [[wild.demand_scoped_updates]] | `update_changing_only_undemanded_slots()` | `update(u) reports change ∧ not blocked` |
| chain_resolution_is_max | unit | [[wild.resolve_chain_max]] | `arbitrary_chain_with_demand()` | `resolve(chain, demand) == max(satisfying(chain, demand))` |
| baseline_break_recorded_new_break_rejected | unit | [[wild.baseline_grandfathers]] | `repo_with_preexisting_break_then_new_break()` | `old == recorded ∧ new == rejected` |
| first_reject_stops_run | unit | [[wild.fail_fast_ordering]] | `revision_failing_identity_and_laws()` | `tiers_run == [identity] ∧ verdict == Reject` |
| exact_tiers_have_no_side_inputs | unit | [[wild.exact_tiers_pure]] | `same_inputs_with_varied_clock_and_network()` | `verdict(a) == verdict(b)` |
| evidence_never_overrides_reject | unit | [[wild.evidence_cannot_override_exact]] | `shape_Reject_plus_clean_traffic_replay()` | `verdict == Reject` |
| verdict_lattice_laws | law | [[wild.verdict_lattice]] | `three_arbitrary_verdicts()` | **identity:** `meet(v, PassObserved) == v` **associativity:** `meet(meet(a, b), c) == meet(a, meet(b, c))` |
| confidence_is_minimum | unit | [[wild.evidence_confidence_conservative]] | `observations_with_confidences([0.99, 0.90])` | `confidence == 0.90` |
| contradiction_creates_draft | unit | [[wild.contradiction_triggers_repair]] | `observed_behavior_outside_declared_contract()` | `repair_draft_created ∧ contract_unchanged` |
| expired_attestation_is_unknown | unit | [[wild.attestation_expiring]] | `attestation_with_past_expiry()` | `verdict(a) == Unknown` |
| extractor_reports_coverage | unit | [[wild.extractor_contract]] | `extractor_output_with_unmapped_construct()` | `coverage lists the construct` |
| no_silent_drop | unit | [[wild.extraction_total]] | `source_with_unsupported_construct()` | `slot_for(construct) is opaque` |
| opaque_share_reported | unit | [[wild.extractor_coverage_reported]] | `source_with_known_opaque_count(3 of 10)` | `report.opaque_share == 0.3` |
| harness_deterministic_given_seed | unit | [[wild.law_harness]] | `harness_run_twice_with_same_seed()` | `result(a) == result(b)` |
| envelope_matches_human | unit | [[wild.output_envelope]] | `arbitrary_check_result()` | `parse(render_human(r)) agrees with envelope(r)` |
| bare_compatible_never_emitted | unit | [[wild.honest_verdict_labels]] | `arbitrary_passing_result()` | `output names the highest tier passed ∧ not equals "compatible"` |
| unknown_consumers_disclosed | unit | [[wild.open_world_disclosed]] | `report_with_known_consumers([a, b])` | `report states undeclared consumers are not covered` |

## Notes

Written from `specs/specodelic.md` alone; the `specodelic` binary was not available, so this file has not been run through `specodelic lint`. Before relying on it, scaffold with `specodelic new wild --file wild.md`, port the tables if the scaffold's columns differ, and run `specodelic lint specs`.

Deliberate boundaries:

- `expr`, `generator`, and `predicate` stay unparsed strings, as in the base format. The laws here are checked by the generated proptest scaffolding, not proven.
- The behavior facet is only as good as the laws authors write and the harness that runs them. Undeclared behavior (Hyrum's law) is out of scope and is disclosed by `open_world_disclosed`, not solved.
- Tier 3 evidence is statistical. The choice of minimum over product in `evidence_confidence_conservative` is a modelling decision (failures are correlated), flagged for human review. It is advisory, so it never gates a transition.
- Governance cases (namespace disputes, sunsets caused by third parties) are recorded as attestations, never computed.

Candidate follow-ups, each as its own file: `wild-ir.md` (the Contract IR), `wild-manifest.md` (manifest and lockfile), and one `extractor-*.md` per ecosystem using `extension_point`/`satisfies`.
