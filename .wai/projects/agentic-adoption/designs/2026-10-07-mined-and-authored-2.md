---
tags: [design]
tracks:
- .wai/projects/agentic-adoption/designs/matrix
---

# Design: mined-and-authored

Decision: 04-mined-and-authored
Date: 2026-10-07T22:01:39Z
Matrix: .wai/projects/agentic-adoption/designs/matrix/

## Rationale

Supporting technical choice for the software-updates product: combine deterministic facts with optional authored obligations under identical protected enforcement across all experimental arms. Comparative reuse and update effectiveness remain unmeasured; simplify to mining-only or existing tools if controlled experiments do not justify the combination.

## Trade-offs

Both extractors and authored obligations need maintenance. Passing structural checks and samples does not establish unmodelled behavior; incomplete demand remains explicit. The combination is retained provisionally and must outperform equal-budget ordinary tests or mining alone on independently valid updates before its additional cost is justified.

## Role and current detailed design

This is a technical subdecision supporting the [software-update product decision](../../software-updates/designs/matrix/decision.md). The [revised detailed design and experimental protocol](2026-10-07-mined-and-authored.md) contains the current workflow, common enforcement across arms A-D, explicit outcome definitions, opt-in range-change experiment, and outcome-based evidence-reuse comparison.

All evidence-reuse markers are neutral until measured. WAI's warning that the status quo has no red cell is intentional: absence of a Wild representation is not evidence of inferiority.

## Decision-time snapshot — winning column

### 01-first-use

Initial supported structural feedback needs mined facts and repository inputs; authored obligations, a registry, and provider adoption are optional.

### 02-independent-checks

The same common trusted invocation protects accepted tests, policy, scope, miner/checker inputs, and authored obligations. Authored text cannot overwrite facts, and changed evidence inputs invalidate results. The combination adds no protection capability withheld from other arms.

### 03-behavior-coverage

Authored obligations add semantics to mined interfaces. Dynamic completeness and general equivalence remain unresolved outside supported analysis or evidence domains.

### 04-feedback-latency

Changed-boundary checks and content-addressed caches are proposed; cold/warm latency and incremental/full equivalence require measurement.

### 05-maintenance

Both extractors and authored obligations need maintenance. Agents can draft and repair them; net attention and compute cost remain unmeasured.

### 06-evidence-reuse

Facts, obligations, coverage, results, and counterexamples bind explicit inputs. E6 compares repeated work avoided, retrieval cost, and stale acceptance with existing logs, tests, and caches under equal access and budgets. Relative reuse benefit is unmeasured.
