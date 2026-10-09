# Rule of 5 — matrix resolution review

**Work reviewed:** revised [matrix](../designs/matrix/problem.md), [decision](../designs/matrix/decision.md), [comparison protocol](../designs/2026-10-09-comparison-protocol.md), criteria/cells and [case catalog](../designs/2026-10-09-case-matrix.md).
**Baseline:** [five findings at 3d8dc08](2026-10-09-matrix-rule-of-5.md), report committed as 760a9d5.
**Tracking:** wild-9co.6. Scope: fix the requested design findings, not implement the experiment or change v1.

## Summary

Five original findings addressed: two HIGH, three MEDIUM. No new defects found in the resolution passes. Architecture selection remains open; no experimental result or runtime guarantee was added.

Both HIGH resolution claims passed mechanical quote/location checks and TypeSafe verification at confidence 1.00 (threshold 0.8). [Request and reviewed snapshot](evidence/matrix-fix-typesafe-request.json); [response](evidence/matrix-fix-typesafe-response.json), model jev-1.13.0. This verifies textual support for the resolution claims, not runtime correctness. MEDIUM resolutions remain UNVERIFIED by TypeSafe and use self-reported inspection. Eligible measured false-positive rate: 0/(2+0); sample size two.

## STAGE 1: DRAFT

Assessment: The experiment now defines the artifacts and authoring operation that distinguish H0/H1/H2 while fixing the graph and oracle.

Major Issues: No new finding. M-DRAFT-001 addressed in protocol **Fixed treatments** and matrix **Factorial comparison**. Ordinary baseline automation is permitted; its setup cost is recorded. Decomposition and language vary in separate matched blocks. H2 entry depends on having runnable machinery, not a favorable H1 outcome.

Shape Quality: GOOD. Treatment code and fixture manifests are future deliverables.

## STAGE 2: CORRECTNESS

Issues Found: No new finding.

- M-CORR-001 addressed: C05/C07 are required from P1 in protocol, decision, criterion and case records; stale provisional scope text removed from active documents.
- M-CORR-002 addressed: explicit phase table requires 18 named cases in P1, 19 in P2, 20 in P3. C12 starts in P2, C15 in P3; C13's unsupported-input controls are described separately by phase. No candidate may waive an R case after seeing results.

Correctness Quality: GOOD as a document protocol.

```text
New CRITICAL issues: 0
Total new issues: 0
New issues vs Previous Stage: undefined (0/0; not fabricated as a percentage)
Estimated false positive rate: not used; eligible measured rate 0/2
Status: CONTINUE through remaining resolution dimensions
```

## STAGE 3: CLARITY

Issues Found: No new finding. M-CLAR-001 addressed in protocol **Cost ledger and reuse workload**. Shared setup, arm setup, authoring, updates, review/repair, execution and exit are separate; unknown sunk effort is not zero. B consumers and U updates determine explicit same-unit amortization, with raw totals and cold/reused conditions retained.

Clarity Quality: GOOD. PHASE_READY is separated from architecture selection; unknown costs or unset confirmatory margins cannot select a winner.

```text
New CRITICAL issues: 0
Total new issues: 0
New issues vs Previous Stage: undefined (0/0)
Estimated false positive rate: MEDIUM resolution unmeasured
Status: CONTINUE through edge-case verification
```

## STAGE 4: EDGE CASES

Issues Found: No new finding. M-EDGE-001 addressed by C09a–e: renaming, empty identity/coverage, cyclic closure, invalid mapping and grouping associativity. Shared identity remains C05. These are required from P1, and cyclic closure does not imply runtime progress.

Edge Case Coverage: GOOD at protocol level. The catalog has 16 families and 20 named case definitions; multi-outcome definitions still need separately frozen executable fixture variants. No new case is labelled executed.

```text
New CRITICAL issues: 0
Total new issues: 0
New issues vs Previous Stage: undefined (0/0)
Estimated false positive rate: MEDIUM resolution unmeasured
Status: CONTINUE to final consistency check
```

## STAGE 5: EXCELLENCE

Final Polish Issues: None. Active README, investigation, descriptions, criteria and affected cells agree with revision 2. Prior review records and TypeSafe snapshots are retained as history.

Excellence Assessment:
- Structure: GOOD
- Correctness: GOOD within document scope
- Clarity: GOOD
- Edge Cases: GOOD protocol coverage; execution remains future work
- Overall: GOOD

Production Ready: WITH_NOTES — ready for fixture/run-manifest construction, not production software or architecture selection.

## Validation

[Consistency results](evidence/matrix-fix-validation.json) record 20 unique definitions, exact catalog/phase-table agreement, required counts 18/19/20, mandatory C05/C07 and C09a–e from P1, and 15 complete matrix cells. Active-document links and quoted verification evidence were checked. These checks inspect documents; they do not run the planned H comparisons.

Verdict rules were checked against these examples:

| Example | Defined result |
| --- | --- |
| P1 required variants all match; C12/C15 absent | PHASE_READY for P1; no portability/refinement claim |
| P1 C05 implementation missing; other required outcomes match | INCOMPLETE |
| Supported C02 positive returns unknown | FAILED |
| Executed C13 well-formed unsupported control returns expected unknown | That diagnostic variant passes; no behavioral conformance inferred |
| Negative case refuses with wrong expected classification | FAILED |
| All required variants match but comparative cost is unknown | PHASE_READY; architecture selection INCONCLUSIVE |

## Verdict

READY for the next research step. Five requested findings are resolved; final pass found no new issues. Numeric early-stop ratios are undefined across zero-new-finding passes, so no artificial convergence percentage is claimed.

Next work remains in wild-9co.2–wild-9co.4: construct the protected oracle and runnable arms, freeze concrete positive/negative fixture variants and expected fields, then execute. Production schema changes still require OpenSpec. This review does not approve an architecture or claim that an experiment already passed.
