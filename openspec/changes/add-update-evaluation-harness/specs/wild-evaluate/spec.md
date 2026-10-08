## ADDED Requirements

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
