# 50 more integration failures (113-162)

Continues the first catalog (rows 1-112). Each row below introduces a failure *mechanism* not used in the first list.

**Verdicts** (about the proposed accretive-contract tool): **S** = mechanically detectable or preventable if adopted. **P** = partly; needs an extra facet, laws, or adapters. **N** = outside versioning.

**Sourcing:** rows 113-122 were checked against web sources this session (linked). Rows 123-162 are from memory and should be verified before citing.

**Tally for this batch:** S 16, P 33, N 1. **Combined with part 1 (162 cases):** S 59, P 90, N 13.

## A. Verified this session

| # | Case | Failure | V | Handling | Source |
|---|---|---|---|---|---|
| 113 | CrowdStrike Channel File 291 (Jul 2024) | A new template type defined 21 input fields, but the code feeding the interpreter supplied 20; out-of-bounds read crashed ~8.5M hosts. Data shipped outside the code release path | S | Extract arity from both the data schema and the interpreter; a mismatch is a failed accretion check. Data-plane artifacts need contracts too | [RCA](https://www.crowdstrike.com/wp-content/uploads/2024/08/Channel-File-291-Incident-Root-Cause-Analysis-08.06.2024.pdf) |
| 114 | Cloudflare outage, 18 Nov 2025 | A DB permissions change made a generated feature file double in size and exceed a hard-coded limit in the proxy | P | Declared limits (cardinality, size) become slots. Undeclared hard-coded limits stay invisible | [post-mortem](https://blog.cloudflare.com/18-november-2025-outage/) |
| 115 | Cloudflare leap second (Jan 2017) | Code assumed time never goes backwards; a negative duration panicked the DNS software | P | Environment assumptions (monotonic clock) as `requires`; cannot infer them from code | [Cloudflare](https://blog.cloudflare.com/how-and-why-the-leap-second-affected-cloudflare-dns/) |
| 116 | Let's Encrypt drops clientAuth EKU (2026) | Certificates were reused for mTLS client auth, a capability never promised for that purpose | P | Only declared demand is knowable. Consumers must declare the purpose; unknown dual-use remains | [Let's Encrypt](https://letsencrypt.org/2025/05/14/ending-tls-client-authentication/) |
| 117 | CA/B Forum SC-081 certificate lifetimes | Max validity falls 398→200 days (Mar 2026), 100 (2027), 47 (2029); manual renewal processes break | P | A scheduled sunset is a time-indexed shrink of `provides`; contracts need a schedule field so the break is computable years ahead | [Sectigo](https://www.sectigo.com/blog/200-day-certificate-expiration-begins) |
| 118 | MCP spec 2025-03-26 → 2025-06-18 | JSON-RPC batching was added, then removed one revision later | S | A standard violating accretion between consecutive revisions: the checker's exact remit | [changelog](https://modelcontextprotocol.io/specification/2025-06-18/changelog) |
| 119 | Redis BSD → RSAL/SSPL → AGPL | License changes forced forks and migrations | P | License as a contract facet (SPDX diff is mechanical; legal meaning is not) | [InfoQ](https://www.infoq.com/news/2025/05/redis-agpl-license) |
| 120 | Redis vs Valkey after the fork | Forks diverge: newer RDB files are not interchangeable, so data needs a logical migration | P | Fork = two accretions from a common ancestor; a pushout exists only if no semantic collision, so divergence is detectable but not repairable | [migration guide](https://computingforgeeks.com/valkey-vs-redis-migration/) |
| 121 | ChatGPT model retirements (Feb 2026) | GPT-4o and others left ChatGPT; existing chats defaulted to a successor model. API access was unchanged at announcement | P | Mutable aliases are an identity problem (pin by hash: S). Behavior drift of the successor is not | [YourStory](https://yourstory.com/ai-story/openai-retiring-gpt-4o-older-models-chatgpt) |
| 122 | Chrome third-party cookies / Privacy Sandbox | A planned replacement stack was built on, then 10 APIs were retired Oct 2025 while cookies stayed | P | Stability tiers: an `experimental` lineage may be retracted, and the tool should label it so consumers know | [Engadget](https://engadget.com/cybersecurity/google-has-killed-privacy-sandbox-130029899.html) |

## B. From memory (verify before citing)

| # | Case | Failure | V | Handling |
|---|---|---|---|---|
| 123 | Bitcoin fork, Mar 2013 | Versions 0.7 and 0.8 disagreed on a database-imposed limit; the chain split | P | Implicit consensus rules defined by an implementation must be declared as contract |
| 124 | Upgradeable smart-contract proxies | New implementation reorders storage variables and corrupts state | S | Layout facet; append-only storage slots |
| 125 | Parity multisig library (2017) | A shared library contract was destroyed, freezing dependent wallets | P | Dependency liveness as `requires`; irreversible operations flagged |
| 126 | Git SHA-1 → SHA-256 | Hash algorithm is part of object identity; repos are mutually unreadable | P | Hash algorithm belongs in identity; interop needs a bridge adapter |
| 127 | OpenSSL 3.0 providers | Legacy algorithms moved behind a provider not loaded by default | P | Capability set as `provides`; loading is environment |
| 128 | Kubernetes dockershim removal | Container-runtime interface dropped from kubelet | S | Provides shrank; external adapter (cri-dockerd) existed |
| 129 | Kubernetes PodSecurityPolicy → Pod Security Admission | Replacement is less expressive, so policies cannot be translated exactly | P | Lossy adapter; the tool should report what is lost |
| 130 | Chrome Manifest V2 → V3 | Blocking webRequest capability removed from extensions | S | Provides shrank; resolution is a policy choice |
| 131 | Safari ITP storage caps | Script-writable storage can be purged after days without interaction | P | Durability as a declared guarantee |
| 132 | macOS Catalina drops 32-bit apps | Unmaintained binaries stop running | P | Adapters impossible without a maintainer |
| 133 | Adobe Flash end of life | Plugin platform removed; content stranded | P | Emulators (Ruffle) act as adapters |
| 134 | GitHub master → main | Scripts hard-coded the default branch name | P | Conventions hard-coded instead of declared |
| 135 | PEP 668 externally-managed environments | `pip install` into system Python now errors | P | Tooling policy change; environment requires |
| 136 | Webpack 5 drops Node polyfills | Bundler had implicitly provided shims | P | Extract implicit provisions from tooling |
| 137 | colors / faker sabotage (2022) | Owner shipped intentionally broken versions | S | Registry rejects a breaking change without a new name |
| 138 | HTTP request smuggling | Front-end and back-end parse message length differently | P | Cross-implementation conformance laws |
| 139 | Gmail/Yahoo bulk-sender rules (2024) | Receivers tightened authentication requirements; mail rejected | P | Receiver's `requires` grew; senders may not track them |
| 140 | CPython free-threaded build | Extensions assumed a global interpreter lock | P | Thread-safety facet, opt-in declaration |
| 141 | NumPy 2.0 C-API change | Wheels built against 1.x failed under 2.x | P | ABI facet; build floor as `requires` |
| 142 | Protobuf generated code vs runtime | Old generated files rejected by newer runtime | S | Generated artifact embeds a required-runtime range |
| 143 | PostgreSQL major upgrades | On-disk format incompatible across majors | S | Each major a lineage; pg_upgrade is the adapter |
| 144 | Elasticsearch / Lucene index lookback | Indices only readable one major back | S | Deliberately non-transitive; checker flags it |
| 145 | Kafka rolling upgrade | Protocol/message-format pins force a two-phase upgrade order | P | Deployment sequencing is outside the contract |
| 146 | Terraform state upgrades | Newer versions write state older ones cannot read; no downgrade | P | Edges can be irreversible; declare reversibility |
| 147 | Python PEP 517 build isolation | Builds that relied on ambient build deps failed | P | Build-time contract |
| 148 | ISO 20022 / MT coexistence | Richer messages truncated when translated to old format | S | Adapter round-trip law detects loss |
| 149 | 3G network sunset | Devices lost connectivity | N | Infrastructure retirement |
| 150 | Excel 1900 leap-year bug | A deliberate bug kept for compatibility | P | Quirk lineage: bug-compat declared, not hidden |
| 151 | OpenSSL 1.1 opaque structs | Code touching struct fields broke | S | Closed/opaque layout flag |
| 152 | Case-insensitive filesystems | Repos with case-colliding paths break on macOS/Windows | P | Filesystem semantics as environment |
| 153 | LB idle timeout vs backend keep-alive | Intermittent 502s from mismatched timeouts | P | Relational constraint across two contracts |
| 154 | Retry amplification | Each layer retries; compatible parts overload the whole | P | Compositional law (retry budget) |
| 155 | JVM DNS caching | Client ignores TTL; stale endpoints | P | Client behavior vs protocol |
| 156 | Repo signing key rotation | Key change breaks installs | P | Trust-anchor lineage |
| 157 | WASI preview1 → preview2 | Module interface model replaced | S | New lineage plus adapter |
| 158 | Sync → async API change | Same name, new calling convention | S | Effect facet (async is a different type) |
| 159 | Ethereum/ETC fork replay | Signed transactions valid on both chains | S | Lineage id inside signed payloads (chain id) |
| 160 | WordPress "Tested up to" | Host compatibility is a human claim | P | Replace assertion with checked compatibility |
| 161 | pip's stricter resolver (2020) | Enforcement exposed conflicts old installers hid | S | Adoption needs baseline/grandfather mode |
| 162 | Old client read-modify-write | Typed clients drop unknown newer fields on update | S | Round-trip law: preserve unknown fields |

## What this batch adds to the design

1. **Data-plane artifacts need contracts** (113, 114): content files, feature files, templates.
2. **Declared limits are slots** (114): sizes, cardinalities, timeouts.
3. **Sunset schedules and stability tiers** (117, 122): breaks can be computed years ahead, and some lineages are explicitly retractable.
4. **Standards can violate accretion too** (118).
5. **Adapters need laws** (148, 162): lossless round-trip and unknown-field preservation.
6. **Lineage id belongs in identity** (126, 159).
7. **Relations between contracts** (153) and **emergent properties** (154) are beyond per-contract checking.
8. **Irreversibility and sequencing** (146, 145): edges can be one-way; upgrade order matters.
9. **Adoption mode** (161): first enforcement will surface latent breaks, so a baseline is required.
