# wild: manual

Machine-checked compatibility for software components, first-party or third-party.

> **Status, read first.** wild is a design with a prototype, not a finished tool. What exists today: a nine-file specification suite (`specs/`, lint-clean), a toy checker (`wild_sim.py`), prototype extractors for Rust, Python, and command-line tools (`wild_proto.py`, `experiments/cli_extract.py`), and experiments on real projects. The `wild` command described below is the intended interface. Sections are marked **[prototype]** where code exists and **[designed]** where only the spec exists. File formats marked *illustrative* are not yet specified.

---

## 1. What it does

Version numbers are claims. wild replaces them with checks.

For every release of a component it extracts a **contract** (what the component provides and what it requires), compares it with earlier releases, and decides mechanically whether the new release can replace the old one. For a set of components that must work together it decides whether they compose, picks the revisions, and produces a **certificate** that anyone can re-check offline.

You get three things:

1. **A compatibility verdict per change**, computed from contracts, not from a version label.
2. **A composition verdict per assembly**, with a certificate.
3. **A deploy order and rollback rules** derived from those contracts, so continuous deployment needs no manual ordering.

## 2. The idea in one page

- A component's contract is a set of named **slots**. A slot is something it **provides** (an output, a function, a command, a field) or **requires** (an input a caller must supply).
- Revision B is an **accretion** of revision A when it provides at least what A provided and requires no more than A required. Old users keep working.
- Accretions compose and have identities, so they form a category (a preorder). This is what lets verdicts chain: if B accretes A and C accretes B, then C accretes A, with no re-check needed.
- A change that is not an accretion is a **break**. A break must start a **new lineage** (a new name) and ship an **adapter** back to the old one. Nobody is silently moved across a break.
- A consumer states its **demand**: the slots it actually uses. Compatibility is checked against the demand, so a break in a slot you never use does not affect you.
- Checks run in **tiers** ordered by cost. The cheap, exact tiers can reject; expensive, statistical tiers can only raise confidence.

## 3. Concepts

| Term | Meaning |
|---|---|
| **Contract** | The set of slots, laws, limits, and defaults of one component revision. |
| **Slot** | A named provided or required item with a type. Outputs have *out* polarity, inputs *in*. |
| **Openness** | Each record or sum is *open* (consumers must tolerate additions) or *closed* (default). Growing a closed output sum is a break. |
| **Revision** | A contract identified by the hash of its canonical form. Never edited. |
| **Lineage** | A chain of revisions where each accretes the previous one. A lineage has a version-free name. |
| **Accretion** | The relation "this revision can replace that one". Reflexive and transitive. |
| **Break** | Any change that is not an accretion. Starts a new lineage. |
| **Adapter** | A checked bridge from one lineage to another (facade library, wire proxy, data upcaster, or component wrapper). |
| **Demand** | The slots a consumer uses, derived from its code and tests. |
| **Floor** | For each provider a consumer uses, the least revision whose provides cover the demand. |
| **Law** | A recorded property that must keep holding (for example idempotency). Laws accumulate across revisions. |
| **Tombstone** | A record that a required slot was dropped, so its name can never return with a different meaning. |
| **Certificate** | A list of bindings (consumer revision, provider revision, demanded slots) that a separate verifier can re-check. |

### Tiers and verdicts

| Tier | What it checks | Nature |
|---|---|---|
| 0 identity | Hashes and lineage names | exact, instant |
| 1 shape | Provides, requires, polarity, openness, limits, defaults | exact, deterministic |
| 2 laws | All accumulated laws against the new implementation | exact, seeded |
| 3 evidence | Replayed traffic, consumer tests, canary | statistical |
| 4 attestation | A signed human claim with scope and expiry | human |

Verdicts form a lattice: `Reject < Unknown < PassDeclared < PassLawChecked < PassObserved`. A report always names the highest tier passed. The word "compatible" alone is never printed. A dependency with no contract is `Unknown`, not `Pass`.

## 4. How a change flows

```
source ──extract──▶ contract ──identify──▶ revision hash
                                   │
        tier 1 shape ◀─────────────┤   (checked against every ancestor)
        tier 2 laws  ◀─────────────┤
                                   ▼
             accretion?  ──yes──▶ publish to lineage
                  │
                  no ──▶ new lineage + adapter ──▶ publish
                                   │
consumers: demand ─▶ resolve ─▶ certificate ─▶ verify (offline)
                                   │
deploy: floors ─▶ gate ─▶ canary ─▶ roll ─▶ live ─▶ retire old lineage when demand is zero
```

## 5. Using it

### 5.1 First week in an existing project **[designed]**

wild adopts a project in four levels. Each adds enforcement; none changes your package manager, registry, or release process.

```
wild init                # writes extractor config, a baseline, and a CI hook; no edits needed
wild adopt observe       # read-only: rebuilds your release history from contracts
wild adopt shadow        # CI reports verdicts but never fails a build
wild adopt gate          # CI rejects only breaks introduced after the baseline
wild adopt native        # publishes sidecar records next to your existing artifacts
```

- **observe** extracts a contract at every past release and lists the releases whose declared version bump disagreed with what actually changed.
- **baseline**: the first enforcement run records existing breaks and rejects none of them. An acknowledged break needs an owner and an expiry; expired acknowledgements reject.
- **native** adds a sidecar record that binds your host artifact's digest to a revision hash. Your package, tag, and version are never modified.

### 5.2 Publishing a release (provider) **[designed]**

```
wild extract .           # source → contract (draft)
wild check               # tiers 0-2 against every earlier revision, locally
wild publish             # signs and appends the revision to the registry log
```

`check` tells you which tier rejected and why: the tier, the slot or law, and the rule. Typical outcomes:

| You did | Verdict |
|---|---|
| Added an output slot or an optional input | accretion, publish |
| Removed or retyped an output slot | break: new lineage and adapter required |
| Made an optional input required | break |
| Added a variant to a closed output sum | break |
| Changed a declared default or tightened a provided limit | break |
| Dropped a required input, later re-added with a new type | rejected (tombstone) |

### 5.3 Handling a break **[designed]**

```
wild adapt acme.billing acme.billing2    # drafts an adapter, TODO on each slot it cannot map
wild check --adapter                      # round-trip laws on recorded samples
wild publish --lineage acme.billing2
```

- A draft adapter has an explicit TODO for every slot the tool cannot derive.
- An adapter must declare whether it is lossless or list what it loses. A lossless adapter needs a passing round-trip law.
- Consumers whose demand does not touch the broken slot may move to the new lineage without an adapter. Moving is always opt-in.

### 5.4 Consuming a component **[designed]**

```
wild demand              # derive the slots you use from code and tests (editable)
wild lock import         # read your existing lockfile; unresolvable entries become Unknown
wild update              # advice only: per candidate version, are your slots still compatible?
```

- `update` never overrides your package manager's choice. It reports changes restricted to your demand, so a change in a slot you do not use is reported but never blocks.
- Lockfile entries are `lineage@hash`. Tags and aliases never resolve.

### 5.5 Composing components **[designed]**

```
wild resolve             # newest revision per package and lineage; no search
wild certify             # write the certificate
wild verify cert.json    # offline; needs only the certificate and the content-addressed contracts
```

- Resolution picks the newest revision in each lineage that satisfies demand. If two consumers need different lineages of one package, both copies are listed.
- A component declared **singleton** may appear under one lineage only.
- Values that cross between lineages need an adapter; otherwise the boundary is reported as unbridged.
- The assembly verdict is the minimum over its bindings, and the report shows the share of bindings verified per tier.

### 5.6 Deploying **[designed]**

```
wild deploy plan         # derive the order from floors; manual ordering is not accepted
wild deploy gate         # a consumer deploys only if its providers are live at or above its floor
wild deploy rollback     # refuses to roll a provider below any live consumer's floor
wild deploy retire       # retires an old lineage when no known consumer demands it
```

- A cycle among floors is rejected and its members listed. Simultaneous deployment is not offered.
- A revision that writes data older revisions cannot read must declare itself **irreversible**; rollback past it is rejected after its first write.
- A stale live-revision report counts as unknown and blocks the gate (fail closed).
- An emergency override records signer, reason, and expiry in the registry log.

### 5.7 Third-party software without contracts **[designed; extractors partly prototyped]**

- **Overlay**: you may publish an overlay contract for an upstream package, bound to its artifact digest and labelled *inferred*.
- **Tests as laws**: your passing integration tests against an uncontracted upstream are recorded as laws of your own component.
- **Version claims**: the upstream's declared version bump is recorded at the attestation tier and never higher.
- An edge to an uncontracted provider is `Unknown` unless an overlay or a law covers the slots you use.

## 6. Reading a report

Every command emits a JSON envelope by default when not attached to a terminal, and a human rendering on request. The envelope carries the tier, the verdict, and the slot ids. A report also states the checker version and lists which consumers are known and which cannot be known.

Example (illustrative):

```
check acme.billing  (rev 4f2a… → 91c0…)   checker 0.1
  tier 0 identity   pass
  tier 1 shape      REJECT   invoice.total: output type int32 → str
  stopped at tier 1 (first reject)
  known consumers: 3 declared. Undeclared consumers are not covered.
```

## 7. Writing a contract *(illustrative; the format is not yet specified)*

Most of a contract is extracted. You edit only what an extractor cannot know: laws, limits, defaults, and anything marked opaque.

```toml
lineage   = "acme.billing"
stability = "stable"            # stable | experimental | deprecated

[[slot]]
name = "invoice.total"
polarity = "out"
type = "decimal(2)"

[[slot]]
name = "invoice.status"
polarity = "out"
type = "sum"
variants = ["draft", "paid"]
openness = "open"               # consumers must tolerate new variants

[[slot]]
name = "charge.amount"
polarity = "in"
type = "decimal(2)"

[limit]
"batch.size" = { max = 500 }

[[law]]
name = "charge.idempotent"
```

## 8. What it does not do

- **Undeclared behavior.** A change in behavior behind an unchanged signature is caught only by a law or by evidence (tier 2 or 3). In experiments it was the main residual.
- **Consumers it cannot see.** Retirement and "safe to remove" are safe only against known consumers.
- **Governance.** Namespace disputes, typosquatting, business decisions to shut a service, and hardware retirements are out of scope; they can be recorded as attestations.
- **Lossy extraction.** The contract is a common denominator. What an extractor cannot express becomes an opaque slot, which is frozen, so it can cause false breaks. Extractors report their opaque share and false-break rate.
- **Emergent behavior.** Properties of a whole system, such as retry amplification, are outside per-contract checking.

## 9. Evidence so far

All from toy models or small real experiments; none from a production deployment.

- The accretion relation passed exhaustive reflexivity and transitivity checks over 76 single-slot states (438,976 triples) after four rule fixes found by the same tests.
- In a synthetic ecosystem, lineage resolution broke zero dependencies and needed no search; with truthful labels it coincides with semver-with-duplicates, so the gain is machine-checked labels.
- **genesis-vibes and specodelic (Rust)**: across 15 consecutive genesis-vibes releases, Cargo's 0.x caret rule and the contract check disagreed on 6, including one patch release that added a public struct field. specodelic's actual usage tolerated 1 to 6 more genesis versions than its Cargo range allowed. No compile test was possible.
- **Flask/Werkzeug and requests/urllib3 (Python)**: on 28 real version combinations, accuracy against an execution oracle was 0.89 for the contract check with call-site arguments and 0.75 for declared version ranges. Small sample, and two extractor fixes were made after seeing failures.
- **specodelic's own CLI**: shapes were identical across v0.2.0 to v0.4.0, while lint behavior changed in two rules. A replayed corpus caught it; the shape tier could not.

## 10. Troubleshooting

| Symptom | Likely cause and fix |
|---|---|
| A change is rejected at tier 1 but you never touch that slot | The full check applies to the whole lineage. Publish as a new lineage; consumers whose demand is unaffected can adopt it unaided. |
| Many breaks on the first run | Use the baseline; breaks present at baseline are recorded, not rejected. |
| False breaks on an opaque slot | Replace opaque with a typed slot in the extractor config, or accept the reported opaque share. |
| A dependency shows `Unknown` | It has no contract. Add an overlay, rely on tests-as-laws, or accept the weaker tier. |
| Deploy gate blocks | A provider is not live at your floor, or its live-revision report is stale. |
| Rollback refused | A live consumer's floor is above the revision you chose; roll those consumers back first. |
| Verification fails offline | The certificate is incomplete or a hash was altered; regenerate it from the registry. |

## 11. Reference

### Commands **[designed]**

| Command | Purpose |
|---|---|
| `init` | Write extractor config, baseline, and CI hook |
| `extract <source>` | Source to contract draft |
| `check` | Run tiers 0 to 2 against every earlier revision |
| `publish` | Sign and append a revision |
| `adapt <old> <new>` | Draft an adapter across lineages |
| `demand` | Derive consumer demand |
| `lock import` | Import an existing lockfile |
| `update` | Per-candidate compatibility advice |
| `resolve` / `certify` / `verify` | Composition, certificate, offline check |
| `deploy plan` / `gate` / `rollback` / `retire` | Rollout rules |
| `adopt observe` / `shadow` / `gate` / `native` | Adoption levels |
| `status` | Level, per-tier share of dependencies, open acknowledgements |
| `explain` | Why a verdict was reached |

### Specification map

| Spec | Covers |
|---|---|
| `wild` | Umbrella: computed, verifiable, honest verdicts |
| `wild.core` | Contract IR and the accretion category |
| `wild.tiers` | Tier pipeline and verdict lattice |
| `wild.compose` | Assemblies, resolution, certificates |
| `wild.registry` | Append-only log, ownership, lockfile, sidecar |
| `wild.bridge` | Adapters, overlays, third-party software |
| `wild.adopt` | Staged adoption |
| `wild.deploy` | Gate, canary, rollback, retirement |
| `wild.extract` | Extractors and law harness |

### Not yet specified

The Contract IR schema and canonical form, the consumer manifest and lockfile formats, and the sidecar record format. Each is planned as its own spec file.
