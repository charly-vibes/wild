# Comparative protocol — revision 2

This research protocol resolves the [matrix review](../reviews/2026-10-09-matrix-rule-of-5.md). It defines a comparison, not an implemented runtime or new normative wire format. Architecture selection remains open.

## Fixed treatments

The experimental unit is a named consumer boundary undergoing a frozen ordered replacement workload. Every arm receives the same underlying graph, artifacts, public obligations, explicit sharing, bindings, oracle, observation adapters, fixtures and budgets. Commit these inputs before execution. An independently specified canonical flat closure is the reference; no arm generates its own grading oracle.

| Arm | Authored artifacts and consumer operation | Permitted reuse | Evaluator input |
| --- | --- | --- | --- |
| H0 | Full flat assembly and experiment-only root mapping per consumer | Copy/templates and ordinary editing/scripts; no reusable component-boundary reference in the submitted format | Explicit flat closure and root mapping |
| H1 | Public contract and versioned external mapping authored once; consumers reference them with instance parameters | Reusable authored boundary; external expander materializes closure, while the assembly checker has no nested kind | Flat closure, public contract and mapping provenance |
| H2 | Public boundary and child assembly in an experimental schema-native composite; consumers instantiate it as a component | Native nested references and expansion under the declared schema | Nested document plus independently checked expansion to the same flat closure |

Equivalent editing/agent assistance, ordinary scripts and caches with complete input keys are permitted in every arm. Record tool/model versions, automation artifacts, permitted actions and setup costs. H0 may automate repeated record production; submitting H1/H2 references changes its treatment. H1 may use helpers, but a schema-native nested component changes the treatment to H2. Do not cripple baseline automation to manufacture a benefit.

Hold decomposition and language fixed within each representation block. Another decomposition gets a separate matched block; aggregate only with declared block weights. P2 changes language implementations deliberately, under a fixed public profile and independently checked adapters. Counterbalance or randomize arm order with a recorded seed. Separate authoring sessions from repeated machine timings so learning and warm-up are visible.

H2 entry requires a versioned experimental grammar, deterministic expander, explicit identity/sharing rules and a runnable adapter to the common oracle. Entry is not readiness and does not depend on H1 winning. An unavailable arm is NOT EXECUTED, not a measured loser.

## Phase and case applicability

R = required; D = deferred to the named later phase and excluded from the current verdict and denominators. All H arms evaluated in a phase receive the same R cases. Labels cannot change after results. Definitions are in the [case catalog](2026-10-09-case-matrix.md).

| Case | P1: S1 + structural closure | P2: add S2 portability | P3: add S3 refinement |
| --- | --- | --- | --- |
| C01 | R | R | R |
| C02 | R | R | R |
| C03 | R | R | R |
| C04 | R | R | R |
| C05 | R | R | R |
| C06 | R | R | R |
| C07 | R | R | R |
| C08 | R | R | R |
| C09a | R | R | R |
| C09b | R | R | R |
| C09c | R | R | R |
| C09d | R | R | R |
| C09e | R | R | R |
| C10 | R | R | R |
| C11 | R | R | R |
| C12 | D: P2 | R | R |
| C13 | R | R | R |
| C14 | R | R | R |
| C15 | D: P3 | D: P3 | R |
| C16 | R | R | R |

P1 includes finite empty assemblies, shared instances and cyclic dependencies structurally. Cyclic closure does not prove runtime progress. C05/C07 are required initially: identity and evidence validity are prerequisites for the pilot's claims. Candidate limitations cannot waive supported positive cases.

C13 has phase-specific unsupported controls: P1 refuses unsupported S2/S3 evaluation requests without a behavioral pass; P2 additionally diagnoses unsupported event/state predicates; P3 additionally refuses unsupported proof/assumption forms. A well-formed unsupported request yields unknown/inconclusive; malformed input yields error. Freeze the precise fixture/diagnostic for each variant. Refusing an S2 request in P1 is not S2 conformance.

P1 makes only recorded S0/S1 claims; P2 adds conformance to its finite cross-language profile, not unrestricted equivalence; P3 adds only the discharged refinement theorem under named assumptions. C15 includes a positive discharged-premise control in P3. Repeated earlier cases detect regressions but do not become additional independent evidence.

## Corpus freeze and deterministic verdict

Before measurement, commit a run manifest naming protocol revision, phase, arms, sources/tools, workload order, input commitments, every R case/variant, positive/negative role, exact expected structural/law/policy/execution fields, finite bounds and cost conditions. Multi-outcome rows become separate variants, such as C03.used and C03.unused. Unbound fixtures or unresolved expectations are NOT EXECUTED and prevent readiness. This protocol is ready for fixture construction; it does not claim that a complete frozen run manifest already exists.

The evaluator reads that manifest, not a candidate-selected case list. Each required variant must match its expected fields. An expected unknown/refusal counts as a successful diagnostic control only when invoked and returning exactly that outcome. Missing implementation is never such a pass. Unknown/error/refusal cannot satisfy a supported positive's expected acceptance. Wrong classifications fail even when they refuse; unsafe acceptance is additionally labelled.

| Aggregate | Definition |
| --- | --- |
| FAILED | At least one executed R variant mismatches expectations; disclose missing results too |
| INCOMPLETE | No observed mismatch, but required variant/input/arm results are missing or NOT EXECUTED |
| PHASE_READY | Every R variant was executed and matched expectations |
| DEFERRED | Case is D; no result claimed, excluded from the phase verdict |

NOT APPLICABLE requires a separately versioned study with a pre-execution exclusion rationale. It cannot override R here. Preserve NOT EXECUTED, UNKNOWN and ERROR distinctly. Compare efficiency only among PHASE_READY arms under the same manifest, while retaining costs/results of failed and incomplete arms in the report.

Report acceptance among supported positives, false refusals, unexpected unknowns, expected diagnostic refusals, unsafe accepts, errors and missing runs, each with numerator/denominator and exact variant ids. Timing repetitions are not independent compatibility observations. Always-refuse candidates cannot qualify because positive controls must accept.

## Cost ledger and reuse workload

Freeze B distinct consumers and U ordered updates per consumer, including their identities, before a block. Each arm authors a first boundary, reuses it for additional consumers, then processes the same replacements. Report first-use and repeated-use costs. A pilot can estimate useful workload sizes; a confirmatory manifest fixes B, U and benefit thresholds before comparative outcomes.

| Bucket | Include | Attribution |
| --- | --- | --- |
| Shared setup | Common oracle, canonical-closure fixtures and common infrastructure | Report once outside arm deltas, not charged only to baseline |
| Arm setup | Representation/expander implementation, schema, installation/configuration, arm-specific adapters | Per arm, including failed attempts; pre-existing sunk effort separately with provenance or UNKNOWN |
| Boundary authoring | Contracts, mappings, instance parameters, consumer configuration | Per boundary, including reused-template edits |
| Updates | Edits and changed declarations/mappings for each replacement | Per update; failed attempts retained |
| Review/repair | Report interpretation, debugging and authoring corrections | Attribute to triggering boundary/update; avoid double counting |
| Execution | CPU/elapsed time, peak memory, checks rerun, evidence bytes, known compute charges | Keep units distinct from human minutes |
| Exit/migration | Export final artifacts to common flat interchange and verify equivalence | Every arm; generic exporter construction belongs in setup |

Human minutes are active work, logged or explicitly estimated; waiting is separate. Agent tokens/compute and tool runtime have separate columns. Unknown pre-existing effort is not zero: report marginal measured cost and mark total-cost ranking unavailable.

Report raw totals first. For B > 0, U > 0 and each additive unit separately, amortized arm cost per consumer-update is `(arm setup + authoring + updates + review/repair + execution + exit) / (B * U)`. Do not mix units or amortize peak memory. Also show setup per boundary and unamortized totals. Shared setup remains separate. C09b's empty graph is a correctness fixture, not a zero-denominator performance workload.

Cold runs start with identical fresh caches and charge population. Reused runs start from the same logical warm-up workload per arm, then execute the same mutation sequence. Record keys/provenance, invalidations and misses; pass C07 before claiming reuse. Separate cold/reused tables. No asymmetric prewarming or cached final policy acceptance. Freeze machine/toolchain, parallelism, repetitions, budgets and execution order.

## Selection

Readiness establishes bounded correctness, not superiority. Before confirmation, declare the primary benefit metric, practical margin, acceptable regressions in other buckets and repeated-measurement comparison method. Without these, report exploratory data only. Unknown necessary costs or unresolved tradeoffs yield INCONCLUSIVE selection and retain the current architecture. Provisional colors never select a winner.
