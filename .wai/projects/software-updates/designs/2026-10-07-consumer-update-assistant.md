---
tags: [design]
tracks:
- .wai/projects/software-updates/designs/matrix
---

# Design: consumer-update-assistant

Decision: 02-consumer-update-assistant
Date: 2026-10-07T21:58:03Z
Matrix: .wai/projects/software-updates/designs/matrix/

## Rationale

Provisional first product: help a consumer complete a contract-checked update or explicit migration through its existing resolver and CI. Measure actual updates, unsafe acceptance, false blocks, human effort, and release lag. Retain mining/authoring as a supporting decision; no comparative advantage is claimed before E3/E5.

## Trade-offs

The local assistant adds extractor and obligation maintenance to existing update tools. Its first supported ecosystem will have explicit coverage limits. An unresolved check may abstain, and a compatible interface does not establish all runtime behavior. Registry-wide native resolution remains a separate, broader option. This selection is an experiment direction, not evidence of superiority or a claim that runtime behavior is implemented.

## Decision-time snapshot — winning column

### 01-completed-updates

The proposed workflow carries a named target from candidate assessment through real resolution, validation, and a pinned change. It does not count a compatibility report alone as completion; effectiveness remains unmeasured.

### 02-range-friction

An opt-in path proposes out-of-range manifest changes and evaluates actual selected artifacts against consumer demand and required closure. Existing runtime/platform and policy constraints remain enforced; incremental update yield is unmeasured.

### 03-unsafe-acceptance

Contract checks add scoped evidence to existing checks. Dynamic gaps can abstain, and both extractors and authored predicates can be wrong; independent unsafe-acceptance rates remain unmeasured.

### 04-human-effort

Agents can mine/enrich contracts and repair consumer changes. Extraction, authoring, triage, and all unsuccessful attempts add costs whose net effect is unmeasured.

### 05-release-lag

The workflow evaluates the same desired target catalog against consumer demand and can propose direct or migrated updates. Time saved and blocked-target duration require experiments.

### 06-first-use

One supported local repository can use existing manifests and CI without upstream contracts or a registry. Extraction setup and time to first completed update are unmeasured.

### 07-migration-support

Direct updates and migrations are separate outcomes; candidate consumer/adapter edits are checked against protected intended behavior before delivery. Migration benefit is unmeasured.

## Product objective

Help a consumer complete useful software updates with less manual compatibility reasoning. Replace reliance on major/minor/patch labels for compatibility decisions with declared contracts and explicit evidence. Keep release names for discovery and exact artifact hashes for identity and reproducibility.

The user experience answers: "Which candidate revisions can this application use, and what is required to move to them?" Agents can draft contracts, discover candidates, and write migrations. The checks that determine a declared compatibility result remain deterministic under their pinned inputs.

## Proposed bounded workflow

This is a design, not implemented CLI behavior. Start with one supported ecosystem and existing package tooling.

1. Read the consumer's current manifest/lock, accepted obligations, supported environment, and update policy. Freeze the source/build context and desired target priorities. Candidate order expresses release/usefulness policy, never proof of compatibility.
2. Discover candidates from an authenticated catalog under those policies. Compare their declared provides and all new required dependencies with the consumer's actual demand. Report unsupported/dynamic usages and evidence limits explicitly.
3. Propose either a direct update, an explicit consumer/adapter migration, or refusal/unknown with reasons. A check alone does not modify the project. Crossing a host compatibility range requires a recorded manifest-change proposal under the project's existing authorization rules; other constraints remain independent.
4. In an isolated branch/workspace, apply the proposed manifest/pin change and invoke the real host resolver. Inspect the selected artifact and complete required closure rather than assuming the requested release was selected. Validate transitive and singleton constraints; resolution failure is an outcome, not an implicit fallback success.
5. Build/install the selected artifacts and run the scoped deterministic checks, existing tests, and independently specified consumer acceptance checks. Re-check all accepted obligations before considering candidate changes to them. Missing evidence yields unknown where required; errors remain errors.
6. Return a reviewable pinned manifest/lock diff, any explicitly labelled migration edits, and evidence bound to the actual artifacts. No production rollout is part of the first product. Compatible direct updates may proceed under an existing automation policy; intent changes follow existing review authority, without requiring a new per-edit permission step.

## Outcome semantics

Direct update means consumer implementation is unchanged; manifest/lock edits are allowed. Migration means consumer code or an adapter changes and is independently checked against preserved intended outcomes. Authorized requirement changes are separately recorded and cannot inflate backward-compatibility counts.

Compatibility status, policy eligibility, evidence coverage, and successful installation/delivery are different dimensions. An interface-level pass does not count as an update. An incompatible patch-labelled release may be refused, while an independently validated major-labelled release unused in its breaking areas may be proposed beyond the original range.

## Supporting decision and experiments

The [contract-production matrix](../../agentic-adoption/designs/matrix/problem.md) evaluates deterministic mining and authored obligations. Its [detailed design and E1-E7 protocol](../../agentic-adoption/designs/2026-10-07-mined-and-authored.md) defines the shared technical implementation hypotheses, protected checking envelope, four experimental arms, outcome table, and all metric denominators. The product and technical matrices answer different questions and can be revisited independently.

E1/E4 establish deterministic extraction and protection credibility. E2 measures useful contract authoring. E5 tests the real out-of-range update path, both directions of version-range misclassification, and direct versus migrated updates. E3 measures aggregate completed-update benefit under equal authority and budgets. E6 measures evidence reuse by work avoided and stale acceptance, irrespective of format. E7 tests actual adoption and update outcomes.

All arms receive the same candidate catalog, target priorities, allowed actions, trusted baseline rules, existing CI, and independent oracle. The only 2x2 treatment variables are mining and authored-obligation feedback. Existing tools may attempt major/range-changing updates; they are not artificially limited to make Wild appear useful.

## Selection rationale and reconsideration

The local update assistant is the first product candidate because its defined workflow produces the user-requested outcome while using existing ecosystem tooling. The native platform adds registry/publication prerequisites for this brownfield audience. The general checker can support the workflow but does not itself define additional candidate-to-delivery behavior. These are scope distinctions, not benchmark results.

Retain the status quo if Wild does not improve valid-update completion or effort at the preregistered risk margins. Prefer mining-only if authored obligations do not justify their cost. Reconsider a general checker only if it demonstrates update outcomes through existing automation. Evaluate the native platform separately when native adoption and shared contract distribution have evidence of demand.

WAI may warn that the baseline has no red cell. That is intentional: no baseline deficiency is invented to satisfy a color heuristic. Its limitations and the alternatives' benefits must be measured on the same tasks.

## Scope of this correction

This fixes the design-review findings and experiment definitions. It does not implement the runtime, execute E1-E7, or change deployed normative specs. Spec changes, particularly opt-in range-changing updates beyond the existing advice-only rule, require an OpenSpec change before runtime implementation. Experiments are tracked by Beads wild-1xk; runtime conformance remains wild-3rr.
