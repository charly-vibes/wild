---
id: spec
kind: intent
statement: THE wild adoption layer SHALL let an existing project adopt contract versioning in stages, without changing its package manager, registry, or release process.
---

# Wild adoption

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

How existing, uncontracted software joins. The ladder is observe, shadow, gate, native. Each level adds enforcement; none requires rewriting the host ecosystem. Legacy version strings are kept as weak evidence. First enforcement runs in baseline mode, because stricter checking surfaces latent breaks that older tools hid.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| history_reconstructed | invariant | `adopt(project) extracts each available historical release; missing source or extraction failure is preserved as an Unknown history node and cannot establish an accretion edge; version strings never establish edges` | [[spec]] |
| past_claims_audited | invariant | `each historical release reports declared version bump against computed verdict; disagreements are listed` | [[spec]] |
| adoption_levels_ordered | invariant | `levels are ordered observe < shadow < gate < native; a project enters level n+1 only from level n` | [[spec]] |
| observe_is_read_only | invariant | `level observe writes nothing to source, manifest, registry, or CI configuration` | [[spec]] |
| shadow_never_blocks | invariant | `level shadow emits verdicts but never changes a build exit status` | [[spec]] |
| gate_scoped_to_new_changes | invariant | `level gate rejects newly introduced breaks and expired baseline acknowledgements; baseline ids are immutable and cannot be reset implicitly by init, retries, or stepping down and up` | [[spec]] |
| baseline_ack_expires | invariant | `each baseline break has an owner, issue time, expiry, and stable finding id; default expiry is 30 days; renewal requires a signed reason and new expiry and appends an audit event rather than replacing history` | [[spec]] |
| first_run_is_baseline | invariant | `first enforcement atomically records a baseline digest, existing findings, and 30-day acknowledgements owned by the initiating identity; it tolerates existing breaks only after baseline persistence succeeds; persistence failure refuses enforcement activation` | [[spec]] |
| lock_import_lossless | invariant | `importing a host lockfile yields one lineage and hash per resolved dependency; unresolvable entries become Unknown, never dropped` | [[spec]] |
| demand_derived_from_code | invariant | `demand includes statically resolved usage and declared dynamic usage; unresolved reflection, plugins, or dynamic calls mark demand incomplete and block safe-removal and scoped-substitution claims; manual reductions require signed scoped expiring overrides and remain disclosed` | [[spec]] |
| safe_update_advice | invariant | `for a host version range, wild reports per candidate version whether demanded slots stay compatible; it never overrides the host resolver's choice` | [[spec]] |
| consumer_demand_trackable | invariant | `per slot, wild reports known consumers; removal_candidate(slot) is derived only when known demand is empty and all known demand manifests are complete and fresh; it is advisory and never authorizes removal within a stable lineage` | [[spec]] |
| integration_points_share_core | invariant | `CLI, CI action, pre-commit hook, and ecosystem plugins call one core and emit the same envelope` | [[spec]] |
| init_needs_no_edits | invariant | `init in a supported ecosystem produces extractor configuration, a baseline, and a CI hook without user edits` | [[spec]] |
| unsupported_ecosystem_degrades | invariant | `unsupported extraction yields Unknown assurance with scoped observations or metadata claims when available; observe and shadow succeed with diagnostics, while gate/native refuse any unmet required policy` | [[spec]] |
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
| zero_demand_slot_removable | unit | [[spec.consumer_demand_trackable]] | `slot_with_no_known_consumers()` | `removal_candidate(slot) == true ∧ advisory_only ∧ no stored flag` |
| same_envelope_everywhere | unit | [[spec.integration_points_share_core]] | `same_change_via_cli_action_and_hook()` | `envelope(cli) == envelope(action) == envelope(hook)` |
| init_works_unedited | unit | [[spec.init_needs_no_edits]] | `fresh_repo_in_supported_ecosystem()` | `init leaves a runnable baseline and CI hook` |
| unsupported_degrades_not_errors | unit | [[spec.unsupported_ecosystem_degrades]] | `project_in_unsupported_language()` | `result.assurance == Unknown ∧ observe_exit_status == ok` |
| status_lists_tier_shares | unit | [[spec.adoption_progress_reported]] | `project_with_mixed_dependencies()` | `status lists level ∧ per-tier shares ∧ open acknowledgements` |

## Notes

Lesson from the catalog: pip's stricter resolver in 2020 exposed conflicts older installers hid, so first enforcement must not reject legacy breaks (`first_run_is_baseline`). Baseline acknowledgements expire so old breaks cannot be silenced forever.

Known limits: a removable slot means no known consumer demands it, not that none exists (see `open_world_disclosed` in `wild`). Extractor noise on first runs is the main adoption risk and is reported in `wild.extract`.

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: History reconstructed

The system SHALL satisfy `history_reconstructed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: History graph from contracts
- **GIVEN** the fixture domain `git_history_with_mislabeled_semver()`
- **WHEN** the `history_reconstructed` check runs
- **THEN** `lineage_graph == computed_accretion_graph`

### Rule: Past claims audited

The system SHALL satisfy `past_claims_audited` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Semver disagreement listed
- **GIVEN** the fixture domain `release_tagged_patch_that_removes_a_slot()`
- **WHEN** the `past_claims_audited` check runs
- **THEN** `audit lists the release`

### Rule: Adoption levels ordered

The system SHALL satisfy `adoption_levels_ordered` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Level skip rejected
- **GIVEN** the fixture domain `project_at_observe_requesting_gate()`
- **WHEN** the `adoption_levels_ordered` check runs
- **THEN** `transition == rejected`

### Rule: Observe is read only

The system SHALL satisfy `observe_is_read_only` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Observe writes nothing
- **GIVEN** the fixture domain `repo_snapshot_before_and_after_observe()`
- **WHEN** the `observe_is_read_only` check runs
- **THEN** `snapshot(before) == snapshot(after)`

### Rule: Shadow never blocks

The system SHALL satisfy `shadow_never_blocks` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Shadow exit status unchanged
- **GIVEN** the fixture domain `build_with_a_computed_break_in_shadow()`
- **WHEN** the `shadow_never_blocks` check runs
- **THEN** `exit_status == host_exit_status`

### Rule: Gate scoped to new changes

The system SHALL satisfy `gate_scoped_to_new_changes` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Baseline break tolerated new rejected
- **GIVEN** the fixture domain `repo_with_old_break_then_new_break()`
- **WHEN** the `gate_scoped_to_new_changes` check runs
- **THEN** `old == tolerated ∧ new == rejected`

### Rule: Baseline ack expires

The system SHALL satisfy `baseline_ack_expires` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Expired ack rejects
- **GIVEN** the fixture domain `acknowledged_break_past_expiry()`
- **WHEN** the `baseline_ack_expires` check runs
- **THEN** `check(ack) == rejected`

### Rule: First run is baseline

The system SHALL satisfy `first_run_is_baseline` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: First run rejects nothing old
- **GIVEN** the fixture domain `repo_with_many_latent_breaks_first_run()`
- **WHEN** the `first_run_is_baseline` check runs
- **THEN** `rejections == 0 ∧ baseline lists all`

### Rule: Lock import lossless

The system SHALL satisfy `lock_import_lossless` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Lock entries all accounted
- **GIVEN** the fixture domain `lockfile_with_unresolvable_entry()`
- **WHEN** the `lock_import_lossless` check runs
- **THEN** `count(imported) == count(lock) ∧ entry.verdict == Unknown`

### Rule: Demand derived from code

The system SHALL satisfy `demand_derived_from_code` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Demand matches usage
- **GIVEN** the fixture domain `consumer_using_slots([a, b])`
- **WHEN** the `demand_derived_from_code` check runs
- **THEN** `demand == {a, b}`

### Rule: Safe update advice

The system SHALL satisfy `safe_update_advice` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Advice leaves resolver alone
- **GIVEN** the fixture domain `range_with_one_incompatible_candidate()`
- **WHEN** the `safe_update_advice` check runs
- **THEN** `advice flags candidate ∧ host_choice unchanged`

### Rule: Consumer demand trackable

The system SHALL satisfy `consumer_demand_trackable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Zero demand slot removable
- **GIVEN** the fixture domain `slot_with_no_known_consumers()`
- **WHEN** the `consumer_demand_trackable` check runs
- **THEN** `removal_candidate(slot) == true ∧ advisory_only ∧ no stored flag`

### Rule: Integration points share core

The system SHALL satisfy `integration_points_share_core` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Same envelope everywhere
- **GIVEN** the fixture domain `same_change_via_cli_action_and_hook()`
- **WHEN** the `integration_points_share_core` check runs
- **THEN** `envelope(cli) == envelope(action) == envelope(hook)`

### Rule: Init needs no edits

The system SHALL satisfy `init_needs_no_edits` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Init works unedited
- **GIVEN** the fixture domain `fresh_repo_in_supported_ecosystem()`
- **WHEN** the `init_needs_no_edits` check runs
- **THEN** `init leaves a runnable baseline and CI hook`

### Rule: Unsupported ecosystem degrades

The system SHALL satisfy `unsupported_ecosystem_degrades` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unsupported degrades not errors
- **GIVEN** the fixture domain `project_in_unsupported_language()`
- **WHEN** the `unsupported_ecosystem_degrades` check runs
- **THEN** `result.assurance == Unknown ∧ observe_exit_status == ok`

### Rule: Adoption progress reported

The system SHALL satisfy `adoption_progress_reported` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Status lists tier shares
- **GIVEN** the fixture domain `project_with_mixed_dependencies()`
- **WHEN** the `adoption_progress_reported` check runs
- **THEN** `status lists level ∧ per-tier shares ∧ open acknowledgements`

#### Acceptance case: Reinitialization cannot erase baseline findings
- **GIVEN** a project has an immutable baseline with an expired acknowledgement
- **WHEN** init is rerun or enforcement is stepped down and up
- **THEN** the baseline id remains unchanged and the expired finding still refuses enforcement

#### Acceptance case: Dynamic calls prevent safe removal advice
- **GIVEN** reflection leaves a known consumer demand manifest incomplete
- **WHEN** a slot has no statically identified consumers
- **THEN** removal_candidate is not asserted and scoped substitution is refused

#### Acceptance case: Unavailable history remains visible
- **GIVEN** historical release source is missing
- **WHEN** adoption reconstructs history
- **THEN** the release remains an Unknown node and no accretion edge is inferred across it

#### Acceptance case: Unsupported ecosystem respects enforcement policy
- **GIVEN** extraction is unsupported and policy requires PassDeclared
- **WHEN** observe and gate modes evaluate the same project
- **THEN** observe returns diagnostics with exit 0; gate refuses with exit 1

## Requirements

### Requirement: Wild adopt design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild adopt design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation
