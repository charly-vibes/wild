---
id: wild.adopt
kind: intent
statement: THE wild SHALL let an existing software project adopt contract versioning in stages, without changing its package manager, registry, or release process.
---

# Wild adoption

How existing, uncontracted software joins the system. The ladder is observe, shadow, gate, native. Each level adds enforcement; none requires rewriting the host ecosystem. Legacy version strings are kept as weak evidence, not discarded. Where software cannot be made compatible, adapters bridge it.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| history_reconstructed | invariant | `adopt(project) extracts a contract at every historical release and derives the lineage graph from computed accretion, never from version strings` | [[wild.adopt]] |
| past_claims_audited | advisory | `each historical release reports declared semver bump against computed verdict; disagreements are listed` | [[wild.adopt]] |
| adoption_levels_ordered | invariant | `levels are ordered observe < shadow < gate < native; a project enters level n+1 only from level n` | [[wild.adopt]] |
| observe_is_read_only | invariant | `level observe writes nothing to source, manifest, registry, or CI configuration` | [[wild.adopt]] |
| shadow_never_blocks | invariant | `level shadow emits verdicts but never changes a build exit status` | [[wild.adopt]] |
| gate_scoped_to_new_changes | invariant | `level gate rejects only breaks introduced after the baseline revision` | [[wild.adopt]] |
| baseline_ack_expires | invariant | `every acknowledged break carries an owner and an expiry; an expired acknowledgement rejects` | [[wild.adopt]] |
| ecosystem_registry_untouched | invariant | `wild never replaces or mutates the host ecosystem's package, tag, or version; it adds a sidecar record` | [[wild.adopt]] |
| sidecar_binds_artifact_digest | invariant | `a sidecar record names the host artifact digest and the revision hash it describes; a mismatch is rejected` | [[wild.adopt]] |
| lock_import_lossless | invariant | `importing a host lockfile yields one lineage and hash per resolved dependency; unresolvable entries become Unknown, never dropped` | [[wild.adopt]] |
| legacy_semver_as_attestation | invariant | `where a dependency has no contract, its declared semver bump is recorded at the attestation tier and never above it` | [[wild.adopt]] |
| demand_derived_from_code | invariant | `consumer demand is derived from consumer code and tests; manual edits are recorded as overrides` | [[wild.adopt]] |
| safe_update_advice | invariant | `for a host version range, wild reports per candidate version whether demanded slots stay compatible; it never overrides the host resolver's choice` | [[wild.adopt]] |
| overlay_contracts | invariant | `a consumer may publish an overlay contract for an uncontracted upstream, bound to the upstream's artifact digest and labelled inferred` | [[wild.adopt]] |
| inferred_is_conservative | invariant | `contracts inferred from traffic or probes mark unobserved slots opaque and reach tier Observed at most` | [[wild.adopt]] |
| adapter_draft_generated | invariant | `adapt(old, new) emits a draft adapter covering every derivable mapping and an explicit TODO for each slot it cannot derive` | [[wild.adopt]] |
| adapter_validated_on_samples | invariant | `a draft adapter is publishable only after its round-trip law passes on recorded samples` | [[wild.adopt]] |
| adapter_forms_closed | invariant | `adapter delivery form ∈ {facade_library, wire_proxy, data_upcaster, component_wrapper}; new forms only under a new Revision` | [[wild.adopt]] |
| consumer_demand_trackable | invariant | `per slot, wild reports which known consumers still demand it; removable(slot) is derived as known_demand(slot) == ∅ and is never stored` | [[wild.adopt]] |
| lineage_routing_exclusive | invariant | `a gateway or resolver may serve several lineages concurrently; each request resolves to exactly one lineage` | [[wild.adopt]] |
| integration_points_share_core | invariant | `CLI, CI action, pre-commit hook, and ecosystem plugins call one core and emit the same envelope` | [[wild.adopt]] |
| init_needs_no_edits | invariant | `init in a supported ecosystem produces extractor configuration, a baseline, and a CI hook without user edits` | [[wild.adopt]] |
| unsupported_ecosystem_degrades | invariant | `an unsupported ecosystem yields Observed or attestation-tier results, never an error that blocks adoption` | [[wild.adopt]] |
| extractor_noise_reported | advisory | `each extraction reports its false-break rate against project history` | [[wild.adopt]] |
| adoption_progress_reported | advisory | `status reports level, share of dependencies per tier, and open acknowledgements` | [[wild.adopt]] |

## Model

### States

- `unmanaged`
- `observed`
- `shadowed`
- `gated`
- `native`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| observe | unmanaged | observed | [[wild.adopt.observe_is_read_only]] ∧ [[wild.adopt.history_reconstructed]] |
| shadow | observed | shadowed | [[wild.adopt.shadow_never_blocks]] |
| gate | shadowed | gated | [[wild.adopt.gate_scoped_to_new_changes]] ∧ [[wild.adopt.baseline_ack_expires]] |
| go_native | gated | native | [[wild.adopt.ecosystem_registry_untouched]] ∧ [[wild.adopt.sidecar_binds_artifact_digest]] |
| step_down | gated | shadowed | [[wild.adopt.adoption_levels_ordered]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| history_graph_from_contracts | unit | [[wild.adopt.history_reconstructed]] | `git_history_with_mislabeled_semver()` | `lineage_graph == computed_accretion_graph` |
| semver_disagreement_listed | unit | [[wild.adopt.past_claims_audited]] | `release_tagged_patch_that_removes_a_slot()` | `audit lists the release` |
| level_skip_rejected | unit | [[wild.adopt.adoption_levels_ordered]] | `project_at_observe_requesting_gate()` | `transition(p) == rejected` |
| observe_writes_nothing | unit | [[wild.adopt.observe_is_read_only]] | `repo_snapshot_before_and_after_observe()` | `snapshot(before) == snapshot(after)` |
| shadow_exit_status_unchanged | unit | [[wild.adopt.shadow_never_blocks]] | `build_with_a_computed_break_in_shadow()` | `exit_status == host_exit_status` |
| baseline_break_tolerated_new_rejected | unit | [[wild.adopt.gate_scoped_to_new_changes]] | `repo_with_old_break_then_new_break()` | `old == tolerated ∧ new == rejected` |
| expired_ack_rejects | unit | [[wild.adopt.baseline_ack_expires]] | `acknowledged_break_past_expiry()` | `check(ack) == rejected` |
| host_version_unchanged | unit | [[wild.adopt.ecosystem_registry_untouched]] | `publish_with_wild_enabled()` | `host_artifact(a) == host_artifact(b)` |
| digest_mismatch_rejected | unit | [[wild.adopt.sidecar_binds_artifact_digest]] | `sidecar_pointing_at_a_different_artifact()` | `check(sidecar) == rejected` |
| lock_entries_all_accounted | unit | [[wild.adopt.lock_import_lossless]] | `lockfile_with_unresolvable_entry()` | `count(imported) == count(lock) ∧ entry.verdict == Unknown` |
| semver_never_above_attestation | unit | [[wild.adopt.legacy_semver_as_attestation]] | `dependency_without_contract_declaring_patch()` | `tier(dep) == attestation` |
| demand_matches_usage | unit | [[wild.adopt.demand_derived_from_code]] | `consumer_using_slots([a, b])` | `demand == {a, b}` |
| advice_leaves_resolver_alone | unit | [[wild.adopt.safe_update_advice]] | `range_with_one_incompatible_candidate()` | `advice flags candidate ∧ host_choice unchanged` |
| overlay_is_labelled_inferred | unit | [[wild.adopt.overlay_contracts]] | `overlay_for_uncontracted_upstream()` | `overlay.label == inferred ∧ overlay.digest == upstream.digest` |
| unobserved_slots_are_opaque | unit | [[wild.adopt.inferred_is_conservative]] | `traffic_covering_half_of_the_api()` | `unobserved slots are opaque ∧ tier ≤ Observed` |
| draft_marks_underivable_slots | unit | [[wild.adopt.adapter_draft_generated]] | `contract_pair_with_one_unmappable_slot()` | `draft has exactly one TODO` |
| unvalidated_adapter_unpublishable | unit | [[wild.adopt.adapter_validated_on_samples]] | `draft_adapter_failing_round_trip()` | `publish(adapter) == rejected` |
| unknown_adapter_form_rejected | unit | [[wild.adopt.adapter_forms_closed]] | `adapter_declaring_form("magic")` | `check(adapter) == failed` |
| zero_demand_slot_removable | unit | [[wild.adopt.consumer_demand_trackable]] | `slot_with_no_known_consumers()` | `removable(slot) == true ∧ no stored flag` |
| one_lineage_per_request | unit | [[wild.adopt.lineage_routing_exclusive]] | `gateway_serving_v1_and_v2()` | `∀ request: count(resolved_lineages) == 1` |
| same_envelope_everywhere | unit | [[wild.adopt.integration_points_share_core]] | `same_change_via_cli_action_and_hook()` | `envelope(cli) == envelope(action) == envelope(hook)` |
| init_works_unedited | unit | [[wild.adopt.init_needs_no_edits]] | `fresh_repo_in_supported_ecosystem()` | `init(r) leaves a runnable baseline and CI hook` |
| unsupported_degrades_not_errors | unit | [[wild.adopt.unsupported_ecosystem_degrades]] | `project_in_unsupported_language()` | `result.tier ≤ Observed ∧ exit_status == ok` |
| noise_rate_reported | unit | [[wild.adopt.extractor_noise_reported]] | `extraction_run_over_known_history()` | `report has false_break_rate` |
| status_lists_tier_shares | unit | [[wild.adopt.adoption_progress_reported]] | `project_with_mixed_dependencies()` | `status lists level ∧ per-tier shares ∧ open acknowledgements` |

## Notes

This is a companion to `wild.md` and relies on its tiers, verdict lattice, and extractor contract. The shape of the sidecar record is deliberately left to a later file.

Known limits: an overlay or inferred contract is only as good as the evidence behind it, and unobserved behavior stays opaque. A removable slot means no known consumer demands it, not that no consumer exists (see `open_world_disclosed` in `wild.md`). Extractor noise on first runs is the main adoption risk, which is why baseline acknowledgements expire rather than silencing breaks forever.
