## MODIFIED Requirements

### Requirement: Bounded deterministic Rust extraction

The local extractor SHALL implement the rust-cargo-local-1 profile defined in this change's design, bind every result to supplied source/build inputs and extractor identity, and emit existing v1 contracts plus separate provenance and completeness records. It SHALL perform no network access or writes to the source bundle. Equivalent supported declaration structure SHALL yield identical semantic contract bytes independently of checkout location. Unknown declaration inventory SHALL prevent complete extraction claims. The profile's signature subset SHALL treat `String` as a supported owned-text scalar (`text-owned`) and `&str` and `&String` as a supported borrowed-text scalar (`text-borrowed`), each emitted without interval fields; mutable text references, bare `str`, and other text-like constructs SHALL remain unsupported and disclosed.

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
