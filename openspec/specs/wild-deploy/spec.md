---
id: spec
kind: intent
statement: THE wild deployer SHALL decide, from declared floors and observed live revisions, when each service may deploy, so that continuous deployment needs no manual ordering or lockstep release.
---

# Wild deploy

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

Rollout rules on top of published revisions. Accretion makes old consumers safe against new providers, but a consumer that starts using a new slot needs its provider live first. This spec turns that into a computed gate, plus safe rollback and lineage retirement.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| deploy_requires_published_revision | invariant | `a revision is deployable only if it is published in the registry and passed tiers identity, shape, and laws` | [[spec]] |
| floor_declared | invariant | `for each demanded provider on a totally ordered accepted ancestry, floor is the least revision covering demand; incomparable covering minima require an explicit pinned covering revision and cannot be represented by a guessed scalar floor` | [[spec]] |
| provider_live_before_consumer | invariant | `a consumer may deploy only when every provider revision reachable by its traffic satisfies its floor, all required policy passes, and a coordination lease protects the live snapshot; one new canary instance does not satisfy the floor for traffic reaching old instances` | [[spec]] |
| gate_order_derived | invariant | `a deploy plan orders services by a topological order of floor edges; manual ordering is not accepted` | [[spec]] |
| floor_cycle_rejected | invariant | `only unsatisfied floor prerequisites create ordering edges; existing dependency cycles whose floors are already satisfied are allowed; an unsatisfied prerequisite cycle is refused with members listed and simultaneous deployment is not offered` | [[spec]] |
| gate_decision_pure | invariant | `the gate is a pure function of floors, routing, live snapshot, policy, coordination generation, and explicit evaluation time; it performs no clock or network reads` | [[spec]] |
| live_state_fresh | invariant | `reports include observed_at, ttl_seconds, generation, and every traffic-reachable revision; at evaluation_time ≥ observed_at + ttl_seconds or on missing/future-dated reports state is Unknown and blocks; default ttl is 60 seconds` | [[spec]] |
| rolling_overlap_safe | invariant | `during a roll, old and new revisions serve concurrently only when the new revision accretes the old one; a non-accretion is never rolled in place` | [[spec]] |
| lineages_served_concurrently | invariant | `a break ships as a new lineage while the old lineage keeps serving until retirement` | [[spec]] |
| retire_on_zero_demand | invariant | `retirement requires empty known demand, fresh complete consumer reports, zero routed traffic, and a policy grace period (default seven days) continuously satisfied; missing reports or renewed demand restart the grace period; registry bytes remain` | [[spec]] |
| canary_traffic_bounded | invariant | `canary traffic share never exceeds the policy maximum` | [[spec]] |
| evidence_required_to_promote | invariant | `promotion requires every binding to satisfy the v1 policy, fresh complete live state, and a valid coordination lease; structural Reject or relevant law counterexample is never promoted` | [[spec]] |
| rollback_respects_floors | invariant | `provider rollback checks floors of all live and in-flight consumers plus irreversible writes under the same coordination lease; generation change or lease loss aborts and requires revalidation; otherwise violating consumers roll back first` | [[spec]] |
| irreversible_edges_declared | invariant | `irreversible writers persist a monotone first-write barrier before acknowledging such writes; after the barrier rollback past it is refused, including canary and rolling aborts; unknown barrier status fails closed` | [[spec]] |
| emergency_override_recorded | invariant | `an authorized override names exact overridable policy findings, signer, reason, and expiry in a log entry; structural Reject, Unknown reachability, lease loss, and irreversible-write barriers are never overridable` | [[spec]] |
| deploy_envelope | invariant | `every deploy command emits an envelope with stage, revision hashes, and gate verdict` | [[spec]] |
| stage_durations_reported | advisory | `each deployment reports time spent per stage from commit to live` | [[spec]] |
| deploy_impact_estimated | advisory | `before the gate runs, the plan lists the known consumers each deployment affects` | [[spec]] |

## Model

### States

- `committed`
- `checked`
- `gated`
- `canary`
- `rolling`
- `live`
- `rolled_back`
- `contracted`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| check | committed | checked | [[spec.deploy_requires_published_revision]] ∧ requires wild-registry `registry_append_only` |
| gate | checked | gated | [[spec.provider_live_before_consumer]] ∧ [[spec.gate_decision_pure]] |
| start_canary | gated | canary | [[spec.canary_traffic_bounded]] |
| promote | canary | rolling | [[spec.evidence_required_to_promote]] |
| finish_roll | rolling | live | [[spec.rolling_overlap_safe]] |
| abort_canary | canary | rolled_back | [[spec.rollback_respects_floors]] ∧ [[spec.irreversible_edges_declared]] |
| abort_roll | rolling | rolled_back | [[spec.rollback_respects_floors]] ∧ [[spec.irreversible_edges_declared]] |
| rollback_live | live | rolled_back | [[spec.rollback_respects_floors]] ∧ [[spec.irreversible_edges_declared]] |
| retry | rolled_back | committed | [[spec.deploy_requires_published_revision]] |
| contract | live | contracted | [[spec.retire_on_zero_demand]] ∧ [[spec.live_state_fresh]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| unpublished_revision_not_deployed | unit | [[spec.deploy_requires_published_revision]] | `revision_absent_from_registry()` | `deploy == rejected` |
| floor_is_least_covering_revision | unit | [[spec.floor_declared]] | `lineage_chain_with_demand()` | `floor == min(r in chain where demand ⊆ provides(r))` |
| consumer_waits_for_provider | unit | [[spec.provider_live_before_consumer]] | `consumer_floor_above_live_provider()` | `gate == blocked` |
| plan_order_is_topological | unit | [[spec.gate_order_derived]] | `random_dag_of_floor_edges()` | `for each edge (p, c): index(p) < index(c)` |
| cycle_reported_with_members | unit | [[spec.floor_cycle_rejected]] | `floor_edges_forming_a_cycle()` | `plan == rejected ∧ members listed` |
| gate_ignores_clock | unit | [[spec.gate_decision_pure]] | `same_explicit_evaluation_inputs_with_varied_host_clock()` | `gate(a) == gate(b)` |
| stale_report_blocks | unit | [[spec.live_state_fresh]] | `live_report_past_ttl()` | `gate == blocked ∧ state == Unknown` |
| accretion_roll_has_no_failures | unit | [[spec.rolling_overlap_safe]] | `rolling_update_of_accretion_pair()` | `no contract-incompatibility failures on the declared demand domain; unrelated operational failures excluded` |
| lineages_overlap_until_retired | unit | [[spec.lineages_served_concurrently]] | `break_shipped_as_new_lineage()` | `served(old) ∧ served(new) until retire` |
| retire_blocked_while_demanded | unit | [[spec.retire_on_zero_demand]] | `old_lineage_with_one_known_consumer()` | `retire == rejected` |
| canary_share_capped | unit | [[spec.canary_traffic_bounded]] | `canary_request_above_policy_max()` | `share ≤ policy_max` |
| exact_reject_not_promotable | unit | [[spec.evidence_required_to_promote]] | `shape_Reject_with_clean_canary()` | `promote == rejected` |
| rollback_below_floor_blocked | unit | [[spec.rollback_respects_floors]] | `provider_rollback_below_a_live_floor()` | `rollback == blocked ∧ consumers listed first` |
| irreversible_rollback_blocked | unit | [[spec.irreversible_edges_declared]] | `irreversible_revision_after_first_write()` | `rollback == rejected` |
| override_needs_expiry | unit | [[spec.emergency_override_recorded]] | `override_without_expiry()` | `override == rejected` |
| envelope_has_stage_and_hashes | unit | [[spec.deploy_envelope]] | `arbitrary_deploy_result()` | `envelope has stage ∧ revision hashes ∧ gate verdict` |
| durations_listed_per_stage | unit | [[spec.stage_durations_reported]] | `completed_deployment()` | `report lists duration for each stage` |
| impact_lists_consumers | unit | [[spec.deploy_impact_estimated]] | `plan_for_provider_with_known_consumers()` | `plan lists affected consumers before gate` |

## Notes

Simulation findings behind these rules (toy model, assumed durations): an additive roll of 20 instances produced no failed requests, an uncoordinated break failed roughly a third of calls hitting the changed slot, manual expand/contract took about four working days end to end, and only a small minority of random deploy orders were safe, hence the derived order. Median lead time matched a modern canary pipeline (about 0.8 hours); the gains were in the tail (waiting on consumers) and in user-impact minutes (about 2.4 times lower than the canary baseline across nine sensitivity runs). Escaped undeclared-behavior defects occurred at the same rate as in the canary baseline.

Known limits: the gate trusts the live-revision reports it receives; stale or missing reports fail closed. Retirement is only safe against known consumers. Data written by a new revision is outside accretion unless declared irreversible.

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Deploy requires published revision

The system SHALL satisfy `deploy_requires_published_revision` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Unpublished revision not deployed
- **GIVEN** the fixture domain `revision_absent_from_registry()`
- **WHEN** the `deploy_requires_published_revision` check runs
- **THEN** `deploy == rejected`

### Rule: Floor declared

The system SHALL satisfy `floor_declared` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Floor is least covering revision
- **GIVEN** the fixture domain `lineage_chain_with_demand()`
- **WHEN** the `floor_declared` check runs
- **THEN** `floor == min(r in chain where demand ⊆ provides(r))`

### Rule: Provider live before consumer

The system SHALL satisfy `provider_live_before_consumer` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Consumer waits for provider
- **GIVEN** the fixture domain `consumer_floor_above_live_provider()`
- **WHEN** the `provider_live_before_consumer` check runs
- **THEN** `gate == blocked`

### Rule: Gate order derived

The system SHALL satisfy `gate_order_derived` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Plan order is topological
- **GIVEN** the fixture domain `random_dag_of_floor_edges()`
- **WHEN** the `gate_order_derived` check runs
- **THEN** `for each edge (p, c): index(p) < index(c)`

### Rule: Floor cycle rejected

The system SHALL satisfy `floor_cycle_rejected` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Cycle reported with members
- **GIVEN** the fixture domain `floor_edges_forming_a_cycle()`
- **WHEN** the `floor_cycle_rejected` check runs
- **THEN** `plan == rejected ∧ members listed`

### Rule: Gate decision pure

The system SHALL satisfy `gate_decision_pure` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Gate ignores clock
- **GIVEN** the fixture domain `same_explicit_evaluation_inputs_with_varied_host_clock()`
- **WHEN** the `gate_decision_pure` check runs
- **THEN** `gate(a) == gate(b)`

### Rule: Live state fresh

The system SHALL satisfy `live_state_fresh` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Stale report blocks
- **GIVEN** the fixture domain `live_report_past_ttl()`
- **WHEN** the `live_state_fresh` check runs
- **THEN** `gate == blocked ∧ state == Unknown`

### Rule: Rolling overlap safe

The system SHALL satisfy `rolling_overlap_safe` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Accretion roll has no failures
- **GIVEN** the fixture domain `rolling_update_of_accretion_pair()`
- **WHEN** the `rolling_overlap_safe` check runs
- **THEN** `no contract-incompatibility failures on the declared demand domain; unrelated operational failures excluded`

### Rule: Lineages served concurrently

The system SHALL satisfy `lineages_served_concurrently` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Lineages overlap until retired
- **GIVEN** the fixture domain `break_shipped_as_new_lineage()`
- **WHEN** the `lineages_served_concurrently` check runs
- **THEN** `served(old) ∧ served(new) until retire`

### Rule: Retire on zero demand

The system SHALL satisfy `retire_on_zero_demand` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Retire blocked while demanded
- **GIVEN** the fixture domain `old_lineage_with_one_known_consumer()`
- **WHEN** the `retire_on_zero_demand` check runs
- **THEN** `retire == rejected`

### Rule: Canary traffic bounded

The system SHALL satisfy `canary_traffic_bounded` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Canary share capped
- **GIVEN** the fixture domain `canary_request_above_policy_max()`
- **WHEN** the `canary_traffic_bounded` check runs
- **THEN** `share ≤ policy_max`

### Rule: Evidence required to promote

The system SHALL satisfy `evidence_required_to_promote` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Exact reject not promotable
- **GIVEN** the fixture domain `shape_Reject_with_clean_canary()`
- **WHEN** the `evidence_required_to_promote` check runs
- **THEN** `promote == rejected`

### Rule: Rollback respects floors

The system SHALL satisfy `rollback_respects_floors` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Rollback below floor blocked
- **GIVEN** the fixture domain `provider_rollback_below_a_live_floor()`
- **WHEN** the `rollback_respects_floors` check runs
- **THEN** `rollback == blocked ∧ consumers listed first`

### Rule: Irreversible edges declared

The system SHALL satisfy `irreversible_edges_declared` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Irreversible rollback blocked
- **GIVEN** the fixture domain `irreversible_revision_after_first_write()`
- **WHEN** the `irreversible_edges_declared` check runs
- **THEN** `rollback == rejected`

### Rule: Emergency override recorded

The system SHALL satisfy `emergency_override_recorded` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Override needs expiry
- **GIVEN** the fixture domain `override_without_expiry()`
- **WHEN** the `emergency_override_recorded` check runs
- **THEN** `override == rejected`

### Rule: Deploy envelope

The system SHALL satisfy `deploy_envelope` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Envelope has stage and hashes
- **GIVEN** the fixture domain `arbitrary_deploy_result()`
- **WHEN** the `deploy_envelope` check runs
- **THEN** `envelope has stage ∧ revision hashes ∧ gate verdict`

### Rule: Stage durations reported

The system SHALL satisfy `stage_durations_reported` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Durations listed per stage
- **GIVEN** the fixture domain `completed_deployment()`
- **WHEN** the `stage_durations_reported` check runs
- **THEN** `report lists duration for each stage`

### Rule: Deploy impact estimated

The system SHALL satisfy `deploy_impact_estimated` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Impact lists consumers
- **GIVEN** the fixture domain `plan_for_provider_with_known_consumers()`
- **WHEN** the `deploy_impact_estimated` check runs
- **THEN** `plan lists affected consumers before gate`

#### Acceptance case: Mixed rollout does not satisfy a new floor
- **GIVEN** a provider routes 90 percent of requests to revision r1 and 10 percent to r2; a consumer requires a slot first provided by r2
- **WHEN** the consumer deploy gate runs
- **THEN** it blocks until all reachable routes cover the floor or the consumer is pinned exclusively to covering instances

#### Acceptance case: Clock is an explicit evaluation input
- **GIVEN** a report observed at 15:00:00Z has ttl_seconds 60
- **WHEN** the pure gate receives evaluation time 15:01:00Z
- **THEN** the report is Unknown and deployment blocks regardless of the host clock

#### Acceptance case: Concurrent rollback invalidates the gate
- **GIVEN** a gate was accepted at coordination generation 12
- **WHEN** provider rollback advances the generation before consumer route activation
- **THEN** activation aborts and revalidates; the old approval cannot authorize it

#### Acceptance case: Canary writes can prevent abort rollback
- **GIVEN** a canary persisted an irreversible first-write barrier
- **WHEN** the canary attempts rollback below the barrier
- **THEN** rollback refuses just as it would after full promotion

#### Acceptance case: Satisfied dependency cycle does not block rollout
- **GIVEN** two services depend on each other and both live providers already cover every floor
- **WHEN** the deploy plan computes unsatisfied prerequisites
- **THEN** it has no cyclic ordering edges and can proceed subject to policy and lease

## Requirements

### Requirement: Prototype deployment simulation

The prototype deployment simulation SHALL run its overlap, deploy-order, pipeline-sensitivity, and checker-cost models, so the assumptions behind the design remain runnable while `wild` itself is unbuilt; this gate does not establish runtime floor, lease, TTL, or rollback conformance.

#### Scenario: Prototype deployment simulation runs clean
- **GIVEN** the deployment scenarios encoded in `prototype/wild_cd_sim.py`
- **WHEN** the deployment simulation runs
- **THEN** it exits 0 and produces non-empty output
- **AND** the gate executes this behavior as a declared contract test

### Requirement: Wild deploy design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild deploy design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation
