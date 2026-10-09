# Change: Add bounded local contract checking

## Why

Wild has a normative design and Python prototypes, but no executable local workflow that checks a candidate against a consumer's accepted obligations. The first product needs useful feedback in an existing repository before registry or publisher adoption.

## What Changes

- Implement a Rust CLI/library for a declared Rust/Cargo analysis profile, deterministic extraction, consumer demand, and local checks using existing v1 contracts, manifests, policies, law results, and envelopes.
- Keep mined facts, accepted obligations, candidate obligation changes, and evidence separate. Human and agent authors use the same format and acceptance rules.
- Pin the accepted base, scope, checker, policy, and test/law harness outside candidate control. Missing analysis remains Unknown; candidate changes cannot erase accepted obligations.
- Add runtime requirements to wild-extract, wild-adopt, and wild-tiers. Introduce a separately versioned local request/report schema during implementation; do not add undocumented fields to v1 documents.
- Deliver only the supported profile. Full v1 runtime conformance, global lineage publication, registry certificates, deployment, and incremental caching remain outside this slice.

## Impact

- Affected specs: wild-extract, wild-adopt, wild-tiers. Existing design-contract requirements remain intact.
- Proposed implementation paths: root Cargo.toml, src/{main,lib,formats,extract,check,harness}.rs, tests/runtime/, schemas/wild-local-v1.schema.json, docs/wild-local-v1.md. Introduce modules only as responsibilities require them.
- Preserve prototype/wild_proto.py as a source of regression cases, not as a conforming implementation.
- Tracking: Beads wild-mh5; bounded prerequisite for wild-nic, not completion of broad runtime issue wild-3rr.
- Design basis: [product decision](../../../.wai/projects/software-updates/designs/2026-10-07-consumer-update-assistant.md) and [technical design](../../../.wai/projects/agentic-adoption/designs/2026-10-07-mined-and-authored.md).

## Review and sequencing

Proposed, not approved or implemented. Rust/Cargo is the proposed first ecosystem. Start with the independent fixtures and trusted invocation, then extraction and checking; connect one real update before extending language coverage. The [evaluation harness](../add-update-evaluation-harness/proposal.md) can prepare fixtures in parallel. Product-alignment review remains recorded in wild-6ig; proposal approval should explicitly resolve that decision before comparative product claims.

## Validation status

Strict OpenSpec validation passes. The change-overlay correspondence check reports 13 scenarios without test contracts; these are future runtime obligations, not executed tests. Existing spec gates remain required. tasks.md is ordered acceptance guidance; Beads owns progress, so OpenSpec's checkbox task count is intentionally empty.
