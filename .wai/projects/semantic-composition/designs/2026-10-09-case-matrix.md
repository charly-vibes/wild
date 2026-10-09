# Evaluation cases

Expected outcomes are experiment requirements, not claims that the current runtime implements them. Observed results are independently labelled. H0/H1/H2 refer to the [approach matrix](matrix/problem.md); run the same applicable cases against each. S0/S1/S2/S3 refer to assurance mechanisms, not an ordinal proof ladder.

| Case | Input / mutation | Required observation and expected outcome | Current evidence | Mechanism |
| --- | --- | --- | --- | --- |
| C01 same-shape race | Replace atomic reservation commit with stale-read commit | Both terminal successes on one reservation must be a behavioral counterexample; shape may still pass | Executed toy: identical shape accepted; 4/6 stale schedules violate, 0/6 atomic | S1, H0/H1/H2 |
| C02 valid internal replacement | Two independently written atomic implementations with the same public boundary | Preserve allowed traces and completion for the frozen finite domain; accept only within bounds | Not executed; baseline atomic model is not a second implementation | S1, H0/H1/H2 |
| C03 used versus unused output removal | Remove one demanded output, then one explicitly unused output | Reject demanded removal; scoped compatibility for unused removal only with complete demand and full replacement dependency checks | Related toy substitution results only; exact paired case not executed here | S0, H0/H1/H2 |
| C04 new hidden dependency | Internal replacement adds an unbound required input while public shape stays fixed | Refuse closure; wrapper must not hide the missing binding | Specified E01/E02; not executed as v1 | S0, H0/H1/H2 |
| C05 shared singleton | Two wrappers reference one real singleton; control uses two distinct instances | Preserve explicit shared identity; reject distinct conflicting instances after flattening | Not executed; human review of initial-pilot scope requested | S0 + identity, H0/H1/H2 |
| C06 cross-boundary relation | Exposed timeout guarantees appear compatible but an internal less_equal relation fails | Refuse relation; hiding must not eliminate its endpoints | Specified E02; not executed as v1 | S0, H0/H1/H2 |
| C07 same contract, new bytes | Change an internal implementation without changing wrapper contract | Old behavioral evidence must not authorize the new assembly; reevaluate affected claims | E04 requires artifact-bound evidence; wrapper linkage undecided | S1, H0/H1/H2 |
| C08 dishonest projection | Adapter drops expiration successes or maps failures into success | Independent event-completeness fixture rejects adapter; no empty-trace pass | Not executed | S1/S2, H0/H1/H2 |
| C09 nested versus flat | Flatten a two-layer graph with injective renaming; compare demand, sharing and relations | Equivalent public observations and equivalent semantic closure; incidental ids cannot change results | Composition specified E02; nested mapping not implemented | S0/S1, H1/H2 vs H0 |
| C10 incomplete bundle | Delete a root subtree, implementation blob or oracle fixture | Commitment mismatch is an error; missing required evidence is unknown/refusal, never pass | Toy dropped binding/corrupt hash rejected; full bundle cases not executed | S0/S1, H0/H1/H2 |
| C11 stale authority | Keep structure fixed; expire/revoke evidence authority or change policy | Reevaluate policy; preserve independent structure/law results; old acceptance not reusable | Specified E04; not executed | Policy, H0/H1/H2 |
| C12 cross-language conformance | Rust and Python implement the same finite input/event profile | Compare both to independent oracle, not only to each other; detect a deliberately mutated implementation | Not executed; outside current Cargo-only first product slice | S2, H0/H1/H2 |
| C13 unsupported obligation | Supply free prose, unsupported temporal predicate or unmapped state/event | Explicit unsupported/unknown or input error at defined boundary; no certified behavioral claim | E09/E10 source inspection; no adapter exists | S2/S3, H0/H1/H2 |
| C14 trace hiding / divergence | Candidate emits no forbidden event because it deadlocks or loops internally | Separate progress obligation fails within defined bound; timeout outside that protocol is inconclusive | Not executed; safety-only six schedules do not answer this | S1/S2/S3, H0/H1/H2 |
| C15 circular assumptions | A guarantees p assuming q; B guarantees q assuming p | No parent guarantee without a discharged environment premise or valid supported fixed-point proof | Not executed; no S3 checker specified | S3, H0/H1/H2 |
| C16 evidence-domain mismatch | Proof uses fewer schedules, different oracle, or candidate edits accepted obligations | Refuse scope/commitment mismatch; sampled evidence cannot be relabelled exhaustive | E04/E07 design; not executed as composite protocol | S1/S2/S3, H0/H1/H2 |

## Result record

Each run records case id, H/S factors, source and implementation identities, exact assembly and boundary mapping, accepted oracle/profile, observation adapter, fixtures, scheduler/domain bounds, method, structural assurance, law status, policy decision, diagnostic, public trace, counterexample where present, execution cost and evidence bytes. These fields describe research records, not extensions to v1 documents.

Separate schema/input errors, known incompatibility, insufficient evidence, and harness failure. Preserve all outcomes in denominators. A case with no runnable implementation is NOT EXECUTED; it must never be reported as a passing unknown-handling test. Freeze the case corpus and oracle before comparative runs; changes invalidate affected comparisons.

## Decision rules

An unsafe accept in any applicable frozen negative case blocks promotion. Report exact numerator/denominator for false refusals and unknowns among positive cases; zero unsafe accepts alone is insufficient because an always-refuse tool achieves that. C02 and the valid controls for C03/C05/C09/C12 must demonstrate useful acceptance. Publish per-case results rather than pooling toy, schema and runtime checks.

Compare authoring effort and recomputation with the same oracle, machine, inputs and budgets. Use separate records for initial construction and subsequent internal replacements. Decide any practical benefit threshold after a pilot measures the available range and before a confirmatory comparison. Generalization beyond the finite cases requires separate evidence.
