# Rule of 5 Review - Final Report

**Work Reviewed:** design matrix at commit `3d8dc08`: [problem](../designs/matrix/problem.md), [decision](../designs/matrix/decision.md), all three approach descriptions, 15 cells, five criteria, and the [16-case catalog](../designs/2026-10-09-case-matrix.md). The linked investigation was read to avoid flagging matters it already explains.

**Convergence:** Stage 5 — no additional findings in the final pass. This is convergence of the review, not acceptance of the matrix: five revisions remain open.

## Summary

The matrix is a sound research map. It correctly separates representation from behavioral assurance, preserves unknowns, includes positive controls, and does not claim that the reservation probe chooses an architecture. It is not yet an unambiguous comparative experiment: two gate-definition problems can change which approach qualifies, and treatment/cost definitions leave room for uneven comparisons.

Total Issues by Severity:
- CRITICAL: 0
- HIGH: 2 — resolve before freezing the comparison
- MEDIUM: 3 — define before corresponding experiment execution
- LOW: 0

Both HIGH findings passed the mechanical existence/verbatim-evidence check and were verified in one TypeSafe request: M-CORR-001 at confidence 0.97 and M-CORR-002 at 0.95, above the 0.8 threshold. [Request with source snapshot](evidence/matrix-typesafe-request.json); [response](evidence/matrix-typesafe-response.json), returned model jev-1.13.0. Measured false-positive rate is 0/(2+0) = 0%; the three MEDIUM findings remain UNVERIFIED and are excluded. This is a finding-support check, not independent validation of the proposed remedies or experimental results.

The matrix files have not been rewritten by this review. The following remedies are proposals for a focused revision, not new architecture decisions.

## STAGE 1: DRAFT

Assessment: The alternatives have recognizable architectural intent, but their operational differences are not specified tightly enough to compare effort. This stage establishes what must remain fixed before checking the gate logic.

Major Issues:

[M-DRAFT-001] MEDIUM — matrix/problem.md:11–13,37; approaches/*/_description.md:1 — UNVERIFIED
Description: H0 already has a supplied root boundary; H1 has an authored public boundary plus mapping; H2 adds a first-class representation. The documents do not define the concrete authoring/reuse operation that separates those boundaries. The final instruction varies internal decomposition, which is a separate experimental factor from representing the same decomposition flat or nested.
Evidence: H0 has a “root boundary supplied to the experiment”; H1 has “Ordinary authored public contract plus explicit internal assembly and experimental mapping”; line 37 says “Keep surface contract constant while varying internal decomposition”.
Recommendation: Define a minimal artifact/workflow for each arm, then represent the same component graph, artifacts, mappings, oracle and replacement sequence in all arms. For example: H0 supplies a flat assembly and experiment boundary per consumer; H1 supplies a reusable authored public contract and external mapping; H2 supplies a schema-native nested boundary that flattens to the same assembly. Specify what reuse and automation each arm permits. Vary decomposition in a separate blocked comparison, not simultaneously with representation. These are proposed treatment definitions, not claims of existing implementations.

Shape Quality: GOOD as a research map; FAIR as an executable comparison.

## STAGE 2: CORRECTNESS

Issues Found:

[M-CORR-001] HIGH — matrix/problem.md:21,25; matrix/decision.md:9; criteria/03-identity-closure.md:1 — VERIFIED (0.97)
Description: C05/C07 have inconsistent gate status. The matrix declares identity checks hard gates while the decision and criterion text leave these two cases' initial-pilot status open.
Evidence: problem.md says “Safety/identity conditions are hard gates”; its identity row includes C05–C07. decision.md asks “whether exact composite evidence linkage and shared singleton identity must be hard conditions for the initial pilot, or remain later cases”.
Impact: Two evaluators can give different promotion verdicts for the same results, or exclude a failing provisional case after observing it.
Recommendation: Freeze each case as required, deferred, or out of scope for each experiment phase before running candidates. Proposed resolution: any pilot that reuses behavioral evidence requires C07; a pilot that supports shared instances requires C05. A restricted pilot may forbid sharing explicitly, test that unsupported input refuses, and defer support for shared assemblies. Defer capability support rather than silently waive identity correctness. Keep the matrix, decision and criterion cell in agreement.

[M-CORR-002] HIGH — matrix/problem.md:7,22; case-matrix.md:18,32 — VERIFIED (0.95)
Description: The initial comparison is S1, but portability cites C12–C14 and the positive-acceptance rule names C12 without a phase applicability rule. C12 explicitly requires S2 cross-language execution.
Evidence: “Compare H0/H1/H2 first at S1.” versus “C02 and the valid controls for C03/C05/C09/C12 must demonstrate useful acceptance.” The C12 row identifies S2 and says it is not executed.
Impact: An S1 candidate can be blocked on a deliberately later capability, or a reviewer can informally remove a gate. “Applicable” is not a reproducible selection rule by itself.
Recommendation: Add a phase × case applicability table. Phase P1 compares H0/H1 at S1 and includes their S0 closure obligations; P2 adds the S2 language/profile cases; P3 adds S3 assumption-discharge cases. Define NOT APPLICABLE separately from NOT EXECUTED and UNKNOWN, with a frozen rationale. Require positive controls only for the declared phase; prohibit describing P1 success as portability or refinement success. Specify an entry criterion for an H2 trial that does not presume H1 wins.

Correctness Quality: FAIR until both gate definitions are reconciled.

```text
New CRITICAL issues: 0
Total new issues: 2
New issues vs Previous Stage: +100% (2 vs 1; issue-rate ratio 200%)
Estimated false positive rate: not used; measured eligible rate 0/2
Status: CONTINUE
```

## STAGE 3: CLARITY

Issues Found:

[M-CLAR-001] MEDIUM — matrix/problem.md:23; criteria/05-effort-reuse.md:1; case-matrix.md:26,34 — UNVERIFIED
Description: “Authoring effort”, “execution cost”, and “initial construction” do not define cost attribution. H2 explicitly needs a new protocol/schema, while the cost criterion names authoring minutes and check runs; it does not state whether building that machinery, adapters or mappings is charged or amortized.
Impact: Prebuilt automation can look cheaper than manual work because its construction cost is outside the measured window. Cold setup, repeated updates and failures can be aggregated differently across arms despite equal nominal budgets.
Recommendation: Record separate one-time implementation/setup, per-boundary authoring, per-update editing, review/repair, check execution, and migration costs. Count failed attempts under the existing rule. Declare the number of consumers, boundaries and update repetitions over which setup is amortized; report cold and reused runs separately, with fixed cache conditions. Keep human minutes and compute resources separate instead of inventing a conversion. State the cost ledger before measuring, then choose practical thresholds before a confirmatory run as already proposed.

Clarity Quality: GOOD on assurance terminology; FAIR on measurement semantics.

```text
New CRITICAL issues: 0
Total new issues: 1
New issues vs Previous Stage: -50% (1 vs 2; issue-rate ratio 50%)
Estimated false positive rate: MEDIUM finding unmeasured; eligible measured rate remains 0/2
Status: CONTINUE
```

## STAGE 4: EDGE CASES

Issues Found:

[M-EDGE-001] MEDIUM — case-matrix.md:15 (C09); docs/wild-formats-v1.md:60–62 — UNVERIFIED
Description: The representation-equivalence case covers one two-layer flattening and injective renaming. The catalog does not cover empty assembly identity, cyclic dependency closure, or a malformed non-injective boundary mapping, although current v1 explicitly defines empty assemblies, permits dependency cycles and rejects name collisions.
Scenario: A flattening implementation works for the reservation tree but loops on cyclic dependencies, duplicates a reachable instance, merges colliding ids, or changes empty-assembly coverage from null into a false numerical claim.
Impact: Passing the listed C09 fixture would not establish preservation of the existing assembly domain. These are missing evaluation cases, not observed implementation bugs.
Recommendation: Split C09 into named controls: empty identity with vacuous coverage, injective renaming invariance, explicit shared instance, cyclic closure reaching a fixed point, and invalid mapping/name-collision refusal. Keep each input and expected verdict separate. If P1 intentionally supports only acyclic nonempty graphs, declare that scope and test refusal of the excluded inputs; do not claim general v1-preserving flattening.

Edge Case Coverage: GOOD for behavioral/evidence failures; FAIR for representation algebra boundaries.

```text
New CRITICAL issues: 0
Total new issues: 1
New issues vs Previous Stage: 0% change (1 vs 1; issue-rate ratio 100%)
Estimated false positive rate: MEDIUM finding unmeasured; eligible measured rate remains 0/2
Status: CONTINUE
```

## STAGE 5: EXCELLENCE

Final Polish Issues: No new findings. Rechecked the linked investigation, all cells and case decision rules. Did not count the following as defects: identical provisional colors, lack of a weighted score, not-yet-measured benefit thresholds, or an absent generic refinement engine. The matrix explicitly discloses those limits. The linked investigation already defines safety-trace inclusion separately from completion, so that is not a missing-semantic-definition finding here.

Excellence Assessment:
- Structure: GOOD research organization; treatment definition needs revision
- Correctness: FAIR gate consistency
- Clarity: GOOD evidence labels; cost attribution needs revision
- Edge Cases: GOOD failure catalog; algebra cases need scoping
- Overall: GOOD foundation, not ready to freeze as a comparative protocol

Production Ready: NO for comparative execution/adoption; usable for discussion and bounded exploratory probes.

Final convergence observation: zero new findings versus one in Stage 4, zero new CRITICAL findings, measured eligible false-positive rate 0/2. Findings stabilized; open findings remain actionable. No new finding fell below the TypeSafe gate, so this review introduces no additional human-confidence escalation. Prior unresolved architecture judgments remain open.

## Top 3 Critical Findings

No CRITICAL findings. The three most consequential items are:

1. M-CORR-001 — inconsistent initial-pilot gates. Freeze C05/C07 applicability before measuring outcomes.
2. M-CORR-002 — S1 comparison lacks phase-specific portability gates. Separate P1/P2/P3 eligibility and claims.
3. M-DRAFT-001 — representation treatments are not operationally fixed. Compare the same graph before varying decomposition.

## Stage-by-Stage Quality

- Stage 1 (Draft): GOOD research map / FAIR experimental treatment definition.
- Stage 2 (Correctness): FAIR; two verified gate issues.
- Stage 3 (Clarity): GOOD assurance labels / FAIR cost accounting.
- Stage 4 (Edge Cases): GOOD behavioral catalog / FAIR algebra-domain coverage.
- Stage 5 (Excellence): no new findings; verdict unchanged.

## Recommended Actions

1. Freeze H0/H1/H2 treatment definitions and a P1/P2/P3 case-applicability table; update the matrix, decision and criteria together.
2. Add a cost ledger with amortization and cache conditions before recording comparative effort.
3. Add named C09 algebra controls or explicit supported-domain exclusions, then rerun this review on the revised matrix.

## Verdict

NEEDS_REVISION

**Rationale:** The matrix asks the right questions and avoids claiming unsupported guarantees. Its gate statuses and experimental treatments still allow inconsistent judgments, so it should guide discussion but not yet decide which representation wins.
