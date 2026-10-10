---
id: wild.evaluate
kind: intent
statement: THE wild evaluation capability SHALL produce reproducible, independently graded comparison reports for synthetic software-update fixtures through real host tooling, while preserving unknown, unresolved, and failed outcomes behind explicit metric denominators.
---

# Wild evaluation

## Purpose

This is a normative design specification; only the prototype and corpus gate scenarios explicitly identified below are implemented. The evaluation harness runs the controlled A–D comparison (mined and authored obligation feedback) over frozen synthetic fixtures through real host tooling, grades delivered artifacts outside the candidates' control, and reports candidate and task metrics with exact denominators. It is a measurement capability separate from product semantics: nothing here changes v1 wire formats, compatibility rules, or the adoption ladder defined in [wild v1 formats](../../../docs/wild-formats-v1.md).

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| oracle_isolation | invariant | `the harness commits protocol, tasks, catalogs, targets, environments, tools/models, budgets, authority, split membership, and independent oracle inputs before comparative runs; the hidden acceptance suite is inaccessible to the candidate workspace; the grader evaluates the actual delivered artifact outside agent control and preserves unresolved verdicts and adjudication history; confirmatory-study mode requires preregistered risk/completion margins and stopping rules, while explicitly labelled fixture/debug runs stay possible` | [[wild.evaluate]] |
| equal_arms_enforcement | invariant | `arms A-D vary only the mined and authored-obligation feedback treatment while accepted-check protection, candidate access, action authority, target priorities, environment, and total budgets stay constant through one shared host execution path; cross-arm outputs and hidden oracle inputs never leak into candidate feedback, and an existing-tool arm retains ordinary tests, logs, caches, and the authority to attempt authorized range-changing updates and migrations` | [[wild.evaluate]] |
| real_range_strata | invariant | `the fixture suite covers original-range allowed/excluded crossed with independently compatible/incompatible candidates through real Cargo resolution, build, and fixed-lock verification, including transitive, singleton, runtime/platform, dynamic-analysis, wrong-target, migration, and intentional-change cases; neither a parse-only compatibility report nor a path replacement bypass counts as an overcome range restriction, and synthetic, real, and unresolved outcomes remain separately reported` | [[wild.evaluate]] |
| denominators_exact | invariant | `summaries implement the design's candidate and task denominators with raw counts and per-reason exclusions, distinguish policy from compatibility outcomes, preserve unknown/error/unresolved cases in their own categories, return null with a reason for undefined ratios, count at most one independently valid delivered update per task/arm/trial, include failed and abandoned attempts in effort, and keep fixed-candidate comparisons distinct from arm-selected search attempts` | [[wild.evaluate]] |

## Model

### States

- `registered`
- `executed`
- `summarized`

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| execute | registered | executed | [[wild.evaluate.oracle_isolation]] ∧ [[wild.evaluate.equal_arms_enforcement]] |
| summarize | executed | summarized | [[wild.evaluate.denominators_exact]] ∧ [[wild.evaluate.real_range_strata]] |

## Properties

| id | kind | derives_from | generator | predicate |
| -- | ---- | ------------ | --------- | --------- |
| oracle_outside_workspace | unit | [[wild.evaluate.oracle_isolation]] | `agent_trial_with_hidden_suite()` | `workspace contains no oracle artifact ∧ grader evaluated the actual committed artifact` |
| deleted_check_still_enforced | unit | [[wild.evaluate.equal_arms_enforcement]] | `each_arm_deletes_its_accepted_check()` | `original check enforced in every arm ∧ refusal category is policy` |
| range_barrier_overcome_by_host | unit | [[wild.evaluate.real_range_strata]] | `cargo_refused_target_under_original_range()` | `authorized manifest resolves the target ∧ lock pins the exact target ∧ consumer validation passes independently` |
| confusion_table_exact | unit | [[wild.evaluate.denominators_exact]] | `six_candidate_eligible_cohort()` | `unsafe_acceptance == 1/3 ∧ recall == 1/3 ∧ false_negative == 1/3 ∧ false_block == 0/3 ∧ unknown == 1/6 ∧ error == 1/6 ∧ oracle_coverage == 6/6` |

## Notes

Scope discipline: every fixture here is synthetic and hand-built, so results demonstrate harness mechanics — equal authority, protected grading, honest outcome retention — not user value. Held-out recruitment, risk/completion margins, and statistical power belong to the preregistered E3 study (comparative research wild-1xk) with the product-alignment review (wild-6ig) still open; no synthetic result closes either. A detected protection bypass fails the fixture suite; zero known bypasses is not a proof of general security.

## Design acceptance cases

### Rule: Oracle isolation

The system SHALL satisfy `oracle_isolation`.

#### Acceptance case: Hidden suite stays hidden

- **GIVEN** a frozen protocol with an independently specified hidden acceptance suite committed before contract generation
- **WHEN** an agent trial edits and executes inside its isolated workspace
- **THEN** the workspace inventory contains no oracle artifact and the external grader grades the actual delivered artifact against the committed suite

### Rule: Equal arms enforcement

The system SHALL satisfy `equal_arms_enforcement`.

#### Acceptance case: Baseline keeps its authority

- **GIVEN** an out-of-range major task authorized under the protocol
- **WHEN** the full-feedback arm and the no-feedback baseline arm each attempt it
- **THEN** both use the same target catalog, budgets, authority, and host execution path, and only the feedback treatment differs

### Rule: Real range strata

The system SHALL satisfy `real_range_strata`.

#### Acceptance case: Range barrier overcome through Cargo

- **GIVEN** a fixture whose exact target Cargo refuses under the original manifest range
- **WHEN** the authorized proposed manifest is applied in an isolated workspace
- **THEN** real Cargo resolves the target, the fixed lock selects it exactly, and independent consumer validation decides the delivered update's validity

### Rule: Denominators exact

The system SHALL satisfy `denominators_exact`.

#### Acceptance case: Unknown and unresolved never pass as successes

- **GIVEN** a summary over attempts that include unknown checker outcomes and an accepted but oracle-unresolved candidate
- **WHEN** candidate and task metrics are computed
- **THEN** the unknown, error, unresolved, and policy-excluded cases stay in their own reported categories and none counts as independently validated completion

## Requirements

### Requirement: Frozen independently graded evaluation inputs

The evaluation harness SHALL commit protocol, tasks, catalogs, targets, environments, tools/models, budgets, authority, split membership, and independent oracle inputs before comparative runs. It SHALL grade actual delivered artifacts outside agent control and preserve unresolved oracle results and adjudication history. Confirmatory-study mode SHALL require preregistered risk/completion margins and stopping rules.

#### Scenario: Candidate cannot read its oracle
- **GIVEN** an agent trial and a hidden acceptance suite committed before contract generation
- **WHEN** the agent edits or executes within its workspace
- **THEN** it cannot access or alter the suite and the external grader evaluates the actual output artifact against the committed suite

#### Scenario: Requested and graded artifacts differ
- **GIVEN** an attempt report names one artifact but the oracle result commits another
- **WHEN** records are validated
- **THEN** the result is invalid and cannot count as a valid update

#### Scenario: Missing margins prevent confirmatory claims
- **GIVEN** a protocol without risk/completion margins or stopping rules
- **WHEN** a confirmatory run is requested
- **THEN** it is refused with missing fields listed, while an explicitly labelled fixture/debug run remains possible

### Requirement: Equal enforcement and authority across arms

The harness SHALL vary only mined and authored-obligation feedback across A-D while holding accepted-check protection, candidate access, action authority, target priorities, environment, and total budgets constant. Existing tooling SHALL retain ordinary tests, logs, caches, and the ability to attempt authorized major/range-changing updates and migrations. Cross-arm outputs and hidden oracle inputs SHALL NOT leak into candidate feedback.

#### Scenario: Baseline can attempt the same major update
- **GIVEN** an out-of-range task authorized for D
- **WHEN** A receives the task
- **THEN** it receives the same target catalog and manifest-change authority through the same host execution path

#### Scenario: Deleted accepted check does not disappear
- **GIVEN** each arm has its own accepted tests/obligations and attempts to delete one
- **WHEN** the common trusted invocation runs
- **THEN** the original check remains enforced in every arm and no arm gains acceptance by weakening its baseline

### Requirement: Exercise real range-changing updates

The fixture suite SHALL cover original-range allowed/excluded crossed with independently compatible/incompatible candidates through real Cargo resolution/build and fixed artifacts. It SHALL include transitive, singleton, runtime/platform, dynamic-analysis, wrong-target, migration, and intentional-change cases. Synthetic, real, and unresolved outcomes SHALL remain separately reported.

#### Scenario: Range barrier is actually overcome
- **GIVEN** actual Cargo rejects the exact target under the original manifest range
- **WHEN** an authorized proposed manifest resolves that target and independent consumer validation passes
- **THEN** a pinned delivered update can count as an overcome range restriction
- **AND** neither a parse-only compatibility report nor a path replacement bypass can count

#### Scenario: Unsupported dynamic usage is retained
- **GIVEN** a fixture contains unresolved returned-object or generated usage
- **WHEN** the treatment returns unknown but an independent oracle can adjudicate behavior
- **THEN** the run retains both outcomes and does not relabel the abstention as detection or unsafe acceptance

### Requirement: Explicit metric denominators and complete effort accounting

Summaries SHALL implement the candidate and task denominators defined in this change's design, report raw counts and exclusions, distinguish policy from compatibility outcomes, preserve unknown/error/unresolved cases, and return null for undefined ratios. Task completion SHALL count at most one independently valid delivered update per task/arm/trial; effort SHALL include failed and abandoned attempts and disclose unavailable measurements. Fixed-candidate comparisons SHALL remain distinct from arm-selected search attempts.

#### Scenario: Six-candidate confusion table
- **GIVEN** two compatible accepts, one incompatible accept, one incompatible reject, one compatible unknown, and one incompatible error, all eligible and adjudicated
- **WHEN** the summary runs
- **THEN** unsafe acceptance, detection recall, and false-negative rate are each 1/3; false-block rate is 0/3; unknown and error rates are each 1/6

#### Scenario: No delivered update
- **GIVEN** three attempted tasks with recorded effort and no independently valid delivery
- **WHEN** cost per valid update is summarized
- **THEN** the ratio is null with zero-delivery reason and total failed effort remains visible

#### Scenario: Multiple attempts do not inflate completion
- **GIVEN** one assigned task takes three attempts before one valid delivered update
- **WHEN** the summary runs
- **THEN** it counts one completed task and includes all three attempts in effort

#### Scenario: Ineligible and unresolved cases remain visible
- **GIVEN** one policy-prohibited candidate and one accepted oracle-unresolved candidate
- **WHEN** compatibility metrics are computed
- **THEN** neither enters the eligible binary table, both remain in assigned counts and their own categories, and neither counts as independently validated completion

### Requirement: Wild evaluate design contract

The design corpus SHALL expose this capability's constraints as normative, self-contained rules with acceptance cases, and SHALL keep the evaluation capability separate from product semantics without claiming study completion for wild-1xk or wild-6ig.

#### Scenario: Wild evaluate design is self-contained
- **GIVEN** this spec and the shared v1 formats document
- **WHEN** the design contract gate checks normative rule coverage and local references
- **THEN** every constraint has a corresponding rule and acceptance case and all local references resolve


