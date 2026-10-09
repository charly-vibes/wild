---
id: wild.tiers
kind: intent
statement: THE wild tier pipeline SHALL decide each revision's verdict through checks ordered by cost, where structural checks can reject, executable law checks disclose their method, and observations and attestations never override structural rejection.
---

# Wild tiers

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. Shared wire formats and decision rules are defined in [wild v1 formats](../../../docs/wild-formats-v1.md) and [the v1 schema](../../../schemas/wild-v1.schema.json).

Checks run in cost order: identity, shape, laws, evidence, attestation. Identity and shape decide declared structure. Law results distinguish proof, exhaustive finite enumeration, and sampling; a passing sample proves only that sample. Evidence and signed attestations are separate scoped claims. The verdict product and policy evaluation are defined in `docs/wild-formats-v1.md`.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| fail_fast_ordering | invariant | `tiers run in order identity < shape < laws < evidence < attestation; a run stops at the first Reject` | [[wild.tiers]] |
| exact_tiers_pure | invariant | `identity and shape are pure functions of canonical contracts and checker version; law evaluation is reproducible only with the implementation digest, harness digest, seed, fixture digests, and resource limits in the v1 bundle` | [[wild.tiers]] |
| verdict_lattice | invariant | `structural assurance forms the lattice Reject < Unknown < PassDeclared; executable laws, observations, and attestations are separate scoped records; assembly assurance is the structural meet and policy checks every binding as defined in docs/wild-formats-v1.md` | [[wild.tiers]] |
| policy_names_min_tier | invariant | `each context has a v1 policy naming structural floor, allowed law methods, required law ids, evidence thresholds, and any required attestations; missing or failed required checks refuse the operation` | [[wild.tiers]] |
| rejection_explains | invariant | `a Reject names the tier, the slot or law, and the rule that failed` | [[wild.tiers]] |
| laws_cumulative | invariant | `laws(v') ⊇ ⋃ laws(ancestors); every ancestor law passes against the v' implementation` | [[wild.tiers]] |
| law_runs_deterministic | invariant | `the same complete harness inputs yield the same law result; seed, implementation and harness digests, fixtures, budgets, and method are recorded; timeout, crash, or nondeterminism is inconclusive and cannot pass required policy` | [[wild.tiers]] |
| evidence_cannot_override_exact | invariant | `observations may add scoped evidence to a structural Pass; they cannot override a structural Reject or a law counterexample` | [[wild.tiers]] |
| evidence_confidence_conservative | advisory | `reported confidence is the minimum over contributing observations, never a product` | [[wild.tiers]] |
| contradiction_triggers_repair | invariant | `observed behavior contradicting the declared contract creates a repair draft; the contract is never edited silently` | [[wild.tiers]] |
| attestation_scoped | invariant | `an attestation names its signer, its scope (lineage and slots), and its claim` | [[wild.tiers]] |
| attestation_expiring | invariant | `an attestation carries issue time and expiry and is bound to artifact and contract digests; at evaluation_time ≥ expiry the attestation status is Unknown while independent checks remain unchanged` | [[wild.tiers]] |
| verdict_cache_keyed | invariant | `structural cache keys include old and new contract hashes and checker version; law cache keys also include implementation, harness, fixtures, seed, method, and budgets; policy evaluation includes demand, policy digest, evidence digests, trust roots, and evaluation time and is never reused past claim expiry` | [[wild.tiers]] |
| verdict_recorded_immutable | invariant | `recorded check results are immutable; new inputs append new records; current policy decisions are recomputed from those records and claim validity at evaluation time` | [[wild.tiers]] |

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
| identify | draft | identified | [[wild.tiers.exact_tiers_pure]] |
| shape_check | identified | shape_checked | [[wild.tiers.fail_fast_ordering]] ∧ preserves wild-core `accretion_monotone` |
| law_check | shape_checked | law_checked | [[wild.tiers.laws_cumulative]] |
| publish | law_checked | published | [[wild.tiers.policy_names_min_tier]] ∧ requires wild-registry `registry_append_only` |
| observe | published | observed | [[wild.tiers.evidence_cannot_override_exact]] |
| attest | observed | attested | [[wild.tiers.attestation_expiring]] |
| repair | observed | draft | [[wild.tiers.contradiction_triggers_repair]] |
| reject_identity | identified | rejected | [[wild.tiers.rejection_explains]] |
| reject_shape | shape_checked | rejected | [[wild.tiers.rejection_explains]] |
| reject_laws | law_checked | rejected | [[wild.tiers.rejection_explains]] |
| revise | rejected | draft | [[wild.tiers.verdict_recorded_immutable]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| first_reject_stops_run | unit | [[wild.tiers.fail_fast_ordering]] | `revision_failing_identity_and_laws()` | `tiers_run == [identity] ∧ verdict == Reject` |
| exact_tiers_ignore_side_inputs | unit | [[wild.tiers.exact_tiers_pure]] | `same_inputs_with_varied_clock_and_network()` | `verdict(a) == verdict(b)` |
| verdict_lattice_laws | law | [[wild.tiers.verdict_lattice]] | `three_arbitrary_verdicts()` | **identity:** `meet(v, PassDeclared) == v` **associativity:** `meet(meet(a, b), c) == meet(a, meet(b, c))` |
| below_policy_refused | unit | [[wild.tiers.policy_names_min_tier]] | `verdict_PassDeclared_under_policy_requiring_laws()` | `decision == refused` |
| reject_names_rule | unit | [[wild.tiers.rejection_explains]] | `arbitrary_rejected_revision()` | `report has tier ∧ slot_or_law ∧ rule` |
| ancestor_law_failure_rejected | unit | [[wild.tiers.laws_cumulative]] | `revision_violating_an_ancestor_law()` | `law_check == failed` |
| law_run_reproducible | unit | [[wild.tiers.law_runs_deterministic]] | `(contract, impl, seed)` run twice | `run(a) == run(b)` |
| evidence_never_overrides_reject | unit | [[wild.tiers.evidence_cannot_override_exact]] | `shape_Reject_plus_clean_traffic_replay()` | `verdict == Reject` |
| confidence_is_minimum | unit | [[wild.tiers.evidence_confidence_conservative]] | `observations_with_confidences([0.99, 0.90])` | `confidence == 0.90` |
| contradiction_creates_draft | unit | [[wild.tiers.contradiction_triggers_repair]] | `observed_behavior_outside_declared_contract()` | `repair_draft_created ∧ contract_unchanged` |
| attestation_without_scope_rejected | unit | [[wild.tiers.attestation_scoped]] | `attestation_missing_scope()` | `check(a) == failed` |
| expired_attestation_is_unknown | unit | [[wild.tiers.attestation_expiring]] | `attestation_with_past_expiry()` | `attestation_status(a) == Unknown ∧ independent_assurance unchanged` |
| cache_key_includes_checker | unit | [[wild.tiers.verdict_cache_keyed]] | `same_pair_under_two_checker_versions()` | `keys differ ∧ no cross-hit` |
| recorded_verdict_unchanged | unit | [[wild.tiers.verdict_recorded_immutable]] | `verdict_recorded_then_rerun_under_new_checker()` | `old record unchanged ∧ new record appended` |

## Notes

Evidence is graded because failures are correlated, so confidence is the minimum, never a product. Simulation round 1 (12 scenarios): six shape breaks were caught at tier 1, two behavior changes at tier 2 through laws, one at tier 3 through canary replay, one safe input widening was correctly passed, and two undeclared behavior changes escaped. Escapes of undeclared behavior are the known residual of this design.

## Design acceptance cases

These cases define future runtime behavior. They are not claims that the current prototypes implement the v1 protocol. Executable document and prototype gates are under Requirements.

### Rule: Fail fast ordering

The system SHALL satisfy `fail_fast_ordering` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: First reject stops run
- **GIVEN** the fixture domain `revision_failing_identity_and_laws()`
- **WHEN** the `fail_fast_ordering` check runs
- **THEN** `tiers_run == [identity] ∧ verdict == Reject`

### Rule: Exact tiers pure

The system SHALL satisfy `exact_tiers_pure` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Exact tiers ignore side inputs
- **GIVEN** the fixture domain `same_inputs_with_varied_clock_and_network()`
- **WHEN** the `exact_tiers_pure` check runs
- **THEN** `verdict(a) == verdict(b)`

### Rule: Verdict lattice

The system SHALL satisfy `verdict_lattice` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Verdict lattice laws
- **GIVEN** the fixture domain `three_arbitrary_verdicts()`
- **WHEN** the `verdict_lattice` check runs
- **THEN** **identity:** `meet(v, PassDeclared) == v` **associativity:** `meet(meet(a, b), c) == meet(a, meet(b, c))`

### Rule: Policy names min tier

The system SHALL satisfy `policy_names_min_tier` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Below policy refused
- **GIVEN** the fixture domain `verdict_PassDeclared_under_policy_requiring_laws()`
- **WHEN** the `policy_names_min_tier` check runs
- **THEN** `decision == refused`

### Rule: Rejection explains

The system SHALL satisfy `rejection_explains` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Reject names rule
- **GIVEN** the fixture domain `arbitrary_rejected_revision()`
- **WHEN** the `rejection_explains` check runs
- **THEN** `report has tier ∧ slot_or_law ∧ rule`

### Rule: Laws cumulative

The system SHALL satisfy `laws_cumulative` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Ancestor law failure rejected
- **GIVEN** the fixture domain `revision_violating_an_ancestor_law()`
- **WHEN** the `laws_cumulative` check runs
- **THEN** `law_check == failed`

### Rule: Law runs deterministic

The system SHALL satisfy `law_runs_deterministic` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Law run reproducible
- **GIVEN** the fixture domain `(contract, impl, seed)` run twice
- **WHEN** the `law_runs_deterministic` check runs
- **THEN** `run(a) == run(b)`

### Rule: Evidence cannot override exact

The system SHALL satisfy `evidence_cannot_override_exact` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Evidence never overrides reject
- **GIVEN** the fixture domain `shape_Reject_plus_clean_traffic_replay()`
- **WHEN** the `evidence_cannot_override_exact` check runs
- **THEN** `verdict == Reject`

### Rule: Evidence confidence conservative

The system SHALL satisfy `evidence_confidence_conservative` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Confidence is minimum
- **GIVEN** the fixture domain `observations_with_confidences([0.99, 0.90])`
- **WHEN** the `evidence_confidence_conservative` check runs
- **THEN** `confidence == 0.90`

### Rule: Contradiction triggers repair

The system SHALL satisfy `contradiction_triggers_repair` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Contradiction creates draft
- **GIVEN** the fixture domain `observed_behavior_outside_declared_contract()`
- **WHEN** the `contradiction_triggers_repair` check runs
- **THEN** `repair_draft_created ∧ contract_unchanged`

### Rule: Attestation scoped

The system SHALL satisfy `attestation_scoped` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Attestation without scope rejected
- **GIVEN** the fixture domain `attestation_missing_scope()`
- **WHEN** the `attestation_scoped` check runs
- **THEN** `check(a) == failed`

### Rule: Attestation expiring

The system SHALL satisfy `attestation_expiring` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Expired attestation is unknown
- **GIVEN** the fixture domain `attestation_with_past_expiry()`
- **WHEN** the `attestation_expiring` check runs
- **THEN** `attestation_status(a) == Unknown ∧ independent_assurance unchanged`

### Rule: Verdict cache keyed

The system SHALL satisfy `verdict_cache_keyed` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Cache key includes checker
- **GIVEN** the fixture domain `same_pair_under_two_checker_versions()`
- **WHEN** the `verdict_cache_keyed` check runs
- **THEN** `keys differ ∧ no cross-hit`

### Rule: Verdict recorded immutable

The system SHALL satisfy `verdict_recorded_immutable` as defined in the Constraints table and the v1 format reference.

#### Acceptance case: Recorded verdict unchanged
- **GIVEN** the fixture domain `verdict_recorded_then_rerun_under_new_checker()`
- **WHEN** the `verdict_recorded_immutable` check runs
- **THEN** `old record unchanged ∧ new record appended`

#### Acceptance case: Same contract different implementation requires new law checks
- **GIVEN** two implementation artifacts have the same contract hash but different bytes
- **WHEN** a law result cached for the first artifact is requested for the second
- **THEN** the law cache misses and policy cannot reuse the first acceptance

#### Acceptance case: Expiry preserves independent structural checks
- **GIVEN** a valid PassDeclared binding has an attestation expiring at 2026-10-06T15:00:00Z
- **WHEN** evaluation occurs exactly at that timestamp
- **THEN** attestation status is Unknown; structural assurance remains PassDeclared; policy requiring attestation refuses

#### Acceptance case: Timeout never becomes law pass
- **GIVEN** a required sampled law reaches its resource budget without completing
- **WHEN** the harness returns a result
- **THEN** status is inconclusive and policy refuses

#### Acceptance case: Version claim cannot satisfy structural policy
- **GIVEN** an uncontracted dependency has only a patch version label
- **WHEN** policy requires PassDeclared
- **THEN** the label remains metadata, assurance is Unknown, and policy refuses
## Requirements
### Requirement: Wild tiers design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL link to a structurally valid shared v1 schema without claiming future runtime behavior is implemented.

#### Scenario: Wild tiers design is self-contained
- **GIVEN** this spec, `docs/wild-formats-v1.md`, and `schemas/wild-v1.schema.json`
- **WHEN** the design contract gate checks normative rule coverage, local references, and the shared schema
- **THEN** every constraint has a corresponding rule and acceptance case
- **AND** both referenced files exist and the schema is valid JSON Schema draft 2020-12
- **AND** this capability is discoverable by strict OpenSpec validation

### Requirement: Protected local checking context

An enforced local check SHALL receive its base, obligations, scope, policy, checker, test/law harnesses, environment, fixtures, budgets, and evaluation time from a trusted invocation outside candidate control. Candidate-proposed changes SHALL be evaluated against the accepted context first. An authorized obligation transition SHALL bind old/new commitments and be labelled intentional change rather than backward compatibility.

#### Scenario: Candidate edits its own judge
- **GIVEN** a candidate deletes a law, narrows demand, or changes the policy or checker
- **WHEN** trusted enforcement evaluates the candidate
- **THEN** it retains the accepted context, reports the proposed change, and cannot accept by using the weaker candidate settings

#### Scenario: Authorized bug-fix changes an old obligation
- **GIVEN** an external authority record accepts a named old-to-new obligation transition for a bug fix
- **WHEN** the candidate passes the replacement requirements and unchanged obligations
- **THEN** its disposition is accepted intentional change with affected consumers recorded, not backward-compatible success

### Requirement: Evidence is bound and method labelled

Local evidence SHALL bind actual implementation and harness bytes, suite, fixtures, environment, scope, seed, and budgets. Current policy SHALL be evaluated afresh. Ordinary build/test success SHALL NOT become structural assurance or a v1 law result without the required harness guarantees. A sandbox that cannot enforce required restrictions SHALL yield inconclusive law evidence.

#### Scenario: Same contract but changed implementation
- **GIVEN** an implementation changes bytes without changing its extracted contract
- **WHEN** checking considers a previous executable law result
- **THEN** that evidence cannot satisfy the new artifact's law requirement

#### Scenario: Unsupported law isolation
- **GIVEN** the available runner cannot prevent an accepted law from reading ambient files or the network
- **WHEN** that law is required by policy
- **THEN** its result is inconclusive and the local outcome is unknown unless another definite failure already requires rejection

