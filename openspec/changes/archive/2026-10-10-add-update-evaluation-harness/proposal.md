# Change: Add a controlled software-update evaluation harness

## Why

The existing simulations and prototype experiments do not establish that Wild helps users complete useful updates. We need reproducible runs through real host tooling, a strong existing-tool baseline, independent grading, and metrics that retain unknowns and failed effort.

## What Changes

- Add a frozen fixture and run protocol for E1 determinism, E4 protected checking, and the E5 end-to-end update experiment; use the same records for the later E3 held-out study.
- Compare the A-D mining/authoring factorial under identical enforcement, candidate access, action authority, target priorities, environments, and budgets.
- Grade actual resolved artifacts and consumer behavior outside the editable agent workspace; record oracle uncertainty and policy eligibility separately.
- Report candidate correctness, task completion, direct updates versus migrations, total effort, coverage, and policy failures with explicit denominators.
- Treat performance thresholds and market/adoption outcomes as hypotheses, not runtime guarantees. Do not claim broad value from synthetic fixtures.

## Impact

- New capability: wild-evaluate. No change to compatibility semantics or the v1 wire schema.
- Proposed implementation: experiments/update_eval.py, experiments/update_fixtures/, experiments/update-protocol.schema.json, and tests/test_update_eval.py. Keep existing simulations intact. Use Python for orchestration around the Rust CLI and actual Cargo.
- Tracking: Beads wild-aoq. Fixture/record work can start after this proposal is approved; end-to-end execution needs [local checks](../add-local-contract-checking/proposal.md) and [the update workflow](../add-consumer-update-workflow/proposal.md).
- Comparative research remains wild-1xk; product-alignment review is wild-6ig. Creating the harness is not completion of either research or broad runtime conformance.
- Source protocol: [revised E1-E7 design](../../../.wai/projects/agentic-adoption/designs/2026-10-07-mined-and-authored.md).

## Review status

Proposed, not approved or executed. First acceptance is reproducible synthetic conformance and a working measurement pipeline. Held-out recruitment, agent/model selection, risk margins, and statistical power are registered before the corresponding study, without blocking construction of the deterministic harness.

## Validation status

Strict OpenSpec validation passes. The overlay correspondence check reports 11 scenarios without test contracts; the harness implementation must supply those tests. The repository's all-items discovery gate has been corrected to include active proposal ids as well as spec ids, while retaining strict validation of both. This gate maintenance adds no runtime behavior. Beads owns task status; tasks.md is ordered guidance without duplicate checkboxes.
