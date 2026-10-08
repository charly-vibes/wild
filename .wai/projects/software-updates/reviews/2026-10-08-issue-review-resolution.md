---
tags: [review, resolution, issues]
tracks:
- openspec/changes/add-local-contract-checking
- openspec/changes/add-consumer-update-workflow
- openspec/changes/add-update-evaluation-harness
---

# Ticket review corrections

All four findings in the [issue review](2026-10-08-issue-review.md) are corrected. Beads wild-bi3 tracks the correction work; Beads remains the authority for implementation status. There are now 18 child tickets under the same three parent epics. Runtime and proposal-approval status are unchanged.

## Initial delivery path

New ticket **wild-aoq.5** supplies the narrow independently specified development corpus: a real Cargo compatible excluded-major/incompatible permitted-patch pair, plus formatting, unresolved-usage, unauthorized-weakening and authorized-transition examples. It can run without the Wild implementation or the full metric engine. Expected future checker behavior is labelled as an expectation, never recorded as executed conformance.

**wild-mh5.1** now depends on wild-aoq.5 instead of the full fixture cohort wild-aoq.2. The initial isolated Cargo runner **wild-nic.2** likewise uses the narrow fixture predecessor. The first direct-update path therefore does not transitively require either wild-aoq.1's metric engine or wild-aoq.2's complete E5 corpus.

The full cohort has not been dropped: wild-aoq.2 extends the narrow corpus and freezes separately held-out inputs before comparative trials. **wild-aoq.3** still depends on both the metric engine and complete cohort. Development fixtures are committed before miner work against them; sealed evaluation data remains unavailable for tuning or generation. The proposal delivery notes now explicitly distinguish these milestones.

This resolves **DEP-001** without removing independent expected outcomes or weakening comparative evaluation.

## Integration and independent audit

The existing final delivery tickets are explicitly DESIGN-lane implementation/release integration. They own scenario registration, dual-format specification reconciliation, required gate maintenance, release evidence, and authorized archive after actual delivery and successful checks. Their audit handoffs are new REVIEW-only children:

| Parent | Integration owner | Independent audit |
| --- | --- | --- |
| wild-mh5 | wild-mh5.5 | wild-mh5.6 |
| wild-nic | wild-nic.5 | wild-nic.6 |
| wild-aoq | wild-aoq.4 | wild-aoq.6 |

Audits depend on the delivered integration, inspect the resulting runtime tests and archived requirements, and record evidence in Beads. They do not implement missing behavior, create test registrations, modify the oracle, or archive changes. A different reviewer is used when available; limited independence must be disclosed otherwise. Defects return to the integration owner and prevent audit/parent completion. Integration does not depend on its own audit, so the handoff introduces no dependency cycle. This resolves **SCOPE-001**.

## Scenario ownership and coordination

The scenario **Unsupported dynamic usage is retained** now belongs to **wild-aoq.3**. Its acceptance requires an actual treatment's unknown result to survive attempt storage, independent grading and aggregation without becoming a detection or unsafe acceptance. Fixture expectations remain in wild-aoq.2. Injecting a synthetic expected record alone cannot close the integration scenario. This resolves **ALIGN-001** while preserving one owner for each of the 36 proposed scenarios.

All children whose exact paths overlap three or more scopes have explicit coordination notes. The narrow fixture ticket additionally identifies its nested-directory overlap with the larger fixture work. Notes call for comparing against base_commit, agreeing narrow edits, re-reading shared protocol changes, and re-anchoring only after validation. The parallel wild-mh5.2/wild-nic.1 branches explicitly coordinate CLI, formats, schema and reference edits. REVIEW tickets inspect rather than modify shared paths. No broad refactor or extra serial dependency was introduced to eliminate the warning. This resolves **PRE-002**.

## Verification

The live tracker was checked after editing, not only the temporary update script:

- All 18 children and three parent epics have source scope and commit anchors; child lane/complexity labels agree with metadata.
- All 36 proposal scenario names have exactly one implementation owner, including the moved dynamic-treatment scenario.
- The narrow fixture ticket has no technical predecessor. The first direct-update path excludes the broad metrics/cohort prerequisites; comparative execution still includes them.
- Each independent audit depends on its matching integration owner, and the graph has no dependency cycles.
- Descriptions list their actual blockers; header, TDD/Tidy First, anti-goal and future-meter disclosures remain present.
- Shared-path coordination notes cover every exact overlap of three or more child scopes, plus the nested bootstrap fixture scope.
- Beads lint passes for all 22 checked records, including the correction issue.
- Strict OpenSpec validation passes for all three changes and nine existing specs; deployed correspondence checks remain clean.

Future pytest meters are still future tests. These corrections do not claim runtime implementation, behavioral test passes, product-value evidence, or a resolution of the separate product-alignment review wild-6ig. The original four ticket-quality findings are resolved; existing proposal approval remains the next implementation boundary.
