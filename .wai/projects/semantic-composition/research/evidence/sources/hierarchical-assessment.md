---
title: "Understanding Wild: Contracts, Compatibility, and Architectural Reasoning"
artifact_type: "upstream documentation draft"
model: "OpenAI GPT-6"
author_role: "AI systems analyst and technical writer"
date: "2026-10-09"
repository: "https://github.com/charly-vibes/wild"
upstream_branch: "main"
upstream_version: "unreleased design/prototype"
upstream_commit: "UNKNOWN"
verification: "Primary-source web inspection; no independent prototype execution"
status: "PROPOSED — not normative Wild documentation"
---

# Understanding Wild: Contracts, Compatibility, and Architectural Reasoning

## TL;DR

Wild is an experimental project exploring **machine-checked compatibility and composition** of software components using contracts. It is **a design with Python prototypes, not a finished CLI**: there is no standalone `wild` executable at the time of this review. Its normative v1 formats describe intended protocol behavior, while smaller prototypes explore selected aspects of the model. [README][readme] [Manual][manual]

Its core idea is simple: a new component version should not be considered safe merely because a version number looks compatible. The relevant question is whether its declared provisions, requirements, laws, and evidence support the particular replacement or assembly. This separates *declared structure*, *behavioral checking*, *sampled evidence*, and *human attestations*. [Manual][manual]

**Critical limitation:** a correct check on an incomplete contract can still miss a real incompatibility. Wild's own experiments warn about undeclared behavior and extractor incompleteness. [Experiment results][results]

## Who should read this

Architects assessing component boundaries; maintainers considering dependency changes; platform teams concerned with upgrades or deployment gates; researchers evaluating contract-based verification. This guide is a conceptual introduction and proposal for upstream documentation, **not executable command documentation**.

## Where Wild stands today

| Area | Status | Caveat |
|---|---|---|
| Nine Specodelic design specs | Present, upstream reports lint clean | Reproduction not performed here |
| Contract and evidence wire formats | Normative v1 design and JSON Schema | Prototypes do not implement full protocol |
| Toy replacement checker | Python prototype | Limited model |
| Extractors | Rust, Python, and CLI experiments | Lossy/incomplete |
| Category, resolver, and certificate simulations | Python prototype | Not production cryptographic certificates |
| Deployment simulations | Python prototype | Assumption-driven |
| `wild` CLI commands | Designed only | No standalone command |
| Graph view generator | UNKNOWN | Not independently established |

Sources: [README][readme], [Manual][manual], [v1 formats][formats].

## Vocabulary

| Term | Meaning |
|---|---|
| Component | A provider or consumer of capabilities; its deployment/implementation may be independent of its contract |
| Contract | Declared provided and required slots, types, defaults, limits, and behavioral laws |
| Slot | A named provided output or required input with a declared meaning/type |
| Accretion | A replacement relation preserving old provisions without strengthening requirements, subject to full rules |
| Lineage | Authority-qualified history of compatible contract revisions |
| Demand | The capabilities a particular consumer actually requires |
| Assembly | Selected component instances, roots, and their declared bindings |
| Law | A declared behavioral property, whose evidence and check method must be considered |
| Evidence | Test results, replay, observations, or attestations supporting a scoped claim |
| Certificate | Intended independent-verification bundle for an assembly and policy |
| SUT | System under test: the existing or proposed implementation being described |
| UNKNOWN | Missing or insufficient information—not a successful check |

## 1. Think in obligations, not versions

A version range is a coarse claim about what might work. A contract states **which capabilities are available**, **what a consumer needs**, and **what conditions are required**. A replacement can be safe for a given consumer only if the relevant obligations hold and dependencies are considered. A change in behavior that is absent from these declarations remains outside structural assurance.

*Example (illustrative, not Wild syntax):* A consumer calls `authorize(amount)` and `refund(id)`. A provider release adds `settlementReport()`; that new capability need not break old consumers. But if it stops accepting an amount previously accepted, the older inputs might no longer be safely substitutable. Behavioral differences such as changed retries can escape a signature-level comparison.

## 2. Understand the assurance layers

| Layer | Intended question | What it does **not** establish alone |
|---|---|---|
| Identity | Are names, hashes, and revisions consistent? | That the implementation meets its contract |
| Shape | Do provided/required slots and types permit substitution? | Unspecified semantics |
| Laws | Do declared behavioral properties pass their stated method? | All properties not declared or tested |
| Evidence | What do tests, replay or canaries demonstrate in scope? | Exhaustive assurance beyond that scope |
| Attestation | Who made a signed, scoped, time-limited claim? | Truth beyond authority and underlying evidence |

The manual separates structural `Reject`, `Unknown`, and `PassDeclared` from the other evidence dimensions. Do not collapse these into an unconditional label of “compatible.” [Manual][manual]

## 3. Describe an existing system without claiming to recover all semantics

Recommended method (**proposed engineering workflow**, not one runnable Wild command):

1. Define externally observable system boundaries and consumers.
2. Inventory provided and required capabilities, plus their semantics and limits.
3. Extract candidate declarations from source/tests where extractors support them.
4. Record dynamic calls, missing imports, opaque types and unavailable versions as uncertainties.
5. Write down independent invariants and behavioral examples.
6. Model roots, component instances, dependency demand, and bindings.
7. Compare contract predictions with independent test executions and real failure examples.
8. Classify each disagreement: model omission, extractor limitation, implementation defect, or requirement ambiguity.

This prevents a source-code AST representation from being mistaken for a complete architectural description.

## 4. Design and change component boundaries

Wild can help reason about coupling through explicit consumer demand, but **contract validity is not a proof of architecture quality**. For a proposed component split, keep the original externally visible contract and test scenarios as an oracle. Check whether the new assembly continues to satisfy those obligations, then independently test cross-component state, ordering, retries, error handling, and other emergent behavior.

Questions worth asking:

- Which consumers depend on which exact slots?
- Does one contract cover several unrelated responsibilities?
- Are dependencies explicitly represented or only discovered at runtime?
- Do the proposed internal components collectively preserve external behavior?
- Are the newly introduced operational failure modes acceptable?

A decomposition may improve cohesion yet increase network complexity. Wild's structural model alone cannot decide that tradeoff.

## 5. Composition is not automatically hierarchical abstraction

Wild's intended assembly model includes roots, component instances, typed bindings, dependency closure and singleton constraints. The v1 design does **not establish a general automatically derived external contract for arbitrary nested assemblies**. [v1 formats][formats]

A future certified-composite mechanism would need to specify how public inputs/outputs map to internal slots, what is hidden, how aggregate laws are checked, and which internal changes preserve the published boundary. This is a **proposal**, not an existing Wild construct.

## 6. Test the contract itself

Two questions must be kept separate: **Does the implementation satisfy the contract?** and **Does the contract faithfully describe the intended system?**

Use negative examples and observed counterexamples to challenge the second. When a structural checker passes a change that fails a smoke test, do not merely add a suppression. Investigate whether a capability, dependency, precondition, behavioral law, or observable effect was omitted from the model. The upstream Flask/Werkzeug and Specodelic experiments illustrate the importance of this distinction. [Experiment results][results]

General-purpose contract-driven behavioral scenario generation and shrinking are **not independently established as implemented Wild features**.

## 7. Make architectural views reproducible

A useful future visualization system could project authoritative artifacts into several separate views:

| Proposed view | Architectural question |
|---|---|
| Assembly dependencies | What requires what, and where are bindings unresolved? |
| Contract boundary | Which exact slots and semantics cross a component boundary? |
| Lineage evolution | What made a revision accretive or breaking? |
| Evidence trace | Why did a policy accept, reject, or remain unknown? |
| Deployment prerequisites | Which updates must precede another change? |
| Change impact | Which consumers are exposed to a particular change? |

These are recommended projections; **no implemented Wild graph renderer was verified**. Generated views should carry input digests, scope, evaluation time, omitted-edge disclosures, and source links. A diagram is an explanation of structured data, not a certificate in itself.

## 8. Treat the experiments as exploratory evidence

The README describes synthetic models with assumed parameters and limited real-project experiments, and acknowledges that extractor improvements followed observed failures. Such results are useful demonstrations of mechanisms and failure modes, but do not establish generalized compatibility prediction quality. [README][readme] [Results][results]

Report unsafe false passes, missed breaks, oracle coverage, and confidence separately. An accuracy percentage alone may conceal safety-relevant false positives.

## 9. Documentation and implementation priorities

1. **P0:** Guarantee-boundaries guide: specified versus implemented, and structural versus behavioral assurance.
2. **P0:** Rule-to-test traceability: each normative rejection linked to schema, implementation, positive test and negative test.
3. **P1:** One complete worked example: capture source → candidate contract → demand → incompatibility → oracle challenge → corrected contract.
4. **P1:** Explicit counterexamples where checking an incomplete contract produces an unsafe verdict.
5. **P1:** Hierarchical-composition design note defining certified composite boundaries.
6. **P2:** Typed graph projection specification, showing uncertainty and provenance.
7. **P2:** Experimental-method guidance separating exploration from held-out validation.

## Assumptions and limitations

- Source inspection used current GitHub-rendered `main` pages on 2026-10-09. **Exact commit SHA: UNKNOWN.** Links to `main` are mutable.
- No official release binary or implemented standalone `wild` CLI was found in the cited README.
- No prototype scripts, schema validators or test suites were executed independently as part of this artifact.
- Described example architectures and proposed views are illustrations, not normative protocol syntax.
- Prior conversation phase reports informed topics, but the factual core of this draft is anchored to the primary sources below.

## Open questions — UNKNOWN

- Which exact revision was inspected, and have newer commits altered semantics?
- Which v1 normative rules have working semantic validator implementations and negative tests?
- How will independent oracles be integrated for contract completeness testing?
- How should composite contracts and aggregate behavioral laws be represented?
- What are the limits of extractor conformance across languages and paradigms?
- Is there a hidden prototype graph renderer outside the inspected documentation?
- How well do the reported findings generalize to held-out real projects?

## Primary sources

- [Repository README][readme] — project status, inventory, experiment caveats.
- [Wild manual][manual] — intended CLI, tiers and planned lifecycle.
- [Normative Wild v1 formats][formats] — protocol rules and document models.
- [v1 JSON Schema][schema] — structural schema, not a complete semantic validator.
- [Experiment results][results] — reported evaluations and limitations.

[readme]: https://github.com/charly-vibes/wild/blob/main/README.md
[manual]: https://github.com/charly-vibes/wild/blob/main/docs/wild-manual.md
[formats]: https://github.com/charly-vibes/wild/blob/main/docs/wild-formats-v1.md
[schema]: https://github.com/charly-vibes/wild/blob/main/schemas/wild-v1.schema.json
[results]: https://github.com/charly-vibes/wild/blob/main/experiments/RESULTS.md
