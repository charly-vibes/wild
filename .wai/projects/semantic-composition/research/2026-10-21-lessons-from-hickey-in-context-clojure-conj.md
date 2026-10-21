---
tags: [pipeline-run:epic-orchestrator-2026-10-14-wild-cdp-3-rung2-contract-bundle-design, pipeline-step:verify]
---

# Lessons from Hickey, "In Context" (Clojure/Conj 2026)

Source: `../tv/transcripts_richhickey/txt/rich-hickey-in-context-conj2026 [P5eO7BNyJao].en-orig.txt`.
This is an analysis note, not a spec: it maps the talk's ideas onto wild's design,
marks where wild already agrees, and flags three tensions worth deciding on.

**Grounding** (reviewed 2026-07, Rule-of-5 pass with TypeSafe verification of
HIGH findings): `openspec/specs/wild-core/spec.md` (`polarity_openness_declared`,
`slot_shapes_closed`, `tombstones_preserve_names`, `accretion_monotone`),
`openspec/specs/wild-compose/spec.md` (`scoped_substitution`,
`binding_well_formed`, `certificate_*`), `src/v1.rs`, `src/check.rs`,
`docs/wild-manual.md` §2–§5. Status tags: **[spec: rule-id]** spec'd,
**[impl: path]** implemented, **[absent]** exists nowhere yet.

## Where wild already agrees (reinforcement, no change needed)

1. **Correctness is accordance with the world, not self-consistency.**
   Hickey: static types enforce "free from error" (internal consistency); you get
   paid for "consistent with fact". wild's bet is the same: contracts are
   *extracted* from reality, tier-3 evidence is replayed traffic, and a version
   label is never accepted as a verdict. PassDeclared is a claim about the world,
   not about the model. [spec: wild-tiers verdicts]

2. **There is no distributed now.**
   Shared-`now` tools (lockstep refactors, "just start using this connector")
   fail once programs, teams, and delivery schedules split. This is wild's core
   premise: independent lineages, floors, and explicit pins exist precisely
   because no check may assume synchronized releases. Rolling-update compatibility
   is a first-class scenario, not an afterthought. [spec: wild-tiers lineage/floors]

3. **Breakage is bad, even automatable breakage.**
   "Of course we did this by only adding and breaking nothing" is the accretion
   relation [spec: wild-core.accretion_monotone]. The adopt ladder
   (observe → shadow → gate) applies the same ethic to wild itself: enforcement is
   added without breaking anyone's release process. [spec: wild-adopt]

4. **Requirements are context-specific, not global.**
   No context-independent aggregate type works in every context; sometimes a key
   is optional here and mandatory there. wild's `demand` is exactly this move:
   the contract states what the component provides/requires; each *consumer*
   states the slots it actually uses [spec: wild-compose.scoped_substitution]
   [impl: src/check.rs — `demand.json` entries collected per consumer into
   `demanded_calls`/`demanded_names`]. Open extension, mirroring the talk's
   nested-destructuring point: per-binding-site (nested) demand — today demand is
   one flat list per consumer record. [absent]

5. **Dynamic systems support learning as you go; static systems demand
   know-it-all-ness.**
   wild never demands omniscience: `Unknown` is a first-class verdict and claims
   are scoped. Laws accumulate across revisions [spec: wild-tiers]; baselines
   expire (30-day acknowledgements) so yesterday's knowledge is re-earned, not
   frozen. [spec: wild-adopt baseline]

6. **Large systems become information systems about themselves.**
   Logs, dashboards, telemetry. wild's registry logs and certificates are that
   information layer for compatibility — keep them plain, inspectable files
   (JSONL, re-checkable offline) so "when you want to see something, you just
   look at it." [spec: wild-compose.certificate_complete]

## New lessons worth adopting

7. **Selection, not prohibition — "it is not wrong to pass more stuff."**
   Hickey's core design rule: require what you need; never reject what you
   don't. Required ≠ only. wild encodes this directionally, not absolutely:
   an input sum growing is an accretion while a closed output sum growing is a
   break [spec: wild-core.polarity_openness_declared], and an open provider sum
   binds only to an open consumer [spec: wild-compose.binding_well_formed].
   See Tension A on the *default*.

8. **Well-behaved conveyance (the `excess` idea).**
   A component that routes what it does not interpret — proxies, pipes,
   registries, middleware — should be certifiable as a *conveyance*: it selects
   what it needs and re-attaches (`merge deep`) the rest downstream.
   Design implication: contracts could gain a `conveys` clause — "unknown input
   slots at these paths are forwarded, not interpreted" — so a pass-through
   component gets a scoped claim instead of being rejected for unextracted
   demand. This is the `select + excess = all` algebra expressed as a verdict.
   **Interaction with an existing invariant:** conveyance narrows what is
   *interpreted* (an extraction-level feature); it never narrows what is
   *validated* — scoped_substitution's rule stands unchanged: "restricting
   demand never hides newly introduced required inputs" [spec:
   wild-compose.scoped_substitution]. A `conveys` claim must not read as an
   exemption from checking the replacement's transitive required-input closure.
   Today nothing of this exists. [absent]

9. **Missing is a policy, not a truth (the `missing` directive).**
   The same expression of requirements serves two contexts with two policies:
   "my program is broken" → throw; "the outside world lacked the fact" → collect
   and handle. wild's verdicts should carry this distinction — placed at the
   contract level, not as a new static verdict: a required input slot could
   declare `on_absent: fallible` [absent], meaning absence is a normal *value
   outcome* the consumer handles, not a caller violation. wild's tier-1 checks
   run pre-deployment over contracts, so this clause changes demand semantics
   and the scoped claim; the absence itself is observed at tier 3 (canary,
   replayed traffic). [spec: wild-tiers]

10. **Few universal conveyors beat many bespoke connectors (DB25 → USB-C).**
    Growing an interface by adding pins breaks everyone downstream. For wild:
    prefer a small number of wide, open conveyance structures over many narrow
    typed ones at component boundaries; grow by accretion on the open structure,
    never by reshaping the connector.

## Tensions to decide (do not silently resolve)

**A. Openness default.** The manual and spec both say records/sums are *closed
by default* [spec: wild-core.polarity_openness_declared] [impl:
src/v1.rs:597 — `is_open()` → `unwrap_or(false)`]; Hickey's whole argument
pushes the opposite default for *information* (facts about the world) and is
relaxed only for *mechanisms* (contrivances you invent, where you write all the
rules). Candidate resolution: open-by-default for records describing
external-world facts; closed remains available and must be justified for
mechanism-internal types. **Ripple:** this is far more than an openspec change —
the default is load-bearing in code, keyed by spec'd unit tests
(`closed_output_growth_is_break`), and because a revision is identified by the
hash of its canonical form, changing the default re-hashes every existing
contract and breaks lineage ancestry at the hash level. It needs an IR schema
version bump (per the `slot_shapes_closed` precedent) plus a hash-migration
story for existing registries.

**B. Tombstones are prohibition by design.** "A tombstoned name can never return
with a different meaning" is exactly the prohibition Hickey warns against
[spec: wild-core.tombstones_preserve_names; the rule exists because exhaustive
small-scope testing found the dropped-names gap]. Keep it: the asymmetry
(silent meaning-change vs loud new name) is worth one deliberate prohibition.
But note it in the spec rationale as a *chosen* exception, so future additions
don't multiply prohibitions casually.

**C. wild is itself a static checker.** The talk's critique of static thinking
("you must be a know-it-all before it compiles") applies to wild's tiers 0–2.
The defense is already built in — Unknown verdicts, scoped claims, evidence and
attestation tiers for what shape checks cannot know — but the manual should say
so explicitly: wild checks mechanisms mechanically and treats information
claims as scoped, expiring, and evidence-backed.

## One-line takeaway

wild's accretion/openness/demand triad is the DB25-to-USB-C move done right;
what the talk adds is *conveyance* (certify the pass-through, without weakening
scoped_substitution), *absence as policy* (fallible required inputs, observed
at tier 3), and an openness default that matches information rather than
mechanisms (an IR-version change, not a doc tweak).

