## ADDED Requirements

### Requirement: Bounded deterministic Rust extraction

The local extractor SHALL implement the rust-cargo-local-1 profile defined in this change's design, bind every result to supplied source/build inputs and extractor identity, and emit existing v1 contracts plus separate provenance and completeness records. It SHALL perform no network access or writes to the source bundle. Equivalent supported declaration structure SHALL yield identical semantic contract bytes independently of checkout location. Unknown declaration inventory SHALL prevent complete extraction claims.

#### Scenario: Repeated extraction and formatting
- **GIVEN** two bundles with equivalent supported declarations, with only whitespace and checkout location different
- **WHEN** the pinned extractor processes both under the same profile and build context
- **THEN** semantic contract bytes match while raw input identities and source provenance remain accurately distinct

#### Scenario: Generated export cannot disappear
- **GIVEN** a macro or build script can generate exported declarations unavailable to the profile
- **WHEN** extraction runs
- **THEN** it reports the construct and incomplete inventory and does not invent a complete contract

#### Scenario: Changed build input requires new extraction
- **GIVEN** a prior report and changed feature selection, target, toolchain, or dependency source
- **WHEN** the prior extraction is submitted for the new bundle
- **THEN** input binding fails and a fresh extraction is required

### Requirement: Explicit consumer demand coverage

The extractor SHALL resolve supported direct consumer usages to provider slots and SHALL disclose every unsupported usage mechanism encountered in the selected source domain. Incomplete demand SHALL prevent scoped-substitution acceptance. Restricting consumer demand SHALL NOT discard required inputs of any selected provider or its transitive dependencies.

#### Scenario: Used and unused removals differ
- **GIVEN** a complete supported consumer demands function a but not function b
- **WHEN** a candidate removes b while retaining a and all required dependency bindings
- **THEN** the scoped structural check can pass although a whole-provider accretion check reports the removal

#### Scenario: Hidden usage blocks a scoped claim
- **GIVEN** the consumer contains an unresolved macro, returned-object method call, or function-pointer flow
- **WHEN** the known direct demand would otherwise pass
- **THEN** the report retains the gap and refuses scoped acceptance with Unknown structural assurance
