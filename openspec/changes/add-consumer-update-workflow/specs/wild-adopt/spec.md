## ADDED Requirements

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
