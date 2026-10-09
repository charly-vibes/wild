---
title: "Wild and Specodelic: Assessment of Semantic Portability and Compositional Contracts"
report_type: "independent architectural assessment"
author_model: "OpenAI GPT-6"
created_at: "2026-10-08T23:33:00-03:00"
created_at_precision: "conversation-local time; reporting timestamp approximate"
source_project_wild: "https://github.com/charly-vibes/wild"
source_project_specodelic: "https://github.com/charly-vibes/specodelic"
specodelic_target_release: "v0.7.0"
wild_branch_observed: "main"
wild_commit_sha: "UNKNOWN"
specodelic_v0_7_0_commit_sha: "UNKNOWN"
verification_method: "Web retrieval of GitHub README, raw documentation, format specification, experimental summary, and docs.rs; attempted git ls-remote failed (DNS)"
source_snapshot_integrity: "NOT COMMIT-PINNED"
implementation_executed: false
claim_scope: "Publicly accessible design and self-reported experiment evidence, not independent code or runtime validation"
provenance_standard: "PROV-inspired: entity = URL documents, activity = reading/comparison, agent = GPT-6"
---

# TL;DR

**Verdict: Wild is a promising *component contract compatibility and assembly* layer, not yet a complete *semantic portability* layer for Specodelic.** Its v1 design specifies language-neutral slots, type inclusion/subtyping, substitutability (called *accretion*), dependency bindings, composition, portable canonical JSON, and evidence-labelled compatibility certificates. These are substantive mechanisms, not just similar terminology. **However**, its own README calls it a *design with prototypes* and says the `wild` command is not yet implemented. Its manual excludes emergent whole-system properties, and an identical interface contract or contract hash cannot establish identical implementation behavior. [W1][W2][W3]

**Recommended integration:** use Specodelic for intent, constraints, state models and properties; use Wild's *proposed* Contract IR for versioned component interfaces, dependency demands, and assembly certificates; add an explicit semantic mapping and refinement checker between the two. Do not treat Wild's declaration-level `PassDeclared` as proof of application correctness. [W2][W3][S1]

**Evidence quality:** documentary assessment only; no Git checkout, source tests, CLI execution, or independently repeated experiments. Git commit identities are **UNKNOWN**. The report does not assert that current main implements the normative Wild v1 format. [W1][W3]

## 1. Evaluation question and definitions

**Question.** Does `charly-vibes/wild` provide the language- and paradigm-neutral semantics, contract refinement, and component-composition guarantees needed to design systems in Specodelic and realize them in different programming languages?

- **SUT:** system under test (a real implementation or component assembly).
- **Specodelic:** a Markdown-based, four-layer specification system with **Intent**, **Constraints**, **Model**, and **Properties**. The spec describes obligations; independent implementation correctness is not implied by linting or even bounded specification verification. [S1]
- **Contract:** a declarative interface description of what a component *provides*, what it *requires*, and possibly behavioral *laws*. [W2]
- **Semantic portability:** the same contract has an agreed meaning across languages and independently developed tools, so equivalent external behavior can be checked, not simply matching names and types.
- **Structural compatibility:** declared inputs, outputs, types, defaults, and dependencies are compatible according to a formal decision procedure.
- **Behavioral conformance:** an observed implementation satisfies a specified behavioral property under an identified set of assumptions, observations, and bounds.
- **Composition:** combining component instances by explicit bindings and establishing that the resulting assembly satisfies stated obligations.
- **Refinement:** a detailed or replacement implementation preserves specified externally observable behaviors; a mere shape match is not sufficient.
- **Accretion (Wild):** a revision can substitute for an earlier one by retaining old provided capabilities while not imposing stronger input demands, with additional restrictions on laws, defaults, relations, and provenance. [W3]
- **Evidence tier:** strength/method by which a claim is supported: structural declaration, checked law, observation, or attestation. The tiers are **not a single ascending proof scale**. [W2][W3]
- **UNKNOWN:** information not established by accessed sources or current testing; should not be interpreted as a negative result.

## 2. Sources and scope

| ID | Primary source | Evidence used | Limit |
|---|---|---|---|
| W1 | [Wild README](https://github.com/charly-vibes/wild/blob/main/README.md) | Repository status, prototype list, experiment caveats | Current branch, unpinned commit |
| W2 | [Wild manual](https://github.com/charly-vibes/wild/blob/main/docs/wild-manual.md) | Conceptual model, tiered checks, intended CLI, explicit exclusions | Mix of designed and prototyped behavior |
| W3 | [Wild v1 formats and decisions](https://github.com/charly-vibes/wild/blob/main/docs/wild-formats-v1.md) | Canonical JSON, Contract IR, subtyping, accretion, assembly, certificates, evidence | Normative *design*, not evidence that prototype implements it |
| W4 | [Wild experiments summary](https://github.com/charly-vibes/wild/blob/main/experiments/RESULTS.md) | Reported real-project experiment results | Self-reported, not independently replicated |
| S1 | [Specodelic v0.6.0 package documentation](https://docs.rs/crate/specodelic/0.6.0) and [v0.7.0 crate module documentation](https://docs.rs/specodelic/latest/specodelic/) | Four-layer design, compiled/model checking boundaries | v0.7.0 package landing page not independently accessible in this retrieval; implementation features must be version-checked |

The release targeted for architecture comparison is **Specodelic v0.7.0**. The accessible 0.6.0 docs and docs.rs latest module inventory are supporting context only; **UNKNOWN** whether every detailed v0.7.0 semantic edge has remained identical. No unverified latest-main behavior is attributed to a release.

## 3. What Wild actually specifies

### 3.1 A portable structural Contract IR

Wild's v1 design describes JSON documents with canonical byte representation and SHA-256 content digests. A contract includes named slots with direction (`in`/`out`), stable meaning identifiers, typed values, defaults, tombstones (historically removed input names), laws, and relations. Types include scalar ranges, records, tagged variants, sequences, maps, functions, and opaque fingerprints. Contravariant input and covariant output requirements are explicit for function subtyping. These are unusually concrete steps toward language-neutral compatibility. **Equal contract digests establish structural identity, not identical executable behavior.** [W3]

Importantly, a contract's semantic meaning identifier remains an *assertion* of identity of meaning. The design does not universally derive meaning from source code. The manual acknowledges undeclared behavior behind unchanged signatures as a core weak point. [W2][W3]

### 3.2 Revision substitution and composition

`accretes(old,new)` checks whether new revisions preserve the old exports, do not strengthen required inputs, retain applicable laws, and meet defined restrictions on defaults, tombstones and relations. An incompatible revision creates a new lineage, with explicit adapters or declared unbridged boundaries. Consumers identify actual *demands* (the slots used), allowing more narrowly scoped replacement claims when demand capture is complete. [W2][W3]

Assembly documents contain component instances, provider demands and explicit bindings. Wild's normative format defines dependency closure, singleton compatibility, facet/type checks, and structural composition under renaming. Its design calls for certificates that can be independently checked against caller-provided expectations, policy, trust roots, time and allowed checker hashes. **This checks declared assembly compatibility, not arbitrary emergent behavior.** [W3]

### 3.3 Law and evidence tiers

Wild distinguishes structural `Reject`, `Unknown`, and `PassDeclared` from law-check methods (proof, finite exhaustive, or sampled), observed traffic evidence, and signed attestations. Tests have artifact/harness/fixture digests and declared execution constraints. A sampled passing result establishes only its tested scope; an attestation authenticates a claim, not its truth; an inconclusive run is not a pass. [W2][W3]

**Design maturity note:** the README and manual say these v1 protocols are designed; Python prototype simulations are smaller and **do not implement the v1 wire protocol**. Claims of production-ready certificates would be unsupported. [W1][W3]

## 4. Fit against semantic-portability requirements

| Requirement | Wild design fit | Confirmed implementation? | Residual gap |
|---|---|---|---|
| Canonical cross-language data interchange | Strong: canonical JSON, hashes, schemas | **UNKNOWN** for complete v1 runtime | Independent implementations must pass conformance fixtures |
| Cross-language interface contract | Strong: common structural types and polarities | Partial extractor prototypes (Rust/Python/CLI) | Coverage, faithful mapping, semantics of opaque constructs |
| Safe revision substitution | Strong formal *design* for accretion | Toy simulations reported | Does not ensure behavioral equivalence of same-shape revisions |
| Consumer-specific compatibility | Explicit demand-based checks | Prototype extraction reported | Dynamic / hidden usage and incomplete demand |
| Assembly compatibility | Explicit bindings, dependency closure and structural certificates | Runtime v1 **not established** | Cross-component temporal and safety invariants |
| Behavioral conformance | Digest-bound laws, harnesses and evidence designed | Prototype/experiments partial | A shared executable meaning for general Specodelic constraints |
| Hierarchical state refinement | No general semantics identified | **UNKNOWN** | Parent-to-child abstraction and trace refinement |
| Cross-language observational equivalence | Not established | **UNKNOWN** | Common event model, observation projection, progress/failure semantics |
| Emergent system-wide properties | Explicitly excluded from per-contract checking | No general guarantee | Concurrency, deadlines, retries, distributed invariants |

**Assessment:** Wild is a plausible complement to Specodelic's structural design model, but does not discharge semantic portability by itself. [W2][W3]

## 5. What the experiments support—and do not

The repository describes small experiments with Rust components, Python dependency pairs, and Specodelic CLI releases. Its manual reports a Python comparison using **28 combinations** and respective accuracies **0.89** for a contract checker versus **0.75** for declared ranges. It also states extractor fixes were made *after inspecting failures*; the reported difference is therefore exploratory, not unbiased out-of-sample validation. For Rust, reported differences from Cargo version ranges did not have a compilation oracle. A replayed CLI corpus detected behavioral differences that shape checks missed. [W1][W2][W4]

These experiments support **feasibility of useful signals**. They do **not** prove cross-language semantic equivalence, soundness of deployed v1 certificates, integration correctness across arbitrary components, or measurable safety improvement in production. All such stronger outcomes are **UNKNOWN**.

## 6. Integration architecture: proposed, not implemented

```text
        Specodelic design contract
  intent | constraints | model | properties
                   |
          semantic translation
      (explicit supported subset)
                   |
     Wild contract + behavior laws
      slots | demands | relations
                   |
           revision / assembly
          compatibility checker
                   |
     assurance and evidence report
                   |
     independent conformance layer
      traces | observations | oracle
                   |
   Rust / Python / JS / service SUTs
```

The key missing interface is a **semantics-preserving mapping** from Specodelic's meaningful properties and transitions to Wild's contracts and laws. Merely compiling a free-text constraint into a Wild `law` label preserves provenance but **not an executable meaning**. The adapter must either (a) translate a supported typed fragment with a documented correctness criterion, (b) attach an independently checked test/harness, or (c) mark the claim **UNKNOWN / uninterpreted**.

A useful minimal experiment would specify one reservation component, with public events `hold`, `confirm`, `expire`, and an invariant such as `confirmed && expired` is forbidden. Build a Rust and Python reference SUT and adapt each to a shared event vocabulary. Verify that:

1. Wild's contract digests and input/output compatibility can be computed consistently.
2. Scenario outputs conform to the **same** independent oracle; negative and race cases are present.
3. A changed implementation with identical slot shapes but divergent expiry behavior is **not falsely certified as behaviorally identical**.
4. A component substitution preserves declared consumer demands *and* an end-to-end reservation safety property.
5. An unsupported temporal/concurrency obligation is reported as **UNKNOWN**, never inferred from `PassDeclared`.

This experiment has **not been executed in this report**.

## 7. Guarantees and non-guarantees

| Possible claim | Defensible statement |
|---|---|
| Two contracts have identical hashes | They have identical canonical declared structural content under the specified hashing rules; not necessarily identical implementations. [W3] |
| New revision accretes old | The declared structural, law-retention and relation obligations required by the checker design hold, assuming correct extraction and implementation of rules. [W3] |
| Binding passes `PassDeclared` | Declared structure passed; hidden behavioral differences may remain. [W2][W3] |
| Law passes sampled harness | That implementation passed listed samples under reported execution assumptions; universal validity is not established. [W3] |
| Assembly certificate verifies | The explicitly supported, configured certificate claims match expected commitments and policy; this does not prove arbitrary system-level safety. [W3] |
| Specodelic specification verifies | Its checked property claims passed the configured checking pipeline/bounds; correctness of every implementation does not follow. [S1] |

## 8. Risks, assumptions, and open questions

### Assumptions

- A1. The repository files retrieved over GitHub represent a coherent branch snapshot. **Not proven**, because the retrieval is not commit-pinned.
- A2. The intended comparison is design-to-design integration, rather than proof of a production-ready executable platform.
- A3. Oracle observations can be normalized into a common event/typed-value vocabulary; doing so without semantic loss must itself be validated.
- A4. The spec's observable obligations can be separated from implementation mechanisms; this will not always be possible for timing and resource guarantees.

### Open questions (all **UNKNOWN** unless resolved)

1. **UNKNOWN:** Exact Wild `main` commit SHA for the inspected design files.
2. **UNKNOWN:** Exact Specodelic `v0.7.0` tagged commit SHA and whether the current tagged compiler's semantic subset maps directly to Wild v1.
3. **UNKNOWN:** Whether Wild's v1 format is implemented by any current executable checker end-to-end, beyond simulations and document/schema validation.
4. **UNKNOWN:** Whether independent Rust/Python/JS implementations of the Wild v1 canonicalizer produce matching bytes/hashes on exhaustive edge-case fixtures.
5. **UNKNOWN:** How Specodelic's `expr`, kernel expressions, state transitions and property scopes can be mapped to Wild `laws` without semantic loss.
6. **UNKNOWN:** Whether Wild accretion is sound against realistic undeclared behavior, nondeterminism and partial demand extraction.
7. **UNKNOWN:** Whether system-level assume–guarantee proof obligations or parent/child hierarchical refinements are planned for either project.
8. **UNKNOWN:** Real-world false-positive/false-negative rates on held-out component compatibility datasets.
9. **UNKNOWN:** Evidence that certificates remain sound through extractor changes, revoked attestations, clock boundaries and multi-language deployment.

## 9. Recommendation and next tests

**Proceed with an integration experiment, not a wholesale merger.** Retain separate responsibilities: Specodelic expresses human intent and checkable system obligations; Wild decides structural substitutability and assembly claims; a new or shared semantic adapter handles observable refinement and truth conditions.

**Pass/fail gates for the experiment:**

1. Schema-level: the same cross-language contract canonicalizes identically and malformed/ambiguous constructs fail closed.
2. Substitution-level: 20+ deliberate interface mutations produce predicted break/accretion classifications; include new required inputs, removed outputs, open/closed sum cases and changed defaults.
3. Behavior-level: 20+ oracle traces (including negative and boundary cases) detect at least one same-shape behavioral regression that Tier 1 deliberately cannot catch.
4. Assembly-level: an individually compatible replacement that violates a composed invariant is rejected by the *behavioral* layer, not misclassified as a Wild shape failure.
5. Evidence-level: missing implementations, unsupported semantics, incomplete demands and timed-out tests remain labelled **UNKNOWN** or inconclusive.
6. Auditability: every verdict records source digests, adapter revision, checker identity, corpus/version, method and finite bounds.

**Bottom line:** Wild offers a serious design for structural portability and contract-based compatibility. It is **not** a proven general-purpose semantic portability engine, nor does it replace independent behavioral verification. The best next step is to prove the *connection* between Specodelic's abstract requirements and Wild's portable contracts using a small, deliberately adversarial cross-language pilot.

## 10. Integrity and provenance record

- **Model:** OpenAI GPT-6.
- **Date:** 2026-10-08 (America/Argentina/Buenos_Aires).
- **Repository commits:** **UNKNOWN**; GitHub DNS access from the code-execution environment failed while attempting `git ls-remote` for Wild `HEAD` and the Specodelic `v0.7.0` tag.
- **Evidence collection:** Live web retrieval of Wild README, manual, v1 formats, experiment summary, and Specodelic docs.rs package material; document comparison only.
- **Code executed:** A failed repository-identity lookup; **no** repository tests, model checks, extraction experiments, or CLI calls were run.
- **External dependencies:** Mutable GitHub `main` URLs mean later readers should pin commits before reproducing claims.
- **Evidence hierarchy:** Documented normative design > explicitly labelled prototype claim > author's self-reported experiments > this report's engineering extrapolation. No extrapolation is labelled as implemented behavior.
- **Scope exclusions:** No current-release security audit, formal proof of theorem soundness, full code-level audit, or independent verification of benchmark metrics.
- **Reproducibility procedure:** Record both commit IDs; archive the cited source files and their SHA-256 digests; run available Wild document gates and prototype tests at that commit; run Specodelic `v0.7.0` against the nine Wild specifications; then execute the proposed cross-language conformance pilot. If a step fails, preserve the failure rather than substituting results from other versions.
