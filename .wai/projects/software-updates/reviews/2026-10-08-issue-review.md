---
tags: [review, issues]
tracks:
- openspec/changes/add-local-contract-checking
- openspec/changes/add-consumer-update-workflow
- openspec/changes/add-update-evaluation-harness
---

# Issue tracker review

System: Beads. Scope: 14 implementation/review tickets and their three parent epics, wild-mh5, wild-nic and wild-aoq. Reviewed repository anchor: bca2ec11bb63bc11b75765847c784e301ecfb003. Tracker contents were collected directly with bd show, including descriptions, acceptance criteria, metadata and dependencies.

Sources: [local checking](../../../../openspec/changes/add-local-contract-checking/proposal.md), [consumer updates](../../../../openspec/changes/add-consumer-update-workflow/proposal.md), and [evaluation harness](../../../../openspec/changes/add-update-evaluation-harness/proposal.md), including their designs, tasks and deltas.

Verdict: **NEEDS_UPDATES**, not a wholesale replan. The tickets describe useful outcomes and cover every proposed scenario name. Three MEDIUM findings concern sequencing, lane boundaries and ownership of an integration scenario. One LOW finding groups shared-file coordination risk. No CRITICAL or HIGH finding was established. Follow-up is Beads **wild-bi3**; this review does not change the original tickets' implementation scope or dependencies.

## Pass 0: Mechanical pre-flight

All 17 tickets have metadata.files and base_commit. All anchors equal the reviewed HEAD, so there are no missing-metadata or stale-scope findings. bd lint reports no template warnings and bd dep cycles reports no cycles. The three XL epics explicitly identify themselves as containers rather than executable XL slices; their appearance in bd ready is not treated as permission to execute them.

### PRE-002 — LOW: Shared files need coordination notes

Affected tickets and shared paths:

| Path | Tickets |
| --- | --- |
| src/main.rs | wild-mh5.1, wild-mh5.2, wild-nic.1 |
| src/formats.rs | wild-mh5.1–4, wild-nic.1–2 |
| schemas/wild-local-v1.schema.json | wild-mh5.1–4, wild-nic.1–4 |
| docs/wild-local-v1.md | wild-mh5.1–4, wild-nic.1, wild-nic.4 |
| src/check.rs | wild-mh5.2–4, wild-nic.3–4 |
| src/update.rs | wild-nic.1–4 |
| experiments/update_eval.py | wild-aoq.1–4 |
| experiments/update_fixtures/ | wild-aoq.2–4 |

Evidence: these paths occur verbatim in metadata.files. Some overlaps are serialized already, but wild-mh5.2 and wild-nic.1 can both start after wild-mh5.1 and share the CLI and protocol files. There are no co-modification notes. Directory entries are scope declarations, not claims that all files inside already exist.

Recommendation: add coordination notes to the affected tickets, especially the two parallel branches; re-read the shared protocol and re-anchor after the other branch lands. Do not force an architectural decomposition or serialize the whole project merely because a small initial CLI shares files. This is one grouped coordination finding across eight paths.

## Pass 1: Completeness and clarity

No new finding. Titles name outcomes; each child has concrete proposed paths, source references, acceptance conditions, headers, TDD/Tidy First instructions and anti-goals. Parent containers are clearly distinguished from child work. There are no orphaned proposal scenario names in the metadata mapping.

## Pass 2: Scope and slice boundaries

### SCOPE-001 — MEDIUM: The final review tickets also implement integration

Affected: wild-mh5.5, wild-nic.5, wild-aoq.4.

Evidence: all three have lane REVIEW. wild-mh5.5 instructs the assignee to "Register real executable correspondence, reconcile scoped dual-format rules, and archive the change". wild-nic.5 similarly owns registration and reconciliation. wild-aoq.4 requires the new deployed dual-format capability and a change to tests/test_gate_wiring.py's nine-capability assumption. Those are deliverables to create, not only existing output to inspect, and the preceding implementation tickets do not explicitly own those registration/integration steps.

Impact: a worker routed as a second-opinion reviewer either leaves required integration undone or becomes the author of the integration it is meant to review. This is a role mismatch, not an objection to the need for conformance verification.

Recommendation: put scenario registration into the corresponding implementation slices, with final integration/archive ownership explicit, and retain the final REVIEW tickets as independent verification. Alternatively, rename and reclassify these tickets as integration delivery work and separately identify the review handoff. Avoid creating schema-only or docs-only tickets when the changes can accompany their behavior.

## Pass 3: Dependencies and ordering

### DEP-001 — MEDIUM: The first extractor waits on the entire evaluation fixture cohort

Affected: wild-mh5.1, wild-aoq.2, wild-aoq.1; transitively the initial update path.

Evidence: the actual graph is wild-mh5.1 → wild-aoq.2 → wild-aoq.1. The fixture ticket requires all four range/compatibility cells plus transitive, singleton, runtime/platform, dynamic, wrong-target, baseline-failure, migration and intentional-change cases, real Cargo replay, and both development and sealed evaluation sets. The prerequisite reporting ticket includes confirmatory-study preregistration validation as well as metric aggregation. Thus all of that must finish before the first extractor ticket can start under the recorded blockers.

Impact: independently specified initial fixtures are necessary, but the graph makes the completed broad fixture runner and reporting path prerequisites for any extraction. This increases time to the first working consumer update. It is an over-broad dependency, not a declared cycle or proof that the underlying fixture work is unnecessary.

Recommendation: separate the minimal independently specified E1/E4 fixture outcomes needed by the first supported profile from expansion of the complete E5 cohort. Keep the full frozen corpus as a prerequisite for comparative evaluation. Repoint wild-mh5.1 to the narrow fixture predecessor only after its acceptance and ownership are concrete; do not simply remove fixture discipline. Preserve sealed-set commitments before any held-out evaluation or tuning on that set. No guessed new issue id or immediately executable dependency-removal command is supplied.

## Pass 4: Plan and scenario alignment

### ALIGN-001 — MEDIUM: A pre-miner fixture ticket owns a treatment-integration scenario

Affected: wild-aoq.2 and wild-aoq.3; relates to wild-mh5.2.

Evidence: metadata assigns "Unsupported dynamic usage is retained" to wild-aoq.2, whose body explicitly says "No Wild checker is required to establish the fixture outcomes." The evaluation spec scenario says "WHEN the treatment returns unknown but an independent oracle can adjudicate behavior" and requires retaining both outcomes without relabelling abstention. The actual A-D adapters and execution arrive in wild-aoq.3; scoped demand checking arrives in wild-mh5.2, after the fixture ticket.

Impact: preparing an independently adjudicated dynamic fixture is not the same verification as retaining a real treatment's unknown result through the evaluation pipeline. A synthetic unknown record can test record handling, but cannot alone demonstrate that integration. The current coverage map does not distinguish these levels. This is not reported as a proven dependency cycle: the ticket can legitimately prepare expected fixture data before the treatment exists.

Recommendation: leave fixture/oracle preparation in wild-aoq.2 and move ownership of the actual treatment-result retention scenario to wild-aoq.3. Alternatively, explicitly name both the earlier record-level test and the later integration acceptance, with the latter required before the parent closes. Preserve the policy/oracle/checker distinction.

## Pass 5: Executability and handoff

No additional defect beyond the findings above. Eleven child meters name future pytest files; none exists at the reviewed commit. Running `pytest -q tests/test_update_eval_records.py` returns exit 4, "file or directory not found", with no tests run. That is not an executed behavioral red test. However, the tickets explicitly disclose this state, set meter_available_at_creation=false, require tests before implementation, and use DESIGN rather than AFK. The absence is therefore recorded as an execution-readiness limitation, not misrepresented as a stale or passing gate.

Before an implementation slice can claim a behavioral baseline, its first TDD step must create and run a meaningful failing test against the agreed behavior. No AFK readiness is inferred from an existing repository CI command. The three review meters are existing overlay commands, with the previously recorded 13/12/11 missing-runtime-contract baselines. Their future successful execution remains required; this review did not implement or run the absent runtime suites.

Lane/complexity metadata is present on every child and no DESIGN task is labelled AFK. File-header criteria and anti-goals are present. L grades are reasonable for new protocol/runtime behavior; there are no executable XL children. Existing proposal approval requirements remain unchanged, and no new approval gate is introduced by this review.

## Convergence

False-positive estimate: 10% reviewer judgment throughout, not an independently measured rate. Findings are grounded in recorded tracker text, paths and dependency edges. Pre-flight produced one grouped LOW finding; it is excluded from the content-pass new-finding comparison.

| After pass | New CRITICAL | New findings | Previous-pass findings | New / previous | Status |
| --- | ---: | ---: | ---: | --- | --- |
| 2 | 0 | 1 | 0 | Undefined; new finding requires continuation | ITERATE |
| 3 | 0 | 1 | 1 | 100% | ITERATE |
| 4 | 0 | 1 | 1 | 100% | ITERATE |
| 5 | 0 | 0 | 1 | 0% | CONVERGED |

Converged at pass 5 means the review stopped finding new defects. It does not mean the outstanding ticket edits have been applied.

## Final assessment

- Total reviewed: 17 tickets (14 children, 3 parent epics).
- Findings: 0 CRITICAL, 0 HIGH, 3 MEDIUM, 1 LOW.
- Slice quality: Good. Horizontal-ticket leakage: Low, concentrated in integration work left to final reviews.
- Lane clarity: Fair at the three review handoffs; otherwise explicit and conservative.
- Clarity: Good. Scope: Good with the review-handoff exception. Dependencies: Fair. Completeness: Good at scenario-name level, with one integration ownership correction needed.
- Top priorities: narrow the initial fixture prerequisite (DEP-001), clarify integration versus review ownership (SCOPE-001), and assign actual treatment-result retention to the execution ticket (ALIGN-001).
- Verdict: NEEDS_UPDATES. Apply the targeted tracker corrections in wild-bi3, recheck coverage and dependencies, and retain the existing proposal approval boundary before runtime work.

The original tickets were reviewed rather than rewritten. This artifact records recommendations; Beads owns follow-up status.
