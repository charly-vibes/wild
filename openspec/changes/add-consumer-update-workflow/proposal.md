# Change: Add an opt-in consumer update workflow

## Why

The adoption specification currently provides compatibility advice while preserving the host resolver's choice. Users need to turn that advice into a validated, pinned update, including candidates excluded by the original version range. An interface report alone does not deliver that outcome.

## What Changes

- Add explicit plan and evaluate commands for a named Cargo candidate. Planning is read-only; evaluation applies a committed manifest proposal in an isolated workspace under existing project authority.
- Preserve the original advice-only behavior of check/observe. Cargo resolves the proposed manifest; Wild never substitutes a different artifact behind the host resolver.
- Inspect the actual selected target and full closure, enforce non-compatibility constraints, build/test, and return a reviewable pinned diff with bound evidence.
- Distinguish direct updates, supplied consumer/adapter migrations, accepted intent changes, refused candidates, unknowns, and execution errors.
- Start with an explicit candidate from a pinned local catalog. Automatic release discovery/ranking, migration generation, production deployment, and the native registry resolver are deferred.

## Impact

- Affected specs: wild-adopt and wild-compose. Clarify the mode scope of advice and registry tip selection without weakening either guarantee.
- Proposed implementation: src/update.rs and src/cargo_host.rs, tests/runtime/update/, and the local-1 schema/reference introduced by add-local-contract-checking. Reuse its checker and report format.
- Implementation depends on [local checking](../add-local-contract-checking/proposal.md); tracking is Beads wild-nic, dependent on wild-mh5.
- Validation uses E5 fixtures supplied by [the evaluation proposal](../add-update-evaluation-harness/proposal.md). Its infrastructure can be prepared independently; a full run needs this workflow.
- Product basis: [consumer update design](../../../.wai/projects/software-updates/designs/2026-10-07-consumer-update-assistant.md).

## Review status

Proposed, not approved or implemented. Success is a real pinned update validated for the named domain, not universal compatibility or deployment approval. Runtime work starts after proposal review under openspec/AGENTS.md.

## Validation status

Strict OpenSpec validation passes. The change-overlay correspondence check reports 12 scenarios without test contracts; these are future runtime obligations. The existing spec suite remains required. tasks.md supplies ordered acceptance guidance and Beads owns task status, so the absence of OpenSpec checkbox counts is intentional.
