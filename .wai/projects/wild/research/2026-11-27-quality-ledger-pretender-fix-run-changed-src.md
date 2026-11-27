---
tags: [pipeline-run:tdd-ro5-2026-11-27-fix-pretender-gate-violations-extract-rs-visitor-split-delivery-params-check-rs-length-harness-extract-field-counts-test-thresholds, pipeline-step:quality-ledger]
---

QUALITY LEDGER (pretender-fix run): Changed - src/check.rs, src/extract.rs (+ extract/demand_resolution.rs), src/delivery.rs, src/harness.rs, src/obligations.rs, src/cargo_host.rs, tests/v1_checker.rs, tests/runtime/test_on_absent.py, tests/runtime/test_scoped_check.rs (split oversized units to clear pretender thresholds; base-file law-binding fix). Verified - just ci exit 0 x2 (local + pre-push), pretender check exit 0, spk lint 0 issues, cargo check clean-worktree exit 0, testaruda 262+14 results ingested green. Review - RO5U pass; HIGH law-binding bug found and fixed in-run; none open. Risks - none known; testaruda selection missed test_authored_laws (run_history empty) - selection coverage gap noted for follow-up. Next - run closed; openness-default run starts next.
