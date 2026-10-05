---
id: spec
kind: intent
statement: THE wild extraction layer SHALL turn schemas, source code, and data artifacts of any ecosystem into Contract IR through pluggable, deterministic extractors that never drop a construct silently.
---

# Wild extract

The language-blind core sees only IR. Everything ecosystem-specific lives in extractors (schemas, source APIs, feature files, templates) and in law harnesses that run recorded properties against an implementation. Anything an extractor cannot express becomes an opaque, frozen slot and is reported.

## Constraints

| id | kind | expr | traces_to |
| -- | ---- | ---- | --------- |
| extractor_contract | extension_point | `for every conforming extractor E: extract(source) yields ContractIR, is deterministic, and reports coverage listing every unextracted construct` | [[spec]] |
| law_harness | extension_point | `for every conforming harness H: run(suite, implementation, seed) yields a LawResult and is deterministic given the seed` | [[spec]] |
| extraction_total | invariant | `every source construct maps to a slot or to an opaque slot; none is dropped silently` | [[spec]] |
| extractor_deterministic | invariant | `the same source and extractor version yield the same IR bytes` | [[spec]] |
| extractor_isolated | invariant | `extractors read only the source they are given and perform no network or write access` | [[spec]] |
| ir_versioned | invariant | `emitted IR names its schema version; the core refuses IR of an unknown version` | [[spec]] |
| data_plane_extractors | invariant | `schemas, templates, and feature files have extractors under the same contract as code extractors` | [[spec]] |
| ecosystems_pluggable | invariant | `supporting a new ecosystem requires an extractor only, with no change to the core` | [[spec]] |
| extractor_coverage_reported | advisory | `each extraction reports the share of constructs mapped to opaque slots` | [[spec]] |
| failure_reported | effect | `an unreadable source emits a failure report naming the source and the cause` | [[spec]] |
| extractor_noise_reported | advisory | `each extractor reports its false-break rate against project history` | [[spec]] |

## Model

### States

- `source_read`
- `parsed`
- `mapped`
- `reported`
- `failed` (emits: [[spec.failure_reported]])

### Transitions

| id | from | to | guard |
| -- | ---- | -- | ----- |
| parse | source_read | parsed | [[spec.extractor_isolated]] |
| map | parsed | mapped | [[spec.extraction_total]] |
| report | mapped | reported | [[spec.extractor_deterministic]] ∧ [[spec.ir_versioned]] |
| fail_read | source_read | failed | [[spec.extractor_isolated]] |

## Properties

| id | kind | derives_from | generator | predicate | observes |
| -- | ---- | ------------ | --------- | --------- | -------- |
| extractor_reports_coverage | unit | [[spec.extractor_contract]] | `extractor_output_with_unmapped_construct()` | `coverage lists the construct` |  |
| harness_deterministic_given_seed | unit | [[spec.law_harness]] | `harness_run_twice_with_same_seed()` | `result(a) == result(b)` |  |
| no_silent_drop | unit | [[spec.extraction_total]] | `source_with_unsupported_construct()` | `slot_for(construct) is opaque` |  |
| same_source_same_bytes | unit | [[spec.extractor_deterministic]] | `source_extracted_twice()` | `bytes(a) == bytes(b)` |  |
| extractor_has_no_side_effects | unit | [[spec.extractor_isolated]] | `extractor_run_with_network_and_writes_blocked()` | `extract completes ∧ no write attempted` |  |
| unknown_ir_version_refused | unit | [[spec.ir_versioned]] | `ir_with_version("99")` | `core == refused` |  |
| feature_file_extracts_like_code | unit | [[spec.data_plane_extractors]] | `feature_file_with_known_arity()` | `ir.arity == known_arity` |  |
| new_ecosystem_needs_no_core_change | unit | [[spec.ecosystems_pluggable]] | `extractor_for_new_ecosystem_added()` | `core_diff == empty` |  |
| opaque_share_reported | unit | [[spec.extractor_coverage_reported]] | `source_with_known_opaque_count(3 of 10)` | `report.opaque_share == 0.3` |  |
| unreadable_source_reported | unit | [[spec.failure_reported]] | `source_path_that_does_not_exist()` | `report names the source ∧ the cause` | [[spec.failure_reported]] |
| noise_rate_reported | unit | [[spec.extractor_noise_reported]] | `extraction_run_over_known_history()` | `report has false_break_rate` |  |

## Notes

The IR is a common denominator, so extraction is lossy by nature; opaque slots are frozen, which can raise false breaks. That is why noise is measured and reported rather than hidden. Facet-specific extraction (ABI, layout, serialization) arrives as additional extractors under the same contract.

Candidate follow-ups, each as its own file: `wild-ir.md` (the Contract IR schema and canonical form), `wild-manifest.md` (consumer manifest and lockfile formats), and one `extractor-<ecosystem>.md` per ecosystem that satisfies `extractor_contract`.
