## MODIFIED Requirements

### Requirement: Explicit consumer demand coverage

The extractor SHALL resolve supported direct consumer usages to provider slots and SHALL disclose every unsupported usage mechanism encountered in the selected source domain. Expression macros whose head is a whitelisted std macro with a closed, argument-confined expansion and whose token trees parse as a comma-separated expression list SHALL be part of the supported demand profile: their arguments SHALL be descended and any demands found there recorded like direct calls, and they SHALL NOT emit an incomplete-demand gap. Any other expression macro — an unlisted head, or a whitelisted head whose tokens do not parse as an expression list — SHALL keep the incomplete-demand disclosure. Incomplete demand SHALL prevent scoped-substitution acceptance. Restricting consumer demand SHALL NOT discard required inputs of any selected provider or its transitive dependencies.

#### Scenario: Used and unused removals differ
- **GIVEN** a complete supported consumer demands function a but not function b
- **WHEN** a candidate removes b while retaining a and all required dependency bindings
- **THEN** the scoped structural check can pass although a whole-provider accretion check reports the removal

#### Scenario: Hidden usage blocks a scoped claim
- **GIVEN** the consumer contains an unresolved macro, returned-object method call, or function-pointer flow
- **WHEN** the known direct demand would otherwise pass
- **THEN** the report retains the gap and refuses scoped acceptance with Unknown structural assurance

#### Scenario: Argument-confined std macro does not block a scoped claim
- **GIVEN** a consumer whose code contains a whitelisted std expression macro (e.g. `println!`) alongside a direct dependency-qualified provider call
- **WHEN** extraction runs
- **THEN** the std macro emits no incomplete-demand gap and the provider call still resolves to a provider slot

#### Scenario: Demands inside supported macro arguments are recorded
- **GIVEN** a whitelisted macro invocation whose arguments reference provider functions (e.g. `assert_eq!(a(), b())`)
- **WHEN** extraction runs
- **THEN** the demands for a and b are recorded exactly like direct calls

#### Scenario: Unsupported macro remains disclosed
- **GIVEN** an expression macro with an unlisted head, or a whitelisted macro whose tokens do not parse as a comma-separated expression list
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap and refuses scoped acceptance with Unknown structural assurance
