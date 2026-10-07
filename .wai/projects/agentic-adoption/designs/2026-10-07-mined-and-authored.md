---
tags: [design]
tracks:
- .wai/projects/agentic-adoption/designs/matrix
---

# Technical design: contracts for software updates

Revised after the Rule-of-5 review. The [product matrix](../../software-updates/designs/matrix/problem.md) owns product selection; the [current technical decision](matrix/decision.md) owns mining and authoring. This document supplies the detailed technical design and experimental protocol for both decisions.

Decision: 04-mined-and-authored
Date: 2026-10-07T17:18:31Z
Matrix: .wai/projects/agentic-adoption/designs/matrix/

## Rationale

Provisional design direction: deterministic mining for immediate structural feedback, with optional human or agent obligations and protected baseline checks. Effectiveness and adoption remain hypotheses subject to independent experiments; this does not approve runtime implementation.

## Trade-offs

The combined approach maintains both extractors and authored obligations. It does not assume those costs are low merely because drafting is cheap. Semantic checks can be sampled or inconclusive; local partial adoption does not establish whole-system compatibility. The registry and deployment architecture are deferred from the first adoption experiment. The choice is provisional and can be reversed by the experiment results below.

## Initial decision-time snapshot — historical

This records the initial selection, before the review corrections. The current decision and snapshot are linked above; in particular, comparative evidence-reuse benefit is now explicitly unmeasured for every approach.

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

## Contribution to the product hypothesis

Wild helps a consumer move to useful software revisions using checked contracts rather than trusting version labels. The primary economic unit is an independently validated software update. Report direct replacements separately from migrations that modify consumer code or add adapters. Version names remain discovery metadata and hashes pin exact artifacts; neither label alone establishes compatibility.

The supporting agent interface answers: "Which accepted obligations does this candidate update violate, where are the affected consumers, and what remains unchecked?" Faster patch feedback is valuable only if it contributes to more valid updates, fewer unnecessary blocks, or less update effort. Generic refactor productivity is a secondary capability, not the product success criterion.

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

One invocation supplies mined baseline/candidate structural facts and a scoped report. A check alone does not edit manifests or bypass host constraints. The product workflow separately supports an explicitly authorized candidate outside the current compatibility range: it proposes a manifest change, resolves the actual resulting closure in isolation, checks that closure and artifacts, and validates the consumer. Runtime/platform, provenance, license, and organization-policy constraints remain independently enforced. No registry identity, historical reconstruction, or mandatory sequence of adoption modes is needed for this local workflow. The out-of-range experiment is specified in E5.

The report includes rule/claim identifier, base/candidate commitment, provider and consumer locations, expected/actual shape, minimal counterexample when available, evidence method, coverage gaps, and next checks that could resolve uncertainty. Suggestions are candidate repairs, not automatic weakenings of obligations. The deterministic core never needs an LLM call.

Use the same engine through CLI and CI; an editor or agent tool wrapper is optional. The loop is edit, check, inspect the incompatible boundary, repair, then check again. Bound output to affected findings and allow full evidence inspection on demand.

Support a protected, selected scope for incremental adoption. Report all discovered excluded boundaries and uncovered uses. A successful scoped check never claims that the whole assembly passes. Existing v1 whole-assembly meet semantics remain intact; a candidate cannot silently shrink the protected scope. Unsupported work outside that scope need not block an independently checked boundary.

Store accepted semantic obligations as small reviewable source-controlled files. Generate large fact inventories and executable bundles into caches or build artifacts. Introduce distribution and certificates when consumers need to share results. Keep lineages as an internal compatibility mechanism until users need cross-release migration; first use should not require inventing new package names.

## Proposed spec changes, subject to OpenSpec proposal

| Existing area | Proposed revision |
| --- | --- |
| wild-adopt | Add direct local scoped checking; make historical audit optional; remove mandatory traversal of all adoption modes for that workflow |
| wild-adopt update advice | Specify opt-in candidate discovery beyond compatibility ranges, reviewable manifest/lock changes, actual host resolution, and separate direct-update/migration outcomes; retain non-compatibility constraints |
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

Common enforcement for every arm: the same external trusted invocation pins the accepted base, existing tests, checker/tool configuration, policy, selected scope, permitted manifest edits, and independent grading inputs. Candidate patches cannot silently delete or weaken any accepted obligation they possess. New proposed tests or laws remain candidate additions until accepted under the same rule. All arms have equal authority to propose authorized out-of-range candidates and migrations, and the same candidate catalog and target priorities. Holding protection constant does not give an arm evidence or obligations it does not produce; it holds the enforcement rule constant.

The independent oracle grades all final artifacts, and the trusted invocation also protects in-loop checks in all arms. No arm receives weaker protection to create an apparent Wild advantage. If baseline protection is studied later, use a separate explicit ablation with identical mining/authoring inputs and report it independently.

Main arms form a 2x2 comparison of mining and authored-obligation feedback:

- A: existing update automation, CI, and specialized compatibility tools under common enforcement; agent can spend its budget writing tests.
- B: A plus deterministic mining and structural diagnostics; no Wild authored-obligation feedback.
- C: A plus authored obligations checked deterministically; no Wild mining feedback.
- D: A plus both mining and authored-obligation feedback; protection is identical to A-C.

Use equal total compute budgets for the primary cost comparison, charging drafting/setup and repair. Also compare at equal correctness targets; report quality/cost frontiers rather than hiding costs behind a fixed-budget success score. Report cold adoption costs and warm recurring costs separately, with amortization over 1, 10, and 100 changes.

Primary product measures are independently validated updates completed, incompatible candidates accepted, compatible candidates unnecessarily blocked, human active minutes and total cost per valid update, and elapsed time to the preselected desired compatible release. Report direct updates and migrations separately. Per-change speed and generic refactor success are secondary diagnostics.

### Outcome definitions and denominators

Each fixed candidate evaluation records base/candidate artifacts and dependency closure, check scope, evidence method, and one result: accept, reject, unknown, or error. Reject includes a reason category; a supported policy prohibition is distinct from a compatibility finding. Unknown is an abstention due to missing/inconclusive evidence; error means the check did not execute successfully. Neither is a false negative or proof of incompatibility. A sampled pass is scoped evidence, never universal compatibility.

The independent oracle assigns compatible, incompatible, or unresolved for the defined consumer domain and records non-compatibility eligibility separately. A compatible candidate is labelled from actual resolution/build and independent consumer validation, with its tested domain disclosed. Oracle-unresolved cases remain in coverage and completion reporting, are adjudicated blind where possible, and never enter binary correctness rates as successful cases.

The following table applies to candidates with adjudicated compatibility and satisfied non-compatibility constraints:

| Checker outcome | Oracle compatible | Oracle incompatible |
| --- | --- | --- |
| accept | Correct acceptance | Unsafe acceptance / false negative |
| reject for compatibility | False block / false positive | Detected incompatibility |
| unknown | Abstained compatible candidate | Abstained incompatible candidate |
| error | Failed evaluation | Failed evaluation |

Compatibility rates below use the policy-eligible adjudicated subset in the table unless a denominator explicitly includes every assigned evaluation. Report any acceptance of a policy-ineligible candidate separately as a policy violation. Publish the original cohort counts alongside exclusions. Denominators of zero yield undefined, never zero:

- Unsafe acceptance rate: accepted incompatible candidates / all accepted candidates with an adjudicated oracle. Report accepted oracle-unresolved candidates separately so uncertainty cannot disappear.
- Breakage detection recall: compatibility-rejected incompatible candidates / all oracle-incompatible candidates. Unknown/error outcomes stay in this denominator but are listed as abstentions/errors, not false negatives. Also report false-negative rate as accepted incompatible / all incompatible.
- False-block rate: compatibility-rejected compatible candidates / all oracle-compatible eligible candidates.
- Abstention and error rates: unknown / all assigned fixed candidate evaluations, and error / all such evaluations. Oracle adjudication coverage is adjudicated / all such evaluations.
- Policy exclusion counts: report each constraint reason independently. Correct policy refusal is not a compatibility false block; erroneous policy decisions are separate errors. Policy-ineligible cases are excluded only from the compatibility-eligible table above, not silently dropped from the assigned cohort.
- Update completion rate: independently valid pinned updates delivered / all assigned update tasks. Also report the rate on the preregistered feasible-target subset; do not select that subset after seeing tool results. A correct refusal on an impossible target is a correct disposition, but not a completed update.
- Human minutes and total cost per valid update: total effort/cost of every assigned task, including failed, blocked, and abandoned attempts / valid updates delivered. Also show median successful-task latency, timeout/abandonment rates, and per-stratum results; do not hide failed-work cost in a success-only median.

Count each assigned task once for completion and report candidate attempts separately. Direct replacement leaves consumer implementation unchanged (manifest/lock updates allowed); a migration changes consumer code or introduces an adapter. Both must satisfy the independently specified target behavior and preserved obligations. An authorized intentional behavior change is a separate labelled task class with predeclared new requirements; it cannot inflate backward-compatibility counts by weakening the old oracle.

### E1: Can deterministic mining describe useful boundaries?

Sample 10 repositories from participating teams in one typed ecosystem, with independent interface/demand inventories for selected boundaries and a separate dynamic-language stress set. Run clean extraction repeatedly across directories and pinned execution environments. Perturb whitespace, source layout, features, macro inputs, imports, and generated code. Compare incremental and full results.

Measure stable canonical facts for equivalent inputs, reported versus actual gaps, supported-boundary coverage, stale-cache verdicts, and cold/warm latency. An undisclosed missing usage or stale accepting verdict is a correctness defect to fix before gating. Initial usability targets: first structural result within 10 minutes on the agreed corpus; warm structural feedback p95 within 2 seconds on recorded hardware. Long behavioral runs are a separate lane. These are targets, not measured guarantees.

### E2: Do agents make useful contracts cheaply?

Compare mining alone, a maintainer-authored obligation, an agent-authored obligation, and mining plus agent-authored obligations. Give authors the pre-change implementation, intended requirement, and public tests; keep candidate bugs and hidden consumer tests unavailable. A maintainer comparison can use a smaller subset to bound cost.

Use unseen mutations and historical changes to test whether obligations discriminate correct and incorrect behavior. Measure drafting and review minutes, useful new defects caught, false blocks of legitimate changes, surviving covered mutants, and execution/maintenance cost. Include requirement-authoring tasks where the old implementation is buggy, preventing "copy current behavior" from counting as correct intent.

Decision: add semantic authoring to the first product only if it contributes independent detections or lowers human effort compared with spending that budget on ordinary tests. Agent-written contract count is not a success metric.

### E3: Does Wild help agents complete useful software updates?

Run arms A-D on an initial 50 held-out software-update tasks across the 10 repositories, three trials per arm: 600 runs for a directional pilot. Include ordinary within-range updates, compatible out-of-range candidates, incompatible within-range candidates, transitive/runtime/platform blockers, dynamic unknowns, and agent-assisted migrations. Freeze candidate catalogs and target priorities across arms; pre-register stratum counts and targets with participating teams. Historical cases use only inputs available at the selected cutoff. Generic feature/refactor tasks belong to a separate secondary cohort and cannot establish the update proposition. This pilot does not establish rare-failure safety; use observed variance to size later studies.

Grade resolved artifacts and actual consumer behavior outside the editable workspace. Cluster uncertainty by repository/task rather than treating repeated trials as independent tasks. Blind human correctness/repair review where practical. Initial product target: at least 20% lower aggregate human minutes per valid completed update at preregistered non-inferior unsafe-acceptance and completion margins, or materially more valid updates at comparable effort and risk. Register margins, severity weights, target priorities, and treatment of timeouts before running; an inconclusive interval is not a success. Report direct and migrated outcomes, and within/out-of-range strata, separately.

### E4: Can a patch redefine its own success?

Construct cases that delete obligations, weaken predicates, remove consumers, alter coverage declarations, change policy, replace a checker, falsify evidence digests, and regenerate contracts from broken code. Include a positive control with a deliberately authorized obligation transition.

Run the same common trusted invocation for A-D and verify that unauthorized changes cannot erase their accepted tests/obligations or produce unsupported whole-scope claims. Report every escape by arm, including tool errors and misleading reports. Acceptance for the bounded conformance suite is zero silent bypasses; this does not prove absence of all possible bypasses. Use the failing cases as regression fixtures.

### E5: Can consumer contracts enable updates that version ranges misclassify?

Use a preregistered 2x2 cohort of host-range allowed/excluded versus independently compatible/incompatible candidates. Explicitly include a major-labelled change to an unused API that the range excludes and a patch-labelled change to a used API that the range allows. Add new transitive requirements, singleton conflicts, supported-runtime/platform constraints, returned-object calls, plugin registrations, and conditional uses. Include a separate migration cohort where consumer edits or adapters are required.

For every arm, use the same explicit opt-in authority and an isolated branch/workspace. Run this end-to-end procedure:

1. Freeze the current consumer, accepted obligations, original manifest/lock, candidate catalog, target revision, and independent oracle before contract generation. Establish that an excluded candidate is blocked by the original declared compatibility range.
2. Propose a specific manifest-range/pin change for that candidate. Record why the original bound exists and which constraint is being changed. Range changes are reviewable actions, not silent resolver overrides; hard runtime/platform or other policy requirements remain enforced.
3. Invoke the real host resolver and install/build the resulting dependency closure. Check exact selected artifacts, every new required dependency, and global constraints. If the requested revision is not selected or resolution fails, record that outcome; do not score the intended revision as an installed success.
4. Run the candidate checks and independent consumer oracle on those actual artifacts. An unresolved dynamic use yields unknown at the declared scope; a new contract generated from the candidate cannot replace accepted consumer obligations.
5. For a direct update, require no consumer implementation edits. For a migration, record each consumer/adapter change and validate it against the same intended outcomes and independently accepted requirement changes. Never relabel a migration as direct compatibility.
6. Produce a reviewable manifest/lock/consumer diff with exact artifact identities and an evidence report. Restore the original isolated baseline between trials. No experiment modifies production deployment or weakens the incumbent application's real policy.

Compare package-wide checks, demand-scoped checks, and existing update tools/CI on valid completed updates, false blocks, unsafe acceptance, unknowns, human effort, and time to the same desired target. Every arm may propose the same authorized range change; the baseline is not artificially prevented from attempting major updates. Only report a range restriction overcome when the original range excluded the candidate and the actual pinned update independently passes. An interface-level verdict alone does not count as an update. Keep real, synthetic, and unresolved cases separate.

### E6: Does evidence help across agents and sessions?

Use separate sessions or workers to change a provider and its consumers, then integrate their branches. Compare ordinary context plus CI with the same workflow plus obligations and counterexamples. This is an experiment design; no additional agents were launched during this session.

Give the baseline its existing logs, test results, and build caches; give each treatment the additional artifacts it actually produced. All arms retain equal access to underlying inputs and equal total budgets, charging artifact retrieval and regeneration. On the same cross-session update tasks, measure repeated investigations/executions avoided, retrieval cost, integration repair time, and stale results accepted. Include changed-artifact, changed-harness, and changed-policy cases to test invalidation. Compare structured diagnostics with the same findings in plain text to isolate feedback format from detection. Markers in the technical matrix remain neutral on comparative reuse until measurements distinguish approaches; native formats or lack of a Wild format are not disadvantages by themselves.

### E7: Will teams adopt and retain it?

Pilot with five teams on existing agent-assisted repositories for four weeks, using a randomized crossover or staggered introduction where practical. Track unassisted setup, first independently valid completed update, desired-release lag, weekly updates delivered, disabling/ignoring findings, maintainer review time, and rejected updates later confirmed valid. Record why a tool is disabled, not just invocation counts. Usage without improved update outcomes does not establish the product proposition.

Suggested early signals: four of five teams onboard within 15 human minutes and voluntarily retain the check at week four. Five teams cannot establish broad market fit. Account for researcher assistance and onboarding work explicitly. Commercial willingness to pay is a separate interview/usage question; technical success does not establish it.

## Decision boundaries and experimental order

E1 and E4 establish whether structural feedback and protected obligations are credible. E2 tests cheap authoring in terms of useful, maintained obligations. E5 establishes the bounded end-to-end update procedure before the larger E3 study; E3 is the principal product value test. E6 isolates reuse benefit. E7 tests adoption and actual update outcomes once a usable local tool exists.

Prefer mining-only initially if D offers no incremental value over B. Prefer authored checking for a boundary if reliable mining is unavailable and C provides measurable value. Prefer existing tools if none of B-D improves the quality/effort frontier. Reconsider the entry ecosystem if useful coverage requires excessive manual declarations. Do not advance to registry/deployment implementation merely because a matrix selected the combined design.

## Delivery slices and validation

The first implementation slice would define independent fixtures and a protected invocation, then a supported miner using prototype/wild_proto.py as a source of failure cases rather than assuming it conforms. A subsequent slice would connect human/agent obligation drafts to the existing schema/evidence concepts and expose the scoped agent feedback loop. The final research slice would run the comparative protocol and measure onboarding.

Future specification work targets openspec/specs/wild-adopt/spec.md, openspec/specs/wild-extract/spec.md, openspec/specs/wild-tiers/spec.md, openspec/specs/wild-compose/spec.md, docs/wild-formats-v1.md, and schemas/wild-v1.schema.json. Runtime paths should be chosen in that proposal; the repository has no Rust implementation layout yet. Write meaningful conformance cases before runtime code, including stale-cache acceptance, hidden demand, unauthorized baseline weakening, and authorized intentional changes. Existing document/schema gates must continue to distinguish design from implemented behavior.

This session produces the decision matrix and design only. No experiment results or runtime guarantees are claimed.
