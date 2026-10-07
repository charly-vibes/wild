# Product decision context

Date: 2026-10-07. This is a revised design hypothesis; no runtime or comparative experiment is complete.

## Observed problem

The user started Wild to make software updates easier through checked compatibility in place of version-label assumptions. The original umbrella spec retains that objective, while the first adoption matrix optimized generic agent-patch feedback. Its criteria did not count completed updates.
The recorded Python experiment shows both a failure allowed by declared ranges and failures missed by the prototype. These motivate testing both directions of label/range disagreement, not replacing existing bounds without evidence.
The [Rule-of-5 review](../../agentic-adoption/reviews/2026-10-07-rule-of-5.md) found objective drift, a confounded protection treatment, format-based reuse bias, ambiguous outcomes, and no explicit out-of-range completion experiment.

## Diagnosis

Hypothesis A: consumer-specific checks avoid unnecessary upgrade blocks. Needs actual resolution and consumer validation.
Hypothesis B: deterministic feedback reduces agent repair and migration effort. Needs equal-budget experiments with ordinary tests available to the baseline.
Hypothesis C: a native contract platform removes more versioning friction but adds first-use requirements. Compare that product route without presuming local adoption proves native value.
Hypothesis D: existing automation plus CI may already meet the need. Keep it as a capable baseline and accept a null result.

## Scope

Start in one supported ecosystem with isolated, reviewable manifest/lock/consumer changes. Candidate contract production is a separate technical decision. A direct update preserves consumer implementation; a migration changes it or adds an adapter. Both require exact artifact identities and independent validation.
The first study does not deploy to production or implement the global registry. The broader native model remains a long-term alternative whose value requires separate evidence.

## Direction and validation

The local consumer-update assistant is selected provisionally because its defined operation ends in the outcome being evaluated, while allowing brownfield adoption. Its performance and net maintenance cost remain unknown.
The shared E1-E7 protocol lives in the revised technical design; E3 and E5 now center completed software updates. E5 establishes an isolated opt-in out-of-range procedure before the larger trial.
