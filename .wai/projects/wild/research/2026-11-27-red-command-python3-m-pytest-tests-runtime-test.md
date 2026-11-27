---
tags: [pipeline-run:tdd-ro5-2026-11-27-widen-method-receiver-demands-wild-8j4, pipeline-step:red]
---

RED: command=python3 -m pytest tests/runtime/test_extract.py -k 'widen_let or widen_reassigned or widen_field or widen_self or widen_chain_with or widen_cross_file' -x -q; expected failure confirmed: test_widen_let_bound_constructor_local_resolves fails rc=1 with receiver gap 'method call .tick on receiver r is outside the supported demand profile' — exactly the missing widening behavior (8 of 9 new tests currently refuse; test_widen_unbounded stays green). Tests-only edit; the earlier recorded_path_ty refactor is behavior-neutral.
