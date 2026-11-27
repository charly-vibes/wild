# Design: add-external-crate-awareness

## The trade-off this change settles

bd wild-90d: "the inventory only sees workspace members supplied in the
bundle, so std/prelude and third-party references keep named
incomplete-demand gaps … Options to design: bundling trusted external
signatures vs declaring a trusted-crate digest set. Scope decision needed;
**never silently trust**."

The question is *who may tell demand resolution what a non-workspace name
means, and how is that authority auditable*. Three options:

### Option A — bundle trusted external signatures (input-supplied inventories)

The extraction bundle's author supplies, per declared external crate, a
pre-extracted signature inventory (slot set with arities/kinds) generated
ahead of time by the same extractor profile run over that dependency. The
bundle declares the crate name and the inventory digest; the extractor
hashes it like any input.

- **Trust model (enforceable, not aspirational)**:
  - Every external inventory is an **input**: content-digested, named in
    the extraction request, bound into provenance — same mechanics as
    source and build inputs (`extractor_deterministic`, the existing
    "changed build input requires new extraction" rule). A digest mismatch
    is a hard input-binding failure.
  - **Provenance recorded, per bundle**: generating tool + version, the
    upstream crate name and version the inventory was extracted from, and
    the content digest. The generating tool is the wild extractor itself —
    so external signatures are structurally identical to workspace slots
    and need no new meaning machinery.
  - **No implicit std trust**: `std`/prelude is just another declared
    bundle (the ecosystem lane ships one, or the bundle author supplies
    it). Nothing resolves that was not declared. "Never silently trust"
    is enforced by construction: resolution against an undeclared external
    name is impossible — the code path is a gap, same as today.
  - **Weaker-claim marking**: a demand resolved against external
    signatures is recorded with `origin: external` + supplying digest. The
    contract and any downstream certificate/check report carry the
    external digest set used; a check that cannot reproduce or verify a
    digest reports Unknown for the affected assurance — never a silent
    pass. External slots are structural evidence about an artifact the
    bundle did not ship; the marking keeps that weakness visible at every
    decision layer.
- **Trade-offs**: offline by construction (`extractor_isolated` untouched —
  nothing is fetched at extraction time); determinism holds (same supplied
  inventories → same bytes); per-bundle, so two bundles may disagree about
  `serde_json` — visible, deliberate, auditable. Cost: a format lane change
  (request/bundle carries declared external inventories) and an inventory
  pre-generation step owned by whoever assembles the bundle.
- **Predicted abstention effect**: on testaruda 0.5.5 the 41 distinct
  external demand targets (`std.io.Error.new`, `libc.kill`,
  `shell_words.split`, `Duration.from_millis`, `Command.new`, `Stdio.piped`,
  `HashMap.new`, `Box.new`, `String.from_utf8_lossy`, …) move from gaps to
  resolved external demands. Combined with
  widen-method-receiver-demands (which clears the receiver shapes), the
  audit's 100.0% abstention is predicted to collapse to the
  unsupported-signature residual (trait impls) and genuinely unknown items
  — the residual count is the measured deliverable, not a promise.

### Option B — trusted-crate digest set declared at check time

Wild (or a registry) pre-extracts and ships signature inventories for a
curated set of crates; checks declare which digests from that set they
trust.

- **Why rejected**: it makes wild a trusted third party standing behind
  extraction results it did not derive from supplied inputs. The bundle
  author, not wild, knows which crates and versions a build actually used;
  a wild-curated set is either too coarse (wrong versions resolve
  structurally) or per-bundle anyway — at which point the digests must be
  supplied with the bundle, which is Option A with provenance flowing
  through wild instead of the bundle author. It also strains
  `extractor_isolated` (the trusted set is neither source nor a declared
  input unless supplied — and supplying it collapses it back into A).
  "Never silently trust" is hardest to enforce exactly where the trust is
  centralized; A keeps every act of trust at the bundle boundary where it
  is named, digested, and auditable. Rejected, reasoning recorded here.

### Option C — abstain by design with typed Unknown reasons

No resolution change: external references keep their gaps, but the gap
carries a typed reason (`external-crate-unmodeled`, `std-item`,
`unsupported-signature`, `unresolved-receiver`, `unknown-target`).

- **Value**: converts the opaque `incomplete-demand` bucket into a
  measurable residual-cause distribution — exactly what the audit
  threshold ("gap-rate measurement is the deliverable") needs, and the
  prerequisite for judging A's rollout. Zero trust expansion, zero
  resolution change, tiny surface (reason tagging at gap emission).
- **Predicted abstention effect**: the abstention rate is unchanged
  (12/12 stays 12/12 at first); what changes is that the 41 external
  targets on 0.5.5 become a countable `external-crate-unmodeled` class
  distinct from receiver-shape and unsupported-signature gaps.

## Recommendation

**Stage C first, then A.** C is a prerequisite measurement step that
changes nothing about trust; A is the resolution mechanism with the only
trust model that keeps "never silently trust" enforceable at the bundle
boundary. B is rejected (reasons above). The two stages land as one change
only if the maintainer approves both; tasks.md separates them so C can
land alone.

This change composes with widen-method-receiver-demands: receiver-shape
widening clears the within-crate gaps; declared external bundles clear the
external ones. Neither approximates — each widened resolution either lands
on a declared, inventoried slot or names its gap.

## Why this is not silent approximation

The house rule (bd wild-8j4: "never approximation; the honest gap stays
until then") is preserved by construction:

- An external demand resolves **only** against a slot in a declared,
  digested inventory — there is no name-based guessing, no known-api table
  consulted implicitly, no "std probably has this".
- Anything undeclared keeps its named gap. The code path for "unknown
  external name" is byte-identical to today's.
- The trust decision is made **once, by the bundle author, before
  extraction**, and is recorded in every artifact downstream (provenance,
  contract, check report). Nobody trusts anything at check time that the
  extraction did not already declare.

## Risks / Trade-offs

- **Wrong external inventory resolves a call the real crate does not
  support** → the digest-pinned inventory is the declared evidence; a
  stale inventory is a provenance failure caught by the digest/provenance
  record, and the `origin: external` marking keeps affected assurance
  weaker and visible. Mitigation: inventory generation tool + upstream
  version recorded per bundle; check reports the digest set.
- **Bundle-size/authors' burden** → declared externals are opt-in per
  bundle; a bundle declaring nothing behaves exactly as today.
- **Cross-crate demand must not be over-trusted** → external slots carry
  no transitive closure beyond what their inventories declare; demands
  into yet-undeclared transitive names keep gaps.
- **Version drift between two releases' external bundles** → structural
  slots are compared per bundle pair as workspace slots already are; a
  changed external inventory between the two extractions is visible input
  change requiring fresh extraction (existing rule).

## Non-goals

- Fetching or building anything at extraction time (`extractor_isolated`
  stays: no network, no writes).
- A wild-curated or registry-curated trusted crate set (Option B,
  rejected).
- Trusting macro-generated external APIs (e.g. `miette!`/`json!` produce
  code, not signatures): external inventories declare slots, not
  expansions; macro-shaped demands keep typed gaps.
- Cross-crate *conveyance* or absence-policy semantics (conveys/on_absent
  clauses are workspace-boundary mechanisms and unchanged).
- Any change to verdict semantics in wild-adopt/wild-evaluate: external
  resolution changes what demands resolve, not how gaps refuse.
