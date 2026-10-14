## MODIFIED Requirements

### Requirement: Bounded deterministic Rust extraction

The local extractor SHALL implement the rust-cargo-local-1 profile defined in this change's design, bind every result to supplied source/build inputs and extractor identity, and emit existing v1 contracts plus separate provenance and completeness records. It SHALL perform no network access or writes to the source bundle. Equivalent supported declaration structure SHALL yield identical semantic contract bytes independently of checkout location. Unknown declaration inventory SHALL prevent complete extraction claims. The profile's signature subset SHALL treat `String` as a supported owned-text scalar (`text-owned`) and `&str` and `&String` as a supported borrowed-text scalar (`text-borrowed`), each emitted without interval fields; mutable text references, bare `str`, and other text-like constructs SHALL remain unsupported and disclosed. A public enum without cfg gating SHALL inventory each of its variants as a named slot under the enum's qualified meaning (`<crate>::<Enum>::<Variant>`) instead of a single opaque enum item, following the identity law (crate identity plus qualified path, never line numbers); cfg-gated variants and generic public enums SHALL keep the honest gap. Impl blocks SHALL be accounted per construct: public inherent impl methods SHALL inventory as type-qualified opaque slots (`<crate>::<module>::<Type>::<method>`), plain-private impl items SHALL carry no public API surface, and trait impls together with restricted-visibility (`pub(crate)`/`pub(in)`) impl items SHALL keep named unsupported-construct gaps; impl bodies SHALL be walked so demands inside them are never silently dropped.

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

#### Scenario: Text-taking public functions become genuine slots
- **GIVEN** a provider whose public functions take or return text (arguments of `&str`, `String`, or `&String`, and a `String` return)
- **WHEN** extraction runs
- **THEN** the functions surface as function-type slots whose arguments and results carry the `text-borrowed`/`text-owned` scalars with no interval fields, `&String` normalizes to `text-borrowed`, and the report claims complete inventory with no diagnostics

#### Scenario: Mutable and bare text stays unsupported
- **GIVEN** a provider with a public function taking `&mut str` (or bare `str`, `char`, `Cow<str>`)
- **WHEN** extraction runs
- **THEN** the report retains the unsupported-construct gap, the function surfaces as an opaque slot, and inventory is incomplete

#### Scenario: Public enum variants become named slots
- **GIVEN** a provider whose public enum declares two variants and a consumer that constructs a dep-qualified variant
- **WHEN** extraction runs
- **THEN** each variant inventories as a named slot under the enum's qualified meaning, the single opaque enum item does not appear, the variant construction resolves as supported demand, and the extraction claims complete inventory with no diagnostics

#### Scenario: Trait impls and restricted impl items are disclosed per construct
- **GIVEN** a provider with an inherent impl exposing a public method, a private method, and a `pub(crate)` method, plus two trait impls on the same type
- **WHEN** extraction runs
- **THEN** the public method inventories as a type-qualified opaque slot, the private method carries no public API surface, and the report retains named unsupported-construct gaps for the `pub(crate)` method and each trait impl — with no blanket impl-block gap

### Requirement: Explicit consumer demand coverage

The extractor SHALL resolve supported direct consumer usages to provider slots and SHALL disclose every unsupported usage mechanism encountered in the selected source domain. Macro invocations in expression or statement position whose head is a whitelisted std macro with a closed, argument-confined expansion and whose token trees parse as a comma-separated expression list SHALL be part of the supported demand profile: their arguments SHALL be descended and any demands found there recorded like direct calls, and they SHALL NOT emit an incomplete-demand gap. Any other macro invocation in either position — an unlisted head, or a whitelisted head whose tokens do not parse as an expression list — SHALL keep the incomplete-demand disclosure rather than being silently skipped. A whitelisted macro invocation whose format string implicitly captures an identifier that names a provider item SHALL keep the incomplete-demand disclosure as well. A method call whose receiver resolves in the bounded shapes — a path expression resolving through the bounded demand rules, or a call expression whose head resolves to an inventoried constructor or free function with a recorded syntactic return type — SHALL create the demand `<crate>::<Type>::<method>`: resolution against the inventoried impl-method or typed slots yields supported demand, and a method absent from the inventory SHALL keep the incomplete-demand gap naming the full path. A method-call receiver outside the bounded shapes (a multi-hop chain beyond one resolved hop, field access, macro output, or an unknown identifier) SHALL keep the incomplete-demand gap naming the receiver. Enum-variant demand paths SHALL resolve as supported demand when the variant is inventoried; unknown variant paths SHALL keep the incomplete-demand gap naming the path. Incomplete demand SHALL prevent scoped-substitution acceptance. Restricting consumer demand SHALL NOT discard required inputs of any selected provider or its transitive dependencies.

#### Scenario: Used and unused removals differ
- **GIVEN** a complete supported consumer demands function a but not function b
- **WHEN** a candidate removes b while retaining a and all required dependency bindings
- **THEN** the scoped structural check can pass although a whole-provider accretion check reports the removal

#### Scenario: Hidden usage blocks a scoped claim
- **GIVEN** the consumer contains an unresolved macro, a method call whose receiver is outside the bounded resolution shapes, or a function-pointer flow
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

#### Scenario: Resolved method call becomes supported demand
- **GIVEN** a consumer whose method call's receiver is a call resolving to an inventoried same-crate constructor with a recorded syntactic return type (e.g. `Meter::new().tick()` where `new` returns `Meter`)
- **WHEN** extraction runs
- **THEN** the demand `Meter::tick` is recorded and resolves against the inventoried type-qualified impl-method slot with no incomplete-demand gap

#### Scenario: Method absent from inventory keeps gap
- **GIVEN** a consumer whose method call's receiver resolves in the bounded shapes but whose method is absent from the inventory (e.g. `Meter::new().tock()`)
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming the full `<crate>::<Type>::<method>` path and refuses scoped acceptance with Unknown structural assurance

#### Scenario: Unbounded method receiver keeps gap
- **GIVEN** a consumer with a multi-hop method chain beyond one resolved hop (e.g. `Meter::new().tick().untick()`)
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming the receiver, and the one-hop demand inside the chain is still recorded

#### Scenario: Variant demand paths resolve
- **GIVEN** a consumer that constructs a dep-qualified inventoried variant (e.g. `provider::Mode::Slow(1)`) and a same-crate inventoried variant in expression position (e.g. `let f = Flavor::Sour;`)
- **WHEN** extraction runs
- **THEN** both demands are recorded as supported and no incomplete-demand gap is emitted

#### Scenario: Unknown variant paths keep the gap
- **GIVEN** a consumer referencing `provider::Mode::Huge` and a same-crate `Flavor::Salty`, neither inventoried
- **WHEN** extraction runs
- **THEN** the report retains the incomplete-demand gap naming each path and refuses scoped acceptance with Unknown structural assurance
