## MODIFIED Requirements

### Requirement: Explicit consumer demand coverage

The extractor SHALL resolve supported direct consumer usages to provider slots and SHALL disclose every unsupported usage mechanism encountered in the selected source domain. Macro invocations in expression or statement position whose head is a whitelisted std macro with a closed, argument-confined expansion and whose token trees parse as a comma-separated expression list SHALL be part of the supported demand profile: their arguments SHALL be descended and any demands found there recorded like direct calls, and they SHALL NOT emit an incomplete-demand gap. Any other macro invocation in either position — an unlisted head, or a whitelisted head whose tokens do not parse as an expression list — SHALL keep the incomplete-demand disclosure rather than being silently skipped. A whitelisted macro invocation whose format string implicitly captures an identifier that names a provider item SHALL keep the incomplete-demand disclosure as well. Incomplete demand SHALL prevent scoped-substitution acceptance. Restricting consumer demand SHALL NOT discard required inputs of any selected provider or its transitive dependencies.

#### Scenario: Used and unused removals differ
- **GIVEN** a complete supported consumer demands function a but not function b
- **WHEN** a candidate removes b while retaining a and all required dependency bindings
- **THEN** the scoped structural check can pass although a whole-provider accretion check reports the removal

#### Scenario: Hidden usage blocks a scoped claim
- **GIVEN** the consumer contains an unresolved macro, returned-object method call, or function-pointer flow
- **WHEN** the known direct demand would otherwise pass
- **THEN** the report retains the gap and refuses scoped acceptance with Unknown structural assurance

#### Scenario: Argument-confined std macro does not block a scoped claim
- **GIVEN** a consumer whose code contains a whitelisted std macro invocation in statement position (e.g. `println!("v={}", 1);`) alongside a direct dependency-qualified provider call
- **WHEN** extraction runs
- **THEN** the std macro emits no incomplete-demand gap and the provider call still resolves to a provider slot

#### Scenario: Demands inside supported macro arguments are recorded
- **GIVEN** a whitelisted macro invocation in expression or statement position whose arguments reference provider functions (e.g. `assert_eq!(a(), b())`) and no other consumer code calls those functions
- **WHEN** extraction runs
- **THEN** the demands for a and b are recorded exactly like direct calls

#### Scenario: Unsupported macro remains disclosed
- **GIVEN** a macro invocation in expression or statement position with an unlisted head, or a whitelisted macro whose tokens do not parse as a comma-separated expression list
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap and refuses scoped acceptance with Unknown structural assurance

#### Scenario: format_args! does not block a scoped claim
- **GIVEN** a consumer whose code contains a routed `format_args!` invocation with positional arguments (e.g. `writer.write_fmt(format_args!("hello {}", "world"));`) alongside a direct dependency-qualified provider call
- **WHEN** extraction runs
- **THEN** the `format_args!` invocation emits no incomplete-demand gap and the provider call still resolves to a provider slot

#### Scenario: Demands inside format_args! arguments are recorded
- **GIVEN** a routed `format_args!` invocation with positional arguments referencing provider functions (e.g. `writer.write_fmt(format_args!("v={} plus {}", add_one(1), 2));`) and no other consumer code calls `add_one`
- **WHEN** extraction runs
- **THEN** the demand for `add_one` is recorded exactly like a direct call

#### Scenario: Demands inside format_args! named-argument values are recorded
- **GIVEN** a routed `format_args!` invocation whose named-argument value references a provider function (e.g. `take_args(format_args!("{x} then {x}", x = add_one(1)));`) and no other consumer code calls `add_one`
- **WHEN** extraction runs
- **THEN** the demand for `add_one` is recorded exactly like a direct call and no incomplete-demand gap is emitted

#### Scenario: Format capture naming a provider item is disclosed
- **GIVEN** a consumer with a whitelisted macro invocation whose format string implicitly captures an identifier naming a provider value item — directly (`use provider::MAX;` followed by `println!("max={MAX}");`) or through a consumer-side alias (`use provider::MAX as LIMIT;` followed by `take_args(format_args!("{LIMIT}"));`) — and no other consumer code references that provider item
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap and refuses scoped acceptance with Unknown structural assurance