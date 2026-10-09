# Decision matrix: reusable assemblies with preserved public obligations

Which representation lets us reuse and replace assemblies while preserving explicit public obligations, with an auditable amount of checking work?

The matrix is a research comparison, not an adoption decision. All approaches receive the same accepted obligations, independent oracle, complete dependency inputs, candidate authority, fixtures, policy and budgets. No approach earns extra assurance merely by having a wrapper or using Wild's format.

Semantic levels S0–S3 are defined in the [investigation](../../research/2026-10-09-investigation.md). P1 compares representations at S1 with S0 closure checks; P2 adds S2 portability; P3 adds S3 refinement. The [comparison protocol](../2026-10-09-comparison-protocol.md) defines arms, phase gates, cost accounting and readiness. S2/S3 are separate factors, not features reserved for H2.

| Approach | Boundary representation | Fit with current v1 | Behavioral basis | Reuse cost hypothesis | Decision |
| --- | --- | --- | --- | --- | --- |
| H0: flattening | Full instance graph plus experiment-only root mapping per consumer | Existing assembly design, runtime still absent | Same oracle as H1/H2 | Repeated configuration may cost effort | Control |
| H1: authored wrapper | Reusable public contract and external mapping; checker receives flat closure | Existing contracts describe wrapper; mapping/evidence linkage needs external versioned record | Same oracle against same assembly | Reuse may offset mapping maintenance | First candidate, not selected winner |
| H2: first-class composite | Schema-native nested boundary reference; expander produces equivalent flat closure | New protocol/schema and flattening rules required | Same oracle; S2/S3 evaluated separately | Reuse may offset implementation/invalidation costs | Eligible independently of H1 results once entry checks pass |

## Criteria and evidence rules

| Criterion | Question | Measurement / hard condition |
| --- | --- | --- |
| C1 boundary fidelity | Are all external requirements and public events preserved? | No hidden required dependency/event; case C04/C08 failures block promotion |
| C2 behavioral honesty | Does the method catch relevant same-shape changes without overclaiming? | Zero unsafe accepts in frozen negative cases; report unknowns and false refusals separately |
| C3 identity and closure | Are sharing, relations, artifacts and claims checked across boundaries? | C05/C07 mandatory from P1; C06/C09a–e/C10/C11/C16 also required from P1 |
| C4 bounded portability | Is meaning preserved across supported implementations? | P2 requires C12; P1 makes no portability claim. C13 unsupported-input controls and C14 bounded progress apply from P1 |
| C5 effort and reuse | Does packaging reduce work at equal correctness? | Protocol ledger separates setup, authoring, updates, repair, execution and exit; cold/reused costs and amortization are explicit |

There is no weighted score. All cases marked required for a phase are hard gates, including C05/C07 in P1. Deferred cases do not affect that phase's denominators or establish its claims. Efficiency is compared only among candidates meeting the same required cases. No numerical effort threshold is set without pilot measurements and a user-valued target. Record all failed attempts and unknowns. Synthetic fixture success supports only a follow-up experiment, not adoption effectiveness.

Color markers in approach directories: green = mechanism directly addresses criterion, yellow = additional assumptions/design needed, red = absent at that semantic level, neutral = no comparative evidence. Colors are provisional design judgments, never executed outcomes. Unknown measurements stay unknown; neutral is not a pass. Detailed executable cases are in the [case matrix](../2026-10-09-case-matrix.md).

## Factorial comparison

| Representation | S0 structural | S1 boundary laws | S2 bounded profile | S3 derived refinement |
| --- | --- | --- | --- | --- |
| H0 flat | Specified; toy subset | Can host same oracle; no full runtime | Research | Research |
| H1 wrapper | Wrapper contract expressible; mapping extra | Initial research candidate | Research | Research |
| H2 composite | New representation required | No automatic gain over H0/H1 | Research | Research; nesting does not supply a proof |

Within a representation comparison, fix the component graph, artifacts, public contract, sharing, bindings, oracle, language and ordered replacement workload. Change only H0/H1/H2 representation and its declared authoring/expansion workflow. Study another decomposition in a separate block containing the same arms. Study language in P2 blocks with fixed decomposition. Freeze tooling and permitted automation before each block.
