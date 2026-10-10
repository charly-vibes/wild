---
id: wild.adopt
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
| history_reconstructed | invariant | `adopt(project) extracts each available historical release; missing source or extraction failure is preserved as an Unknown history node and cannot establish an accretion edge; version strings never establish edges` | [[wild.adopt]] |
| past_claims_audited | invariant | `each historical release reports declared version bump against computed verdict; disagreements are listed` | [[wild.adopt]] |
| adoption_levels_ordered | invariant | `levels are ordered observe < shadow < gate < native; a project enters level n+1 only from level n` | [[wild.adopt]] |
| observe_is_read_only | invariant | `level observe writes nothing to source, manifest, registry, or CI configuration` | [[wild.adopt]] |
| shadow_never_blocks | invariant | `level shadow emits verdicts but never changes a build exit status` | [[wild.adopt]] |
| gate_scoped_to_new_changes | invariant | `level gate rejects newly introduced breaks and expired baseline acknowledgements; baseline ids are immutable and cannot be reset implicitly by init, retries, or stepping down and up` | [[wild.adopt]] |
| baseline_ack_expires | invariant | `each baseline break has an owner, issue time, expiry, and stable finding id; default expiry is 30 days; renewal requires a signed reason and new expiry and appends an audit event rather than replacing history` | [[wild.adopt]] |
| first_run_is_baseline | invariant | `first enforcement atomically records a baseline digest, existing findings, and 30-day acknowledgements owned by the initiating identity; it tolerates existing breaks only after baseline persistence succeeds; persistence failure refuses enforcement activation` | [[wild.adopt]] |
| lock_import_lossless | invariant | `importing a host lockfile yields one lineage and hash per resolved dependency; unresolvable entries become Unknown, never dropped` | [[wild.adopt]] |
| demand_derived_from_code | invariant | `demand includes statically resolved usage and declared dynamic usage; unresolved reflection, plugins, or dynamic calls mark demand incomplete and block safe-removal and scoped-substitution claims; manual reductions require signed scoped expiring overrides and remain disclosed` | [[wild.adopt]] |
| safe_update_advice | invariant | `for a host version range, wild reports per candidate version whether demanded slots stay compatible; it never overrides the host resolver's choice; advice/check/observe never modify the manifest or host selection, and only explicit authorized update evaluation may apply a proposed manifest in an isolated workspace, with the host resolver selecting under that manifest` | [[wild.adopt]] |
| consumer_demand_trackable | invariant | `per slot, wild reports known consumers; removal_candidate(slot) is derived only when known demand is empty and all known demand manifests are complete and fresh; it is advisory and never authorizes removal within a stable lineage` | [[wild.adopt]] |
| integration_points_share_core | invariant | `CLI, CI action, pre-commit hook, and ecosystem plugins call one core and emit the same envelope` | [[wild.adopt]] |
| init_needs_no_edits | invariant | `init in a supported ecosystem produces extractor configuration, a baseline, and a CI hook without user edits` | [[wild.adopt]] |
| unsupported_ecosystem_degrades | invariant | `unsupported extraction yields Unknown assurance with scoped observations or metadata claims when available; observe and shadow succeed with diagnostics, while gate/native refuse any unmet required policy` | [[wild.adopt]] |
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
| gate | shadowed | gated | [[wild.adopt.gate_scoped_to_new_changes]] ∧ [[wild.adopt.first_run_is_baseline]] |
| go_native | gated | native | [[wild.adopt.init_needs_no_edits]] ∧ preserves wild-registry `ecosystem_untouched` and `sidecar_binds_artifact_digest` |
| step_down | gated | shadowed | [[wild.adopt.adoption_levels_ordered]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| history_graph_from_contracts | unit | [[wild.adopt.history_reconstructed]] | `git_history_with_mislabeled_semver()` | `lineage_graph == computed_accretion_graph` |
| semver_disagreement_listed | unit | [[wild.adopt.past_claims_audited]] | `release_tagged_patch_that_removes_a_slot()` | `audit lists the release` |
| level_skip_rejected | unit | [[wild.adopt.adoption_levels_ordered]] | `project_at_observe_requesting_gate()` | `transition == rejected` |
| observe_writes_nothing | unit | [[wild.adopt.observe_is_read_only]] | `repo_snapshot_before_and_after_observe()` | `snapshot(before) == snapshot(after)` |
| shadow_exit_status_unchanged | unit | [[wild.adopt.shadow_never_blocks]] | `build_with_a_computed_break_in_shadow()` | `exit_status == host_exit_status` |
| baseline_break_tolerated_new_rejected | unit | [[wild.adopt.gate_scoped_to_new_changes]] | `repo_with_old_break_then_new_break()` | `old == tolerated ∧ new == rejected` |
| expired_ack_rejects | unit | [[wild.adopt.baseline_ack_expires]] | `acknowledged_break_past_expiry()` | `check(ack) == rejected` |
| first_run_rejects_nothing_old | unit | [[wild.adopt.first_run_is_baseline]] | `repo_with_many_latent_breaks_first_run()` | `rejections == 0 ∧ baseline lists all` |
| lock_entries_all_accounted | unit | [[wild.adopt.lock_import_lossless]] | `lockfile_with_unresolvable_entry()` | `count(imported) == count(lock) ∧ entry.verdict == Unknown` |
| demand_matches_usage | unit | [[wild.adopt.demand_derived_from_code]] | `consumer_using_slots([a, b])` | `demand == {a, b}` |
| advice_leaves_resolver_alone | unit | [[wild.adopt.safe_update_advice]] | `range_with_one_incompatible_candidate()` | `advice flags candidate ∧ host_choice unchanged` |
| zero_demand_slot_removable | unit | [[wild.adopt.consumer_demand_trackable]] | `slot_with_no_known_consumers()` | `removal_candidate(slot) == true ∧ advisory_only ∧ no stored flag` |
| same_envelope_everywhere | unit | [[wild.adopt.integration_points_share_core]] | `same_change_via_cli_action_and_hook()` | `envelope(cli) == envelope(action) == envelope(hook)` |
| init_works_unedited | unit | [[wild.adopt.init_needs_no_edits]] | `fresh_repo_in_supported_ecosystem()` | `init leaves a runnable baseline and CI hook` |
| unsupported_degrades_not_errors | unit | [[wild.adopt.unsupported_ecosystem_degrades]] | `project_in_unsupported_language()` | `result.assurance == Unknown ∧ observe_exit_status == ok` |
| status_lists_tier_shares | unit | [[wild.adopt.adoption_progress_reported]] | `project_with_mixed_dependencies()` | `status lists level ∧ per-tier shares ∧ open acknowledgements` |

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

Scope reconciliation: advice/check/observe never modify the manifest or host selection. Only explicit update evaluation may apply an authorized proposed manifest in isolation; Cargo selects under that manifest.

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

### Requirement: Standalone local compatibility check

Wild SHALL check supplied base/candidate bundles for a named consumer scope without requiring registry publication, upstream contract adoption, historical reconstruction, or activation of adoption gate/native modes. It SHALL use v1 envelopes and the local-1 report contract, write only explicitly requested report artifacts, and preserve host manifests, lockfiles, source, and CI configuration.

#### Scenario: First result in an existing repository
- **GIVEN** supported local bundles and an explicit check request with no Wild registry or adoption history
- **WHEN** wild check evaluates the requested boundary
- **THEN** it reports structural assurance, law methods, scope, coverage, and stable diagnostics
- **AND** project files and adoption level remain unchanged

#### Scenario: A result separates policy from execution
- **GIVEN** a required analysis gap, a known structural break, and a malformed request in three separate runs
- **WHEN** checks finish
- **THEN** the local outcomes are respectively unknown, reject, and error with exits 1, 1, and 2
- **AND** all refuse policy acceptance without calling missing evidence a structural counterexample

### Requirement: Separate authored obligations from extracted facts

Wild SHALL accept human- or agent-authored obligation drafts using the same local-1 format and authority rules, store them separately from mined facts, and preserve accepted obligations when re-extracting candidate code. Authorship SHALL NOT raise assurance. Prose without an executable or structural predicate SHALL remain unverified, and contradictions with extracted facts SHALL remain visible.

#### Scenario: Regeneration cannot erase intent
- **GIVEN** an accepted law and a candidate that regenerates its contracts without that law
- **WHEN** the candidate is checked
- **THEN** the original law is still evaluated and the proposed deletion is reported separately

#### Scenario: Human and agent predicates receive equal checking
- **GIVEN** otherwise identical executable obligations with human and agent origin labels
- **WHEN** the same checker evaluates them on identical committed inputs
- **THEN** their assurance and law results match while provenance retains the different origins

### Requirement: Explicit authorized update planning

Wild SHALL provide a separate local update mode that records an exact target, original range, proposed manifest edit, base/configuration commitments, and allowed actions. Advice/check/observe SHALL retain their read-only host-selection behavior. Evaluation SHALL require external project authority bound to the plan before applying any edit in isolation; missing authority SHALL NOT be inferred from compatibility evidence.

#### Scenario: Plan without changing the application
- **GIVEN** a candidate excluded by the original Cargo range
- **WHEN** wild update plan runs
- **THEN** it writes only the requested proposal and identifies the exact range change and pending checks
- **AND** the original manifest, lockfile, source, and host selection are unchanged

#### Scenario: Candidate self-authorization fails
- **GIVEN** a candidate supplies an authority file not committed by the trusted invocation
- **WHEN** update evaluation starts
- **THEN** it refuses before applying the planned edit

### Requirement: Real host resolution and update delivery

Wild SHALL evaluate the authorized plan in isolation using actual Cargo resolution, inspect the selected target and complete dependency closure, build/test with a fixed lock, and evaluate protected obligations on those artifacts. It SHALL deliver a pinned diff only after every required check succeeds and output persistence completes. Missing required evidence SHALL remain unknown; runtime/platform/provenance/license/organization constraints SHALL NOT be silently relaxed with the version range.

#### Scenario: Compatible release outside the old range
- **GIVEN** a frozen registry target excluded by the original manifest that removes only an unused function in a completely supported scope
- **WHEN** an authorized manifest change resolves that exact target and all required closure, build, test, and contract checks pass
- **THEN** the output contains a delivered pinned direct-update diff and evidence for the actual artifacts
- **AND** the original worktree remains unchanged

#### Scenario: Permitted patch breaks a consumer
- **GIVEN** a patch release allowed by the old range removes a demanded function
- **WHEN** the actual selected target is evaluated
- **THEN** the update is refused with the violated demand and no delivered-update claim

#### Scenario: Cargo selects a different artifact
- **GIVEN** a plan for a specific source and release
- **WHEN** actual resolution selects a different source or release
- **THEN** evaluation refuses and records both requested and actual identities

#### Scenario: Environment constraint survives range relaxation
- **GIVEN** an otherwise compatible target requires an unsupported Rust version or violates a required provenance policy
- **WHEN** the manifest-range change is evaluated
- **THEN** the relevant constraint refuses delivery independently of compatibility

#### Scenario: Failed persistence or stale base cannot deliver
- **GIVEN** checks pass but the output cannot be durably written or an input commitment no longer matches
- **WHEN** delivery is finalized
- **THEN** the result is error or refusal with the cause and does not claim a delivered update

### Requirement: Direct updates and migrations remain distinct

Wild SHALL classify manifest/lock-only changes as direct updates and supplied consumer/adapter changes as migrations. Both SHALL satisfy protected intended outcomes. Authorized obligation changes SHALL be recorded as intentional transitions and SHALL NOT count as backward-compatible direct updates. The first implementation SHALL accept supplied migration patches without requiring automatic migration generation.

#### Scenario: Consumer repair is a migration
- **GIVEN** an update passes only after a supplied consumer-code patch
- **WHEN** the original intended outcomes and new closure pass validation
- **THEN** the result includes that patch and reports migration rather than direct compatibility

#### Scenario: Removed assertion is not preserved behavior
- **GIVEN** a migration deletes a protected consumer test or obligation
- **WHEN** evaluation runs without a separately authorized intent transition
- **THEN** the original obligation remains required and the deletion cannot make delivery pass

