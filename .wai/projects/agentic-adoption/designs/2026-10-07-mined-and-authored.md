---
tags: [design]
tracks:
- .wai/projects/agentic-adoption/designs/matrix
---

# Design: mined-and-authored

Decision: 04-mined-and-authored
Date: 2026-10-07T17:18:31Z
Matrix: .wai/projects/agentic-adoption/designs/matrix/

## Rationale

Provisional design direction: deterministic mining for immediate structural feedback, with optional human or agent obligations and protected baseline checks. Effectiveness and adoption remain hypotheses subject to independent experiments; this does not approve runtime implementation.

## Trade-offs

The combined approach maintains both extractors and authored obligations. It does not assume those costs are low merely because drafting is cheap. Semantic checks can be sampled or inconclusive; local partial adoption does not establish whole-system compatibility. The registry and deployment architecture are deferred from the first adoption experiment. The choice is provisional and can be reversed by the experiment results below.

## Decision-time snapshot — winning column

### 01-first-use

Initial supported structural feedback needs mined facts and repository inputs; authored obligations, a registry, and provider adoption are optional.

### 02-independent-checks

Authored text cannot overwrite extracted facts. Candidate obligations are compared with the protected base; evidence invalidates when inputs change. Enforcement requires trusted external invocation.

### 03-behavior-coverage

Authored obligations add semantics to mined interfaces. Dynamic completeness and general equivalence remain unresolved outside supported analysis or evidence domains.

### 04-feedback-latency

Changed-boundary checks and content-addressed caches are proposed; cold/warm latency and incremental/full equivalence require measurement.

### 05-maintenance

Both extractors and authored obligations need maintenance. Agents can draft and repair them; net attention and compute cost remain unmeasured.

### 06-evidence-reuse

Facts, provenance, obligations, coverage, results, and counterexamples bind explicit inputs; sharing can follow local adoption.

## Product hypothesis

Wild provides an agent with a fast, deterministic answer to: "Which accepted obligations does this patch violate, where are the affected consumers, and what remains unchecked?" The economic unit is an independently validated change, not a generated line of code or contract. Measure human attention and final correctness as well as agent compute.

The initial user is a team already making agent-assisted changes in an existing repository. Value must appear for one selected boundary before upstream packages, a registry, or a deployment controller adopt Wild.

## Three distinct artifacts

| Artifact | Producer | Meaning |
| --- | --- | --- |
| Extracted facts | Pinned deterministic miner | What the supplied source/build bundle declares and which usages the supported analysis resolves |
| Accepted obligations | Human or agent draft, accepted through project policy | What must remain true for a named consumer or boundary |
| Evidence and verdict | Pinned checker and declared harnesses | Which obligations were checked, by what method, on which inputs, with what result |

Authorship is provenance, not an assurance tier. An agent-written executable predicate can be checked in the same way as a human-written predicate. Neither a fluent description nor a signature establishes that the predicate captures the requirement. Source extraction observes the implementation; it does not independently establish intended semantics.

A candidate claim carries a stable claim identifier, subject and scope, authoring origin, source/build commitment, predicate or structural rule identifier, referenced evidence, and accepted/proposed status. Records distinguish proof, exhaustive finite enumeration, samples, and unverified declarations using the existing v1 assurance model. These are conceptual additions to evaluate, not a replacement wire schema.

Generated facts and authored obligations are stored separately. Re-mining does not erase authored obligations, and authored text cannot silently overwrite extracted facts. Contradictions are reported. An extractor bug requires an explicit correction with evidence, not a hidden precedence rule.

## Deterministic mining

Prefer compiler/type-checker semantic data and existing schema descriptions where available. Parse-only fallbacks expose their limits. A supported bundle includes imported schemas, generated sources, dependency identities, target, feature flags, toolchain, and extractor configuration. Macros and conditional exports require their actual build context.

Extract interface declarations, callable signatures, fields, schema defaults, and statically resolved consumer uses. Add semantic laws such as idempotency through authored predicates and executable evidence. A string named "idempotent" extracted from a comment is not proof of idempotency.

Keep semantic facts separate from source-location provenance so harmless whitespace or a moved declaration does not change the semantic contract solely through its source span. Evidence still binds the exact candidate artifact. Unsupported reflection, plugins, generated exports, and unresolved returned-object calls create explicit coverage gaps. An agent may propose a declaration or adapter that narrows a gap, but cannot assert complete coverage merely to clear it.

Cache keys include source/build inputs, extractor, schema, and checker versions. A change to any semantic dependency invalidates affected facts; an artifact or harness change invalidates affected executable evidence. Incremental checks must match a clean full check. Changes to analysis configuration, generated inputs, or uncertain dependency edges trigger conservative invalidation.

## Preserve obligations across agent edits

Let B be an explicitly selected accepted base and C the candidate. A trusted invocation pins the checker, policy, selected boundary scope, and the obligations accepted at B. Extract C and evaluate it against those obligations before considering changes proposed by C.

An agent can propose code, contract, and test changes together, but deleting a consumer, weakening a law, shrinking coverage, changing extractor options, or editing policy is a separately visible obligation change. It cannot turn the compatibility check green by changing what the same check expects. Local runs provide feedback; CI loads trusted checker/policy inputs outside the candidate's control for enforcement.

The baseline is a compatibility promise, not a claim that all old behavior is correct. An intentional API change or bug fix can legitimately retire an old obligation under the project's existing review policy. Its transition records the affected consumers and migration decision. The result is "accepted intentional change" rather than a fabricated claim of backward compatibility. The experiment must include such tasks to detect overconstraint.

No new per-edit human approval is introduced for contract-preserving changes. Humans are needed when intent or an accepted obligation changes, according to the project's existing authority rules.

## First-use and agent interface

Proposed CLI sketch, not implemented commands:

```text
wild check --base main --head HEAD --scope package:billing --format json
```

One invocation supplies mined baseline/candidate structural facts and a scoped report. Existing tests and host dependency bounds remain in force. Initial use does not require historical reconstruction, a registry identity, signed publication, or a sequence of adoption modes.

The report includes rule/claim identifier, base/candidate commitment, provider and consumer locations, expected/actual shape, minimal counterexample when available, evidence method, coverage gaps, and next checks that could resolve uncertainty. Suggestions are candidate repairs, not automatic weakenings of obligations. The deterministic core never needs an LLM call.

Use the same engine through CLI and CI; an editor or agent tool wrapper is optional. The loop is edit, check, inspect the incompatible boundary, repair, then check again. Bound output to affected findings and allow full evidence inspection on demand.

Support a protected, selected scope for incremental adoption. Report all discovered excluded boundaries and uncovered uses. A successful scoped check never claims that the whole assembly passes. Existing v1 whole-assembly meet semantics remain intact; a candidate cannot silently shrink the protected scope. Unsupported work outside that scope need not block an independently checked boundary.

Store accepted semantic obligations as small reviewable source-controlled files. Generate large fact inventories and executable bundles into caches or build artifacts. Introduce distribution and certificates when consumers need to share results. Keep lineages as an internal compatibility mechanism until users need cross-release migration; first use should not require inventing new package names.

## Proposed spec changes, subject to OpenSpec proposal

| Existing area | Proposed revision |
| --- | --- |
| wild-adopt | Add direct local scoped checking; make historical audit optional; remove mandatory traversal of all adoption modes for that workflow |
| wild-adopt baseline rules | Scope acknowledgements to accepted findings and enforcement context; unrelated pre-existing debt must not become a universal first-use expiry cliff |
| wild-extract | Specify compiler/build context, provenance, declared analysis domain, invalidation, and incremental/full equivalence |
| wild-core / tiers | Separate extracted facts, accepted obligations, and candidate obligation changes; retain explicit assurance and evidence methods |
| wild-compose | Allow local explicit assemblies from existing manifests without requiring newest-tip selection; retain complete validation of the chosen scope |
| wild umbrella / formats | Add actionable agent diagnostics and explicit scoped outcomes without inflating assurance |
| wild-registry / deploy | Remain later integrations; not prerequisites for local value |

The current specs are unchanged. Runtime implementation still belongs to wild-3rr; implementation of these revisions requires its own approved OpenSpec change.

## Experiment protocol

Beads wild-1xk owns comparative validation. The numbered experiments below are research protocols, not task-status lists. All success thresholds are provisional product targets to register before collecting results.

Freeze the first extractor/checker before held-out evaluation. Split by repository or release family, not random adjacent commits, to reduce leakage. Construct a mix of real historical changes, independently generated mutations, and live authoring tasks; report each separately. Include known-compatible changes, undeclared behavioral changes, dynamic usage, intentional breaks, and bug fixes that intentionally change old behavior.

Use a trusted external oracle prepared before contract generation: held-out consumer tests, independently reviewed requirements, and full builds where possible. Record disagreements for adjudication; neither a smoke test nor a mutation label is infallible. Agents must not alter or see hidden acceptance cases. Hold task, environment, harness configuration, model version, and budget fixed across arms; repeat stochastic trials and randomize execution order. Do not assume a shared random seed makes outputs identical.

Main arms:

- A: existing CI and specialized compatibility tools; agent can spend its budget writing tests.
- B: A plus deterministic mining and structural diagnostics.
- C: A plus authored obligations checked deterministically.
- D: A plus mining, authored obligations, and protected baseline checking.

Use equal total compute budgets for the primary cost comparison, charging drafting/setup and repair. Also compare at equal correctness targets; report quality/cost frontiers rather than hiding costs behind a fixed-budget success score. Report cold adoption costs and warm recurring costs separately, with amortization over 1, 10, and 100 changes.

Primary measures: independently correct task completion; compatibility regressions among accepted patches; all missed breakages including refused/unknown outcomes separately; human active minutes per accepted patch; cost per accepted patch. Report completion/refusal/abandonment rates so a tool that rejects everything cannot win on low accepted-error rate. Secondary measures include repair iterations, latency, token/compute use, flaky decisions, and provenance/coverage fidelity.

### E1: Can deterministic mining describe useful boundaries?

Sample 10 repositories from participating teams in one typed ecosystem, with independent interface/demand inventories for selected boundaries and a separate dynamic-language stress set. Run clean extraction repeatedly across directories and pinned execution environments. Perturb whitespace, source layout, features, macro inputs, imports, and generated code. Compare incremental and full results.

Measure stable canonical facts for equivalent inputs, reported versus actual gaps, supported-boundary coverage, stale-cache verdicts, and cold/warm latency. An undisclosed missing usage or stale accepting verdict is a correctness defect to fix before gating. Initial usability targets: first structural result within 10 minutes on the agreed corpus; warm structural feedback p95 within 2 seconds on recorded hardware. Long behavioral runs are a separate lane. These are targets, not measured guarantees.

### E2: Do agents make useful contracts cheaply?

Compare mining alone, a maintainer-authored obligation, an agent-authored obligation, and mining plus agent-authored obligations. Give authors the pre-change implementation, intended requirement, and public tests; keep candidate bugs and hidden consumer tests unavailable. A maintainer comparison can use a smaller subset to bound cost.

Use unseen mutations and historical changes to test whether obligations discriminate correct and incorrect behavior. Measure drafting and review minutes, useful new defects caught, false blocks of legitimate changes, surviving covered mutants, and execution/maintenance cost. Include requirement-authoring tasks where the old implementation is buggy, preventing "copy current behavior" from counting as correct intent.

Decision: add semantic authoring to the first product only if it contributes independent detections or lowers human effort compared with spending that budget on ordinary tests. Agent-written contract count is not a success metric.

### E3: Does Wild improve an agent's completed changes?

Run arms A-D on an initial 50 held-out tasks across the 10 repositories, three trials per arm: 600 runs for a directional pilot. Task types include refactors, feature additions, dependency upgrades, and intentional compatibility changes. This pilot does not establish rare-failure safety; use observed variance to size later studies.

Grade final artifacts outside the editable workspace. Cluster uncertainty by repository/task rather than treating repeated trials as independent tasks. Blind human correctness/repair review where practical. Initial product target: at least 20% lower median human active time at an agreed non-inferior correctness margin, or a material correctness improvement at comparable effort. Register the margin and severity weights with participating teams before running; an inconclusive interval is not a success.

### E4: Can a patch redefine its own success?

Construct cases that delete obligations, weaken predicates, remove consumers, alter coverage declarations, change policy, replace a checker, falsify evidence digests, and regenerate contracts from broken code. Include a positive control with a deliberately authorized obligation transition.

Run the actual trusted invocation and verify that unauthorized changes cannot erase original findings or produce whole-scope claims. Report every escape, including tool errors and misleading reports. Acceptance for the bounded conformance suite is zero silent bypasses; this does not prove absence of all possible bypasses. Use the failing cases as regression fixtures.

### E5: Does consumer demand outperform a package-wide diff?

Use provider changes that remove an unused export, change a used signature, or introduce a new transitive requirement. Add returned-object calls, plugin registrations, and conditional uses. Compare package-wide checks, demand-scoped checks, and the independent full consumer oracle.

Measure false blocks eliminated, added misses, uncovered usage reported, analysis time, and candidate dependency closure validation. Treat unsupported cases as abstentions and measure their rate. Ship scoped clearance only for the analysis domains validated here; do not relax host dependency bounds by default.

### E6: Does evidence help across agents and sessions?

Use separate sessions or workers to change a provider and its consumers, then integrate their branches. Compare ordinary context plus CI with the same workflow plus obligations and counterexamples. This is an experiment design; no additional agents were launched during this session.

Measure cross-boundary regressions discovered before merge, integration repair time, repeated investigations, and evidence reused without stale acceptance. Budget-match added context so gains are not attributed solely to giving one arm more information. Compare structured diagnostics with the same findings in plain text to isolate feedback format from detection.

### E7: Will teams adopt and retain it?

Pilot with five teams on existing agent-assisted repositories for four weeks, using a randomized crossover or staggered introduction where practical. Track unassisted setup, first useful finding, weekly active use, disabling/ignoring findings, maintainer review time, and rejected changes later confirmed valid. Record why a tool is disabled, not just invocation counts.

Suggested early signals: four of five teams onboard within 15 human minutes and voluntarily retain the check at week four. Five teams cannot establish broad market fit. Account for researcher assistance and onboarding work explicitly. Commercial willingness to pay is a separate interview/usage question; technical success does not establish it.

## Decision boundaries and experimental order

E1 and E4 establish whether structural feedback and protected obligations are credible. E2 tests the user's cheap-authoring premise in terms of useful, maintained obligations. E3 is the principal value test. E5 and E6 isolate the proposed differentiation. E7 tests actual adoption once a usable local tool exists.

Prefer mining-only initially if D offers no incremental value over B. Prefer authored checking for a boundary if reliable mining is unavailable and C provides measurable value. Prefer existing tools if none of B-D improves the quality/effort frontier. Reconsider the entry ecosystem if useful coverage requires excessive manual declarations. Do not advance to registry/deployment implementation merely because a matrix selected the combined design.

## Delivery slices and validation

The first implementation slice would define independent fixtures and a protected invocation, then a supported miner using prototype/wild_proto.py as a source of failure cases rather than assuming it conforms. A subsequent slice would connect human/agent obligation drafts to the existing schema/evidence concepts and expose the scoped agent feedback loop. The final research slice would run the comparative protocol and measure onboarding.

Future specification work targets openspec/specs/wild-adopt/spec.md, openspec/specs/wild-extract/spec.md, openspec/specs/wild-tiers/spec.md, openspec/specs/wild-compose/spec.md, docs/wild-formats-v1.md, and schemas/wild-v1.schema.json. Runtime paths should be chosen in that proposal; the repository has no Rust implementation layout yet. Write meaningful conformance cases before runtime code, including stale-cache acceptance, hidden demand, unauthorized baseline weakening, and authorized intentional changes. Existing document/schema gates must continue to distinguish design from implemented behavior.

This session produces the decision matrix and design only. No experiment results or runtime guarantees are claimed.
