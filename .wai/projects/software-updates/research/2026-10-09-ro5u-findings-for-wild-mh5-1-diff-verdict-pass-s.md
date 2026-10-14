---
tags: [pipeline-run:tdd-ro5-2026-10-09-wild-mh5-1-extract-rust-contracts-local-1-schema-canonical-reader-extract-path, pipeline-step:fix-review]
---

RO5U findings for wild-mh5.1 diff, verdict pass. Stage 1 DRAFT: shape sound. Stage 2 CORRECTNESS: H1 leading zeros accepted in parse_number (v1 violation); H2 envelope checker null violated v1 envelope digest requirement; H3 dep-qualified demand to unsupplied provider silently dropped. Stage 3 CLARITY: converged. Stage 4 EDGE CASES: M1 cfg attrs only on fns; M2 pub static/type not opaque-inventoried; M3 missing package version defaulted to 0.0.0; L1 opaque slots lacked locations; L2 parse_object O(n^2) dup detection — tracked. Final: no criticals, converged; highs+mediums fixed with behavior-impacting tests (leading-zero unit refusal; unsupplied-provider incomplete-demand runtime), L2 tracked.
