---
tags: [pipeline-run:tdd-ro5-2026-11-27-fix-pretender-gate-violations-extract-rs-visitor-split-delivery-params-check-rs-length-harness-extract-field-counts-test-thresholds, pipeline-step:orient]
---

ORIENT: pretender-gate blocks push with 11 new violations (0.12 Rust checks): src/check.rs check() 217>200 lines; delivery.rs params 10/11/13>8 (validate_and_deliver, deliver, report_record); extract.rs void_mutator 9>3 + SourceWalk 17 fields>=10; harness.rs LawOutcome 10 fields>=10; test_on_absent.py/test_scoped_check.py cyclomatic 9/11>8; v1_checker.rs set_key 3, integer_slot 4 params>2. Fix = code refactor per pretender.toml ratchet contract; task selected.
