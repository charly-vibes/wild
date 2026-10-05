---
id: spec
kind: intent
statement: THE wild tier pipeline SHALL decide each revision's verdict through checks ordered by cost, where exact deterministic tiers can reject and probabilistic tiers can only raise confidence.
---

# Wild tiers

Five tiers in cost order: identity, shape, laws, evidence, attestation. The first three are pure and exact; evidence is statistical; attestation is human, signed, and expiring. Verdicts form a lattice, and policy states the minimum tier a context requires.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| fail_fast_ordering | invariant | `tiers run in order identity < shape < laws < evidence < attestation; a run stops at the first Reject` | [[spec]] |
| exact_tiers_pure | invariant | `tiers identity, shape, and laws are pure: the same inputs give the same verdict, with no network or clock access` | [[spec]] |
| verdict_lattice | invariant | `verdicts form a lattice Reject < Unknown < PassDeclared < PassLawChecked < PassObserved with meet and join` | [[spec]] |
| policy_names_min_tier | invariant | `each context (publish, deploy, adopt) names the minimum tier it requires; a verdict below it is refused` | [[spec]] |
| rejection_explains | invariant | `a Reject names the tier, the slot or law, and the rule that failed` | [[spec]] |
| laws_cumulative | invariant | `laws(v') ⊇ ⋃ laws(ancestors); every ancestor law passes against the v' implementation` | [[spec]] |
| law_runs_deterministic | invariant | `the same contract, implementation, and seed give the same law result; seeds are recorded in the report` | [[spec]] |
| evidence_cannot_override_exact | invariant | `evidence may raise a Pass confidence; it never turns a Reject from an exact tier into Pass` | [[spec]] |
| evidence_confidence_conservative | advisory | `reported confidence is the minimum over contributing observations, never a product` | [[spec]] |
| contradiction_triggers_repair | invariant | `observed behavior contradicting the declared contract creates a repair draft; the contract is never edited silently` | [[spec]] |
| attestation_scoped | invariant | `an attestation names its signer, its scope (lineage and slots), and its claim` | [[spec]] |
| attestation_expiring | invariant | `an attestation carries an expiry; an expired attestation counts as Unknown` | [[spec]] |
| verdict_cache_keyed | invariant | `cached verdicts are keyed by old hash, new hash, checker version, and policy` | [[spec]] |
| verdict_recorded_immutable | invariant | `a recorded verdict for a key is never rewritten; a new checker version records a new verdict` | [[spec]] |

## Model

### States

- `draft`
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
| identify | draft | identified | [[spec.exact_tiers_pure]] |
| shape_check | identified | shape_checked | [[spec.fail_fast_ordering]] ∧ preserves wild-core `accretion_monotone` |
| law_check | shape_checked | law_checked | [[spec.laws_cumulative]] |
| publish | law_checked | published | [[spec.policy_names_min_tier]] ∧ requires wild-registry `registry_append_only` |
| observe | published | observed | [[spec.evidence_cannot_override_exact]] |
| attest | observed | attested | [[spec.attestation_expiring]] |
| repair | observed | draft | [[spec.contradiction_triggers_repair]] |
| reject_identity | identified | rejected | [[spec.rejection_explains]] |
| reject_shape | shape_checked | rejected | [[spec.rejection_explains]] |
| reject_laws | law_checked | rejected | [[spec.rejection_explains]] |
| revise | rejected | draft | [[spec.verdict_recorded_immutable]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| first_reject_stops_run | unit | [[spec.fail_fast_ordering]] | `revision_failing_identity_and_laws()` | `tiers_run == [identity] ∧ verdict == Reject` |
| exact_tiers_ignore_side_inputs | unit | [[spec.exact_tiers_pure]] | `same_inputs_with_varied_clock_and_network()` | `verdict(a) == verdict(b)` |
| verdict_lattice_laws | law | [[spec.verdict_lattice]] | `three_arbitrary_verdicts()` | **identity:** `meet(v, PassObserved) == v` **associativity:** `meet(meet(a, b), c) == meet(a, meet(b, c))` |
| below_policy_refused | unit | [[spec.policy_names_min_tier]] | `verdict_PassDeclared_under_policy_requiring_laws()` | `decision == refused` |
| reject_names_rule | unit | [[spec.rejection_explains]] | `arbitrary_rejected_revision()` | `report has tier ∧ slot_or_law ∧ rule` |
| ancestor_law_failure_rejected | unit | [[spec.laws_cumulative]] | `revision_violating_an_ancestor_law()` | `law_check == failed` |
| law_run_reproducible | unit | [[spec.law_runs_deterministic]] | `(contract, impl, seed)` run twice | `run(a) == run(b)` |
| evidence_never_overrides_reject | unit | [[spec.evidence_cannot_override_exact]] | `shape_Reject_plus_clean_traffic_replay()` | `verdict == Reject` |
| confidence_is_minimum | unit | [[spec.evidence_confidence_conservative]] | `observations_with_confidences([0.99, 0.90])` | `confidence == 0.90` |
| contradiction_creates_draft | unit | [[spec.contradiction_triggers_repair]] | `observed_behavior_outside_declared_contract()` | `repair_draft_created ∧ contract_unchanged` |
| attestation_without_scope_rejected | unit | [[spec.attestation_scoped]] | `attestation_missing_scope()` | `check(a) == failed` |
| expired_attestation_is_unknown | unit | [[spec.attestation_expiring]] | `attestation_with_past_expiry()` | `verdict(a) == Unknown` |
| cache_key_includes_checker | unit | [[spec.verdict_cache_keyed]] | `same_pair_under_two_checker_versions()` | `keys differ ∧ no cross-hit` |
| recorded_verdict_unchanged | unit | [[spec.verdict_recorded_immutable]] | `verdict_recorded_then_rerun_under_new_checker()` | `old record unchanged ∧ new record appended` |

## Notes

Evidence is graded because failures are correlated, so confidence is the minimum, never a product. Simulation round 1 (12 scenarios): six shape breaks were caught at tier 1, two behavior changes at tier 2 through laws, one at tier 3 through canary replay, one safe input widening was correctly passed, and two undeclared behavior changes escaped. Escapes of undeclared behavior are the known residual of this design.
