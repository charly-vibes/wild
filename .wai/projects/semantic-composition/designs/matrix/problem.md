# Decision matrix: reusable assemblies with preserved public obligations

Which representation lets us reuse and replace assemblies while preserving explicit public obligations, with an auditable amount of checking work?

The matrix is a research comparison, not an adoption decision. All approaches receive the same accepted obligations, independent oracle, complete dependency inputs, candidate authority, fixtures, policy and budgets. No approach earns extra assurance merely by having a wrapper or using Wild's format.

Semantic levels S0–S3 are defined in the [investigation](../../research/2026-10-09-investigation.md). Compare H0/H1/H2 first at S1. S2 and S3 add semantic capability and must be evaluated as separate factors, not bundled exclusively into H2.

| Approach | Boundary representation | Fit with current v1 | Behavioral basis | Reuse cost hypothesis | Decision |
| --- | --- | --- | --- | --- | --- |
| H0: flattening | Explicit full graph; root boundary supplied to the experiment | Existing assembly design, runtime still absent | Same independent oracle as H1/H2 | Simple representation; repeated boundary configuration may cost effort | Control |
| H1: authored wrapper | Ordinary authored public contract plus explicit internal assembly and experimental mapping | Existing contracts can describe a wrapper; assembly mapping/evidence linkage needs an external versioned record | Public laws reevaluated against the actual assembly | Lower initial machinery; maintaining mappings may cost more | First candidate, not selected winner |
| H2: first-class composite | Nested public boundaries and child assembly commitments | New protocol/schema and flattening/identity rules required | Same public laws unless a separately supported S2/S3 profile is used | Reusable boundaries may reduce repeated authoring; invalidation/proof costs unknown | Candidate after H1/control evidence |

## Criteria and evidence rules

| Criterion | Question | Measurement / hard condition |
| --- | --- | --- |
| C1 boundary fidelity | Are all external requirements and public events preserved? | No hidden required dependency/event; case C04/C08 failures block promotion |
| C2 behavioral honesty | Does the method catch relevant same-shape changes without overclaiming? | Zero unsafe accepts in frozen negative cases; report unknowns and false refusals separately |
| C3 identity and closure | Are sharing, relations, artifacts and claims checked across boundaries? | C05–C07/C09–C11/C16; no stale or incomplete result accepted |
| C4 bounded portability | Is meaning preserved across supported implementations? | Same finite trace/domain oracle, explicit adapters; C12–C14; unsupported cases stay unknown |
| C5 effort and reuse | Does packaging reduce work at equal correctness? | Record authoring minutes, changed declarations, checks rerun, runtime and evidence bytes per case |

There is no weighted score. Safety/identity conditions are hard gates; efficiency is compared only among candidates that meet them. No numerical effort threshold is set without pilot measurements and a user-valued target. Record all failed attempts and unknowns. Synthetic fixture success supports only a follow-up experiment, not adoption effectiveness.

Color markers in approach directories: green = mechanism directly addresses criterion, yellow = additional assumptions/design needed, red = absent at that semantic level, neutral = no comparative evidence. Colors are provisional design judgments, never executed outcomes. Unknown measurements stay unknown; neutral is not a pass. Detailed executable cases are in the [case matrix](../2026-10-09-case-matrix.md).

## Factorial comparison

| Representation | S0 structural | S1 boundary laws | S2 bounded profile | S3 derived refinement |
| --- | --- | --- | --- | --- |
| H0 flat | Specified; toy subset | Can host same oracle; no full runtime | Research | Research |
| H1 wrapper | Wrapper contract expressible; mapping extra | Initial research candidate | Research | Research |
| H2 composite | New representation required | No automatic gain over H0/H1 | Research | Research; nesting does not supply a proof |

Keep surface contract constant while varying internal decomposition, then keep decomposition constant while varying language. This avoids attributing a stronger oracle to the choice of hierarchy.
