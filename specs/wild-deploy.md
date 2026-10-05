---
id: wild.deploy
kind: intent
statement: THE wild deployer SHALL decide, from declared floors and observed live revisions, when each service may deploy, so that continuous deployment needs no manual ordering or lockstep release.
---

# Wild deploy

Rollout rules on top of published revisions. Accretion makes old consumers safe against new providers, but a consumer that starts using a new slot needs its provider live first. This spec turns that into a computed gate, plus safe rollback and lineage retirement.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| deploy_requires_published_revision | invariant | `a revision is deployable only if it is published in the registry and passed tiers identity, shape, and laws` | [[wild.deploy]] |
| floor_declared | invariant | `for each provider a consumer demands, its manifest records floor = least revision in the lineage whose provides cover the demand` | [[wild.deploy]] |
| provider_live_before_consumer | invariant | `a consumer revision may deploy iff for every provider: live(provider) ⪰ floor` | [[wild.deploy]] |
| gate_order_derived | invariant | `a deploy plan orders services by a topological order of floor edges; manual ordering is not accepted` | [[wild.deploy]] |
| floor_cycle_rejected | invariant | `a cycle among floor edges is rejected and its members listed; simultaneous deployment is not offered` | [[wild.deploy]] |
| gate_decision_pure | invariant | `the gate verdict is a pure function of floors and live revisions, with no clock or network input` | [[wild.deploy]] |
| live_state_fresh | invariant | `a live-revision report older than its ttl counts as Unknown, and Unknown blocks the gate (fail closed)` | [[wild.deploy]] |
| rolling_overlap_safe | invariant | `during a roll, old and new revisions serve concurrently only when the new revision accretes the old one; a non-accretion is never rolled in place` | [[wild.deploy]] |
| lineages_served_concurrently | invariant | `a break ships as a new lineage while the old lineage keeps serving until retirement` | [[wild.deploy]] |
| retire_on_zero_demand | invariant | `an old lineage retires only when known demand is empty and a grace period has elapsed; retirement never deletes registry revisions` | [[wild.deploy]] |
| canary_traffic_bounded | invariant | `canary traffic share never exceeds the policy maximum` | [[wild.deploy]] |
| evidence_required_to_promote | invariant | `promotion requires a verdict at or above the policy minimum tier; a Reject from an exact tier is never promoted` | [[wild.deploy]] |
| rollback_respects_floors | invariant | `rolling a provider back to revision r is permitted only if r ⪰ the floor of every live consumer; otherwise those consumers roll back first` | [[wild.deploy]] |
| irreversible_edges_declared | invariant | `a revision that writes data older revisions cannot read declares itself irreversible; after its first write, rollback past it is rejected` | [[wild.deploy]] |
| emergency_override_recorded | invariant | `a manual gate override carries signer, reason, and expiry, and is appended to the registry log` | [[wild.deploy]] |
| deploy_envelope | invariant | `every deploy command emits an envelope with stage, revision hashes, and gate verdict` | [[wild.deploy]] |
| stage_durations_reported | advisory | `each deployment reports time spent per stage from commit to live` | [[wild.deploy]] |
| deploy_impact_estimated | advisory | `before the gate runs, the plan lists the known consumers each deployment affects` | [[wild.deploy]] |

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
| check | committed | checked | [[wild.deploy.deploy_requires_published_revision]] ∧ [[wild.registry.registry_append_only]] |
| gate | checked | gated | [[wild.deploy.provider_live_before_consumer]] ∧ [[wild.deploy.gate_decision_pure]] |
| start_canary | gated | canary | [[wild.deploy.canary_traffic_bounded]] |
| promote | canary | rolling | [[wild.deploy.evidence_required_to_promote]] |
| finish_roll | rolling | live | [[wild.deploy.rolling_overlap_safe]] |
| abort_canary | canary | rolled_back | [[wild.deploy.rollback_respects_floors]] |
| abort_roll | rolling | rolled_back | [[wild.deploy.rollback_respects_floors]] |
| rollback_live | live | rolled_back | [[wild.deploy.rollback_respects_floors]] ∧ [[wild.deploy.irreversible_edges_declared]] |
| retry | rolled_back | committed | [[wild.deploy.deploy_requires_published_revision]] |
| contract | live | contracted | [[wild.deploy.retire_on_zero_demand]] ∧ [[wild.deploy.live_state_fresh]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| unpublished_revision_not_deployed | unit | [[wild.deploy.deploy_requires_published_revision]] | `revision_absent_from_registry()` | `deploy == rejected` |
| floor_is_least_covering_revision | unit | [[wild.deploy.floor_declared]] | `lineage_chain_with_demand()` | `floor == min(r in chain where demand ⊆ provides(r))` |
| consumer_waits_for_provider | unit | [[wild.deploy.provider_live_before_consumer]] | `consumer_floor_above_live_provider()` | `gate == blocked` |
| plan_order_is_topological | unit | [[wild.deploy.gate_order_derived]] | `random_dag_of_floor_edges()` | `for each edge (p, c): index(p) < index(c)` |
| cycle_reported_with_members | unit | [[wild.deploy.floor_cycle_rejected]] | `floor_edges_forming_a_cycle()` | `plan == rejected ∧ members listed` |
| gate_ignores_clock | unit | [[wild.deploy.gate_decision_pure]] | `same_state_with_varied_clock()` | `gate(a) == gate(b)` |
| stale_report_blocks | unit | [[wild.deploy.live_state_fresh]] | `live_report_past_ttl()` | `gate == blocked ∧ state == Unknown` |
| accretion_roll_has_no_failures | unit | [[wild.deploy.rolling_overlap_safe]] | `rolling_update_of_accretion_pair()` | `failed_requests == 0` |
| lineages_overlap_until_retired | unit | [[wild.deploy.lineages_served_concurrently]] | `break_shipped_as_new_lineage()` | `served(old) ∧ served(new) until retire` |
| retire_blocked_while_demanded | unit | [[wild.deploy.retire_on_zero_demand]] | `old_lineage_with_one_known_consumer()` | `retire == rejected` |
| canary_share_capped | unit | [[wild.deploy.canary_traffic_bounded]] | `canary_request_above_policy_max()` | `share ≤ policy_max` |
| exact_reject_not_promotable | unit | [[wild.deploy.evidence_required_to_promote]] | `shape_Reject_with_clean_canary()` | `promote == rejected` |
| rollback_below_floor_blocked | unit | [[wild.deploy.rollback_respects_floors]] | `provider_rollback_below_a_live_floor()` | `rollback == blocked ∧ consumers listed first` |
| irreversible_rollback_blocked | unit | [[wild.deploy.irreversible_edges_declared]] | `irreversible_revision_after_first_write()` | `rollback == rejected` |
| override_needs_expiry | unit | [[wild.deploy.emergency_override_recorded]] | `override_without_expiry()` | `override == rejected` |
| envelope_has_stage_and_hashes | unit | [[wild.deploy.deploy_envelope]] | `arbitrary_deploy_result()` | `envelope has stage ∧ revision hashes ∧ gate verdict` |
| durations_listed_per_stage | unit | [[wild.deploy.stage_durations_reported]] | `completed_deployment()` | `report lists duration for each stage` |
| impact_lists_consumers | unit | [[wild.deploy.deploy_impact_estimated]] | `plan_for_provider_with_known_consumers()` | `plan lists affected consumers before gate` |

## Notes

Simulation findings behind these rules (toy model, assumed durations): an additive roll of 20 instances produced no failed requests, an uncoordinated break failed roughly a third of calls hitting the changed slot, manual expand/contract took about four working days end to end, and only a small minority of random deploy orders were safe, hence the derived order. Median lead time matched a modern canary pipeline (about 0.8 hours); the gains were in the tail (waiting on consumers) and in user-impact minutes (about 2.4 times lower than the canary baseline across nine sensitivity runs). Escaped undeclared-behavior defects occurred at the same rate as in the canary baseline.

Known limits: the gate trusts the live-revision reports it receives; stale or missing reports fail closed. Retirement is only safe against known consumers. Data written by a new revision is outside accretion unless declared irreversible.
