---
tags: [pipeline-run:tdd-ro5-2026-11-27-widen-method-receiver-demands-wild-8j4, pipeline-step:orient]
---

ORIENT: widen-method-receiver-demands (wild-8j4). OpenSpec change exists (0/13 tasks, proposal+design+spec+tasks approved). Declared-trust widening Option B: bundle-wide pre-pass (return types + public struct field types across all bundle files), let-bound ctor/field flow, inventoried field access, self/Self in public inherent impls, chain hop folding. No inference; every unresolved shape keeps the named incomplete-demand gap. Tests in tests/runtime/test_extract.py. One pure refactor edit already applied (recorded_return_ty -> recorded_path_ty).
