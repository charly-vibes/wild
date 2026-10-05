# 112 integration failures vs. an accretive-contract versioning tool

**Verdicts** (about the proposed tool, not the world):
- **S**: detectable or preventable mechanically if the design is adopted
- **P**: partly; needs an extra facet (ABI, behavior, dialect, environment), laws, or adapters
- **N**: outside versioning (governance, business, hardware, coordination)

Examples come from memory and are not individually re-verified. Check specifics before citing.

**Tally:** S 43, P 57, N 12.

## A. Dependency and packaging

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 1 | left-pad unpublished | Artifact vanished, builds broke | S | Append-only immutable registry |
| 2 | event-stream takeover | Malicious maintainer shipped code | P | New capabilities show as new requires in the diff; trust is out of scope |
| 3 | Diamond ranges (npm/pip) | Incompatible ranges unsatisfiable | S | Lineage is a chain; take the max |
| 4 | Python 2→3 | Breaking change, no bridge | P | New lineage name plus mandatory adapter; language-level adapters only partly feasible |
| 5 | Caret range, breaking minor | Declared minor actually broke | S | Compatibility computed, not asserted |
| 6 | 0.x semver loophole | "Anything may change" | S | No special-case versions |
| 7 | Yanked crate/gem | Lockfiles reference withdrawn release | P | Never delete; mark with advisory edge |
| 8 | npm peerDependency duplicates (React) | Two copies, hooks break | P | Singleton contract kind; needs runtime check |
| 9 | Rust types across majors | v1 `Error` ≠ v2 `Error` | P | Adapter plus declared shared identity |
| 10 | Maven nearest-wins | Silently picks older version | S | Resolver picks max in chain |
| 11 | Dependency confusion | Public package shadows internal name | P | Namespace ownership in registry |
| 12 | Typosquatting | Lookalike package names | N | Social/registry policy |
| 13 | Phantom dependencies | Import works only via hoisting | S | Extracted demands vs declared demands |
| 14 | Floating `latest` Docker tag | Same tag, different bits | S | Content-addressed revisions |
| 15 | Mutable GitHub Action tags | Tag repointed to malicious commit | S | Hash identity |
| 16 | Lockfile drift between envs | CI ≠ prod | S | Hash-pinned revisions |

## B. ABI and platform

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 17 | C++ std::string dual ABI (GCC 5) | Link/runtime errors | P | ABI facet separate from API |
| 18 | Rust unstable ABI | dylib mismatch | P | ABI facet; hash must match |
| 19 | glibc symbol versions | "GLIBC_2.xx not found" | P | Symbol versioning is accretion; build floor is a requires |
| 20 | Windows DLL hell | Shared DLL overwritten | S | Content-addressed side-by-side |
| 21 | Java serialVersionUID | Deserialization fails | P | Serialization facet |
| 22 | CPython C-extension ABI | Wheel per minor version | P | abi3 = declared frozen subset |
| 23 | Node native addon ABI | NODE_MODULE_VERSION mismatch | P | Same as 22 |
| 24 | Struct padding/endianness | Layout mismatch across platforms | S | Layout facet in IR |
| 25 | FFI/JNI struct drift | Silent memory corruption | S | Layout hash |
| 26 | Linux "never break userspace" | Rare semantic regressions | P | Behavioral laws |
| 27 | Linux in-kernel API | Out-of-tree modules break | P | Explicit "unstable" lineage |
| 28 | Android targetSdk changes | Same API, new behavior | P | Defaults as slots; behavior laws |
| 29 | Swift pre-5.0 ABI | Apps bundled runtime | P | ABI facet |

## C. Schema and serialization

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 30 | Protobuf field-number reuse | Old data misread | S | Names/ids never reassigned |
| 31 | proto2 required field | Can never be removed | S | Requires polarity |
| 32 | Protobuf unknown enum value | Old client mishandles | P | Open vs closed sum flag |
| 33 | Avro non-transitive BACKWARD | v1→v3 breaks despite adjacent passes | S | Transitive closure |
| 34 | Avro added field, no default | Old readers fail | S | New provide must be optional |
| 35 | Thrift field id/type change | Wire mismatch | S | Shape diff |
| 36 | JSON int64 in JavaScript | Precision loss | P | Numeric range in scalar facet |
| 37 | null vs absent field | Semantics diverge | P | Presence as slot attribute |
| 38 | additionalProperties:false | Added field breaks strict client | S | Open/closed record flag |
| 39 | NOT NULL column, old writers | Inserts fail | S | Writers' requires grew |
| 40 | Dropping column, old readers | Queries fail | S | Provides shrank |
| 41 | Column rename | Needs expand/contract | S | New name plus adapter (dual-write) |
| 42 | ORM/DB drift | Model ≠ actual schema | P | Extract both and diff |
| 43 | Parquet/Arrow column reorder | Positional readers break | P | Positional vs named slot flag |
| 44 | CSV header change | Downstream parsers break | S | Shape diff |
| 45 | Date format/timezone in payload | Silent misinterpretation | P | Semantic type facet |
| 46 | XML `any` / namespaces | Extension collisions | S | Open record with namespaced names |
| 47 | GraphQL field removal | Unknown clients break | P | Only declared demand is knowable |
| 48 | GraphQL enum addition | Exhaustive clients break | S | Output-position sum is closed |
| 49 | OpenAPI vs implementation drift | Spec lies | P | Extract from code and spec; diff |

## D. Services and protocols

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 50 | /v1→/v2 copies whole API | Coarse bump forces total migration | S | Per-slot compatibility |
| 51 | Twitter API v1.1 / pricing | Access removed | N | Business decision |
| 52 | Google Reader shutdown | Service ended | N | Business decision |
| 53 | Chrome SameSite default | Same cookie, new behavior | P | Defaults as behavior slots |
| 54 | TLS 1.0 removal | Old clients locked out | P | Capability negotiation as requires/provides |
| 55 | HTTP middlebox ossification | Protocol can't evolve | N | Network reality |
| 56 | DNS flag day | Needs global coordination | N | Coordination |
| 57 | gRPC status/deadline per language | Divergent semantics | P | Cross-language laws |
| 58 | Retry/idempotency change | Duplicate side effects | P | Idempotency as law |
| 59 | Offset→cursor pagination | Different protocol | S | New name plus adapter |
| 60 | Rate-limit tightening | Integrations throttled | P | Non-functional laws |
| 61 | Webhook payload evolution | Receivers unknown | P | Declared demands only |
| 62 | OAuth scope restriction | Capability narrowed | P | Capability as requires |
| 63 | Parsed error strings | Clients depend on text | P | Hyrum: undeclared surface |
| 64 | Unspecified ordering (Go map) | Code relied on order | P | Declare unordered; cannot stop reliance |
| 65 | Performance regression | Complexity change breaks callers | P | Bounds as laws |
| 66 | Token TTL change | Cached tokens expire early | P | Behavior law |

## E. Language and library

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 67 | Java 9 modules | Illegal reflective access | P | Reflection surface undeclared |
| 68 | Log4j JNDI default | Dangerous default behavior | P | Defaults as slots |
| 69 | Node createCipher removal | API removed | S | Provides shrank |
| 70 | AngularJS→Angular | Rewrite under same brand | P | New lineage; adapter extremely hard |
| 71 | Perl 6 / Raku | Incompatible successor | S | Lineage rename |
| 72 | Swift 2→3 renames | Mass source breakage | S | Rename = adapter (migrator) |
| 73 | Ruby 3 kwargs | Same signature, new semantics | P | Call-semantics law |
| 74 | C undefined behavior | Optimizers exploit UB | N | Language spec problem |
| 75 | JS flatten→flat (MooTools) | Monkey-patching collided with new builtin | P | Open-world extension |
| 76 | Python `async` keyword | Identifiers became reserved | S | Reserved names are a shared namespace |
| 77 | Go compat promise exceptions | Unkeyed struct literals | P | Closed-record flag |
| 78 | Rust trait impl ambiguity | Added impl/method breaks callers | P | Coherence facet |
| 79 | Scala 2.12 vs 2.13 binary | Incompatible artifacts | S | Artifact suffix = lineage name |
| 80 | Java default-method conflict | Diamond default methods | S | Name collision in merge |
| 81 | Overload ambiguity | Added overload breaks call sites | P | Resolution rules per language |
| 82 | Inference breakage | Return-type change alters inference | P | Language-specific facet |
| 83 | Struct field addition | Breaks positional/exhaustive use | S | Closed-record flag |
| 84 | Floating-point determinism | Differs by platform/flags | N | Hardware/compiler |
| 85 | ICU/Unicode collation | Sort order changes | P | Dialect/environment requires |
| 86 | Regex dialects | PCRE vs RE2 behavior | P | Dialect named in contract |

## F. Distributed systems and runtime

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 87 | Rolling deploy N/N+1 | Mixed versions coexist | S | Accretion = bidirectional safety |
| 88 | Stale cached objects | Old serialization after deploy | S | Transitive compatibility |
| 89 | Kafka in-flight old messages | Long retention outlives schema | S | Transitive compatibility |
| 90 | Event-sourcing replay | Years-old events | S | Upcasters are adapters |
| 91 | Feature-flag combinatorics | Untested combinations | P | Flags as slots; explosion remains |
| 92 | Mobile long-tail clients | Old apps never update | S | Accretion keeps them working |
| 93 | Root cert expiry (Let's Encrypt 2021) | Old devices fail TLS | N | Time/trust |
| 94 | Y2038 / int32 time | Overflow | P | Width in scalar facet |
| 95 | Kubernetes API removals | extensions/v1beta1 gone | S | apiVersion lineage plus conversion |
| 96 | Terraform provider upgrade | Resource semantics change | P | Behavior laws |
| 97 | Helm values schema | Values keys change | S | Shape diff |
| 98 | YAML "Norway problem" | Parser dialect differences | P | Dialect named |
| 99 | CRD conversion webhook failure | Conversion bug | P | Adapter law tests |
| 100 | nginx directive removal | Configs refuse to load | S | Provides shrank |

## G. Standards, hardware, data, humans

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 101 | Mars Climate Orbiter | Units mismatch | P | Units in IR |
| 102 | Ariane 5 | Ariane 4 assumptions reused | P | Environment assumptions as requires |
| 103 | Knight Capital | Reused flag changed meaning mid-deploy | S | Names never change meaning |
| 104 | HL7 v2 | Vendor-specific interpretation | P | Profiles as contracts |
| 105 | Bluetooth/USB interoperability | Implementation quirks | N | Hardware certification |
| 106 | OOXML transitional vs strict | Two dialects | P | Dialect lineage |
| 107 | CSS vendor prefixes/quirks | Browser divergence | N | Implementation diversity |
| 108 | SQL dialects | Portable SQL isn't | P | Dialect lineage |
| 109 | Emoji version glyphs | Missing characters | N | Client updates |
| 110 | Excel gene names → dates | Auto-typing corrupts data | P | Semantic type facet |
| 111 | EDI X12 versions | Trading-partner mismatch | S | Negotiated adapters |
| 112 | tzdata changes | Future timestamps change meaning | N | Political reality |

## What this changes in the design

1. **Contracts need facets**, not one shape: API, ABI/layout, serialization, behavior/defaults, dialect, environment. Most P verdicts live in the last four.
2. **Defaults and environment are first-class slots.** Many failures are same signature, new behavior (53, 68, 73, 28).
3. **Name identity must be enforced hard** (103, 30, 9). A name's meaning never changes.
4. **Polarity plus open/closed flags** resolve a large cluster (31, 38, 48, 77, 83).
5. **Open-world demand is irreducible** (47, 61, 63, 75). Say so in output rather than pretend otherwise.
6. **N cases need a different tool**: governance, deprecation schedules, coordination.
