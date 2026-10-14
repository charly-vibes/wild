---
tags: [pipeline-run:tdd-ro5-2026-10-13-wild-m7f-std-macro-demand-support, pipeline-step:red]
---

RED evidence (wild-m7f.3): command=pytest tests/runtime/test_extract.py -q. Result: 5 failed / 12 passed. Reds match the amended design's missing behavior, NOT setup breakage: (b) statement assert_eq! args not descended (exit 0, complete_inventory true, demand entries missing — silent acceptance), (c) expression format! still emits incomplete-demand (exit 1), (d) nested foo!() inside statement println! silently skipped (exit 0), (e) statement vec![1,2]; silently skipped (exit 0), (g) unparseable println!(a; b); silently skipped (exit 0). Green guards: (a) statement println! accepted exit 0 (passes pre-change too — silent), (f) expression vec! refused exit 1 (incumbent ExprMacro visit). All 10 pre-existing tests green — determinism/invariance gates intact.
