---
id: spec
kind: intent
statement: THE wild adoption layer SHALL let an existing project adopt contract versioning in stages, without changing its package manager, registry, or release process.
---

# Wild adoption

How existing, uncontracted software joins. The ladder is observe, shadow, gate, native. Each level adds enforcement; none requires rewriting the host ecosystem. Legacy version strings are kept as weak evidence. First enforcement runs in baseline mode, because stricter checking surfaces latent breaks that older tools hid.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| history_reconstructed | invariant | `adopt(project) extracts a contract at every historical release and derives the lineage graph from computed accretion, never from version strings` | [[spec]] |
| past_claims_audited | invariant | `each historical release reports declared version bump against computed verdict; disagreements are listed` | [[spec]] |
| adoption_levels_ordered | invariant | `levels are ordered observe < shadow < gate < native; a project enters level n+1 only from level n` | [[spec]] |
| observe_is_read_only | invariant | `level observe writes nothing to source, manifest, registry, or CI configuration` | [[spec]] |
| shadow_never_blocks | invariant | `level shadow emits verdicts but never changes a build exit status` | [[spec]] |
| gate_scoped_to_new_changes | invariant | `level gate rejects only breaks introduced after the baseline revision` | [[spec]] |
| baseline_ack_expires | invariant | `every acknowledged break carries an owner and an expiry; an expired acknowledgement rejects` | [[spec]] |
| first_run_is_baseline | invariant | `the first enforcement run on a project records existing breaks as baseline and rejects none of them` | [[spec]] |
| lock_import_lossless | invariant | `importing a host lockfile yields one lineage and hash per resolved dependency; unresolvable entries become Unknown, never dropped` | [[spec]] |
| demand_derived_from_code | invariant | `consumer demand is derived from consumer code and tests; manual edits are recorded as overrides` | [[spec]] |
| safe_update_advice | invariant | `for a host version range, wild reports per candidate version whether demanded slots stay compatible; it never overrides the host resolver's choice` | [[spec]] |
| consumer_demand_trackable | invariant | `per slot, wild reports which known consumers still demand it; removable(slot) is derived as known_demand(slot) == ∅ and is never stored` | [[spec]] |
| integration_points_share_core | invariant | `CLI, CI action, pre-commit hook, and ecosystem plugins call one core and emit the same envelope` | [[spec]] |
| init_needs_no_edits | invariant | `init in a supported ecosystem produces extractor configuration, a baseline, and a CI hook without user edits` | [[spec]] |
| unsupported_ecosystem_degrades | invariant | `an unsupported ecosystem yields Observed or attestation-tier results, never an error that blocks adoption` | [[spec]] |
| adoption_progress_reported | advisory | `status reports level, share of dependencies per tier, and open acknowledgements` | [[spec]] |

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
| observe | unmanaged | observed | [[spec.observe_is_read_only]] ∧ [[spec.history_reconstructed]] |
| shadow | observed | shadowed | [[spec.shadow_never_blocks]] |
| gate | shadowed | gated | [[spec.gate_scoped_to_new_changes]] ∧ [[spec.first_run_is_baseline]] |
| go_native | gated | native | [[spec.init_needs_no_edits]] ∧ preserves wild-registry `ecosystem_untouched` and `sidecar_binds_artifact_digest` |
| step_down | gated | shadowed | [[spec.adoption_levels_ordered]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| history_graph_from_contracts | unit | [[spec.history_reconstructed]] | `git_history_with_mislabeled_semver()` | `lineage_graph == computed_accretion_graph` |
| semver_disagreement_listed | unit | [[spec.past_claims_audited]] | `release_tagged_patch_that_removes_a_slot()` | `audit lists the release` |
| level_skip_rejected | unit | [[spec.adoption_levels_ordered]] | `project_at_observe_requesting_gate()` | `transition == rejected` |
| observe_writes_nothing | unit | [[spec.observe_is_read_only]] | `repo_snapshot_before_and_after_observe()` | `snapshot(before) == snapshot(after)` |
| shadow_exit_status_unchanged | unit | [[spec.shadow_never_blocks]] | `build_with_a_computed_break_in_shadow()` | `exit_status == host_exit_status` |
| baseline_break_tolerated_new_rejected | unit | [[spec.gate_scoped_to_new_changes]] | `repo_with_old_break_then_new_break()` | `old == tolerated ∧ new == rejected` |
| expired_ack_rejects | unit | [[spec.baseline_ack_expires]] | `acknowledged_break_past_expiry()` | `check(ack) == rejected` |
| first_run_rejects_nothing_old | unit | [[spec.first_run_is_baseline]] | `repo_with_many_latent_breaks_first_run()` | `rejections == 0 ∧ baseline lists all` |
| lock_entries_all_accounted | unit | [[spec.lock_import_lossless]] | `lockfile_with_unresolvable_entry()` | `count(imported) == count(lock) ∧ entry.verdict == Unknown` |
| demand_matches_usage | unit | [[spec.demand_derived_from_code]] | `consumer_using_slots([a, b])` | `demand == {a, b}` |
| advice_leaves_resolver_alone | unit | [[spec.safe_update_advice]] | `range_with_one_incompatible_candidate()` | `advice flags candidate ∧ host_choice unchanged` |
| zero_demand_slot_removable | unit | [[spec.consumer_demand_trackable]] | `slot_with_no_known_consumers()` | `removable(slot) == true ∧ no stored flag` |
| same_envelope_everywhere | unit | [[spec.integration_points_share_core]] | `same_change_via_cli_action_and_hook()` | `envelope(cli) == envelope(action) == envelope(hook)` |
| init_works_unedited | unit | [[spec.init_needs_no_edits]] | `fresh_repo_in_supported_ecosystem()` | `init leaves a runnable baseline and CI hook` |
| unsupported_degrades_not_errors | unit | [[spec.unsupported_ecosystem_degrades]] | `project_in_unsupported_language()` | `result.tier ≤ Observed ∧ exit_status == ok` |
| status_lists_tier_shares | unit | [[spec.adoption_progress_reported]] | `project_with_mixed_dependencies()` | `status lists level ∧ per-tier shares ∧ open acknowledgements` |

## Notes

Lesson from the catalog: pip's stricter resolver in 2020 exposed conflicts older installers hid, so first enforcement must not reject legacy breaks (`first_run_is_baseline`). Baseline acknowledgements expire so old breaks cannot be silenced forever.

Known limits: a removable slot means no known consumer demands it, not that none exists (see `open_world_disclosed` in `wild`). Extractor noise on first runs is the main adoption risk and is reported in `wild.extract`.
