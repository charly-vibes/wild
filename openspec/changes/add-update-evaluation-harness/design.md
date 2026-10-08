# Update evaluation design

## Delivery order and causal comparison

Prepare records, trusted fixture inputs, and independently specified expected outcomes before developing the miner against them. Use a development fixture set for E1/E4 and a separate frozen evaluation set for E5. Connect a single actual update as soon as local checking and Cargo execution exist. Expand language coverage based on observed gaps, then preregister E3; do not build the native platform first.

| Arm | Additional feedback beyond the common existing-tool baseline |
| --- | --- |
| A | None; existing update automation, CI, compatibility tools, logs/caches, and ordinary agent-written tests remain available |
| B | Deterministically mined contracts and structural diagnostics |
| C | Authored obligations and their checked feedback, including explicitly declared structure if supplied; no miner output |
| D | Both mined and authored-obligation feedback |

All arms use the same trusted invocation for accepted tests/obligations, policies, configuration, scope, target priorities, catalog, and permitted edits. All can propose authorized out-of-range updates and supplied/generated migrations under equal budgets. Common protection preserves each arm's actual accepted obligations; it does not give A obligations produced by D or require a Wild wire format to pass A's checks. Common non-compatibility constraints and external grading apply to everyone. Record each arm's acceptance rule before runs, including how its native tool results map to accept/reject/unknown/error. Use a common host execution path so isolation or range-edit authority is not a treatment. Reuse native logs/build caches in the baseline; charge retrieval/regeneration cost across all arms.

An arm that lacks feedback due to a disabled treatment cannot receive that feedback indirectly via shared output directories or prior run logs. Independent grading inputs are inaccessible to generating agents. Rotate clean workspaces and hide other arms' artifacts; immutable fixture inputs and tool binaries can be shared. Share cache inputs only under the preregistered cold/warm policy.

## Commands and records

Proposed orchestration commands:

```text
python3 experiments/update_eval.py validate --protocol study.json
python3 experiments/update_eval.py run --protocol study.json --output results/
python3 experiments/update_eval.py summarize --runs results/ --output summary.json
```

Use a separate versioned evaluation schema; do not change the v1 runtime format. Validation and summary are deterministic functions of committed records. Experimental execution may contain nondeterministic agents or systems: preserve raw outputs and distinguish reproducible configuration from identical generated code.

| Record | Required content |
| --- | --- |
| Protocol | Version/id; development/evaluation split; task and stratum membership; frozen catalog and desired targets; environment/tool/model identities and settings; arm adapters and outcome mapping; authority; budgets/timeouts; execution order randomization; cold/warm policy; preregistered hypotheses, risk/completion margins, stopping and adjudication rules |
| Task | Unique id; real/synthetic origin and historical cutoff; consumer/base digests; exact target; original allowed/excluded range; direct/migration/intent class; preregistered feasible-target flag with basis; non-compatibility constraints; hidden oracle commitment; policy-prohibition, dynamic, transitive, singleton, runtime, and platform tags |
| Attempt | Task/arm/trial/attempt ids; all input commitments; actual edits and authority; requested/selected artifacts and full closure; checker result and reason category; execution stage/status; build/check evidence; human active time and compute cost including setup/repair; elapsed time; exit/timeout/abandonment; output artifact digests |
| Oracle result | Actual attempt artifact commitment; compatible/incompatible/unresolved for a named domain; eligibility result and reasons; grader/harness/input identities; adjudication history and disagreements; hidden-test access record |
| Task result | References to every attempt; terminal disposition; at most one delivered result; independent validity; direct/migration/intent class; total costs and elapsed time; no delivery on unresolved oracle |

Do not fabricate unavailable cost fields as zero. Each cost field is measured, explicitly unavailable, or intentionally inapplicable; incomplete cost coverage prevents a cost-superiority conclusion. Wall time and human active minutes are distinct. Use recorded per-model pricing inputs or normalized resource counts rather than silently importing current prices during summary. Keep agent secrets out of reports.

## Fixtures and independent grading

The E5 minimum matrix has all four original-range allowed/excluded × independently compatible/incompatible cells. Prove original exclusion with actual Cargo resolution using the unchanged manifest and attempted exact target, not a handwritten semver predicate. Then exercise the committed manifest change and verify Cargo's selected target/source and fixed-lock build. Supply multiple genuine releases through a frozen local registry; do not use path replacement to bypass range enforcement.

Include: a major release removing an unused API; a patch removing a used API; a compatible ordinary update; an incompatible excluded release; an added transitive requirement; a declared singleton conflict; runtime/platform ineligibility; unsupported returned-object/macro/plugin-like use; wrong-target selection; baseline failure; a migration; and an authorized intent change. Positive/negative law cases must include unchanged signatures with changed behavior. Some hard cases should abstain rather than pass; report that outcome honestly. Synthetic fixture contracts may be provided under the corresponding authored treatment but never exposed selectively outside its declared rules.

E1 repeats extraction across clean directories and checks canonical facts, provenance changes, unsupported inventory, toolchain/features/generated-input perturbation, and artifact evidence invalidation. No incremental/full equivalence claim until an incremental implementation exists. E4 attempts to delete tests/laws, alter scope/policy/checker, omit consumers, falsify digests, and regenerate weaker contracts under the common trusted runner in every arm, with an authorized transition as positive control. A detected bypass fails the fixture suite; zero known bypasses is not a proof of general security.

The oracle is specified before candidate contracts and uses held-out consumer tests and independently reviewed behavior/constraints with real builds. A failing tool process alone does not label incompatibility: a grader distinguishes candidate failure from infrastructure failure and may return unresolved. A passing smoke test is scoped evidence, not complete truth. Preserve grader disagreements and unresolved labels. Oracle commits bind the actually evaluated artifact, including migration code, not merely the requested release. Do not discard hard cases after seeing arm results.

## Outcomes and exact denominators

Candidate checker outcome is accept, reject, unknown, or error, with reason categories. Unknown is missing/inconclusive evidence; error is unsuccessful evaluation execution; neither is a false negative. Structural/counterexample rejection, non-compatibility policy refusal, and host-resolution refusal remain distinguishable. Map v1 refuse to reject or unknown using evidence/reason, not just the exit code. Native arms use their preregistered adapter mapping.

The binary compatibility table includes only policy-eligible candidates with an adjudicated compatible/incompatible oracle. For that subset:

| Metric | Numerator / denominator |
| --- | --- |
| Unsafe acceptance | Accepted incompatible / all accepted adjudicated candidates |
| Breakage detection recall | Compatibility-rejected incompatible / all incompatible candidates |
| False-negative rate | Accepted incompatible / all incompatible candidates |
| False-block rate | Compatibility-rejected compatible / all compatible candidates |

Unknown/error cases remain in the compatible/incompatible denominators where adjudicated. Report their counts separately. For all assigned fixed candidate evaluations, report unknown rate, error rate, oracle adjudication coverage, and every policy exclusion/violation. Accepted but oracle-unresolved cases remain visible and never count as validated successes. A policy error is not disguised as a compatibility false block. Give counts before exclusions and per-reason exclusions; multi-reason tags need not sum to unique cases.

Task completion is independently valid pinned updates delivered / all assigned update tasks, counting each task once per arm/trial. Also report completion on the preregistered feasible-target subset, and direct/migration/intent-change strata. Correct refusal on an impossible task is correct disposition but not completion. Multiple attempts are not independent completed tasks. Candidate-attempt metrics are descriptive; use the fixed-candidate cohort for primary detection comparisons to avoid selection bias from arm-specific search.

Human minutes or total cost per valid update is the sum over all assigned tasks, including failures/abandonment/setup/repair, divided by independently valid updates. Report cold and warm costs separately and amortization assumptions. Zero denominators yield null with a reason, never zero. Report successful-task latency alongside timeout/abandonment and all-task effort; do not hide failed effort behind a success-only median. Changed target priorities require a new protocol version.

### Aggregation acceptance example

A fixed-candidate eligible cohort has six candidates: two compatible accepted, one incompatible accepted, one incompatible rejected for compatibility, one compatible unknown, and one incompatible error. The summary must give unsafe acceptance 1/3, recall 1/3, false-negative rate 1/3, false-block rate 0/3, unknown 1/6, error 1/6, and oracle coverage 6/6. Add an unresolved accepted case and a policy-prohibited case: they change all-assigned counts and their own reported categories, but not those binary rates. A separate task fixture with three attempts delivering one task must count one completion and charge all three attempts.

## Study gates and claims

For E3, register the repository/release-family split, stratum counts, feasible targets, budgets, tool/model snapshots, risk/completion margins, severity weights, timeouts, and stopping rules before execution. Use the design's 50 tasks across 10 repositories × four arms × three trials as a directional pilot, not proof of rare-failure safety. Cluster uncertainty by repository/task and report real versus synthetic results separately. A 20% effort reduction is a provisional target, not a software test assertion; an inconclusive interval is not success. Missing preregistration permits labelled fixture/debug runs but refuses confirmatory-study mode.

E2 semantic-authoring usefulness, E6 cross-session reuse, and E7 adoption use this accounting where applicable but remain later studies. Do not require five participating teams or a full E3 corpus merely to ship the first reproducible fixture runner. Retain the existing-tool baseline if Wild does not improve completed-update effort or yield at the agreed risk margins.

## Integration and rollback

Keep a new evaluation capability separate from product semantics. At implementation, give wild-evaluate a full dual-format Purpose/Constraints/Model/Properties/Design acceptance cases layout and executable Requirements, preserving repository corpus tests. Register spectacular contracts only when the harness and meaningful tests exist. No study record can change its committed inputs in place; corrected records append a revision and invalidate affected summaries. Removing the experimental runner does not affect existing product/prototype behavior.
