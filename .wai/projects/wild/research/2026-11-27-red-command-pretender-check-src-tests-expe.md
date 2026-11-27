---
tags: [pipeline-run:tdd-ro5-2026-11-27-fix-pretender-gate-violations-extract-rs-visitor-split-delivery-params-check-rs-length-harness-extract-field-counts-test-thresholds, pipeline-step:red]
---

RED: command='pretender check ./src ./tests'; expected failure=11 violations (check() function_lines 217>200; delivery params 10/11/13>8; extract.rs void_mutator 9>3 + excessive_fields 17; harness LawOutcome excessive_fields 10>=10; test cyclomatic 9/11>8; v1_checker params 3/4>2), observed exactly that set — exit confirms gate red for the violations, not setup breakage. Behavior-parity tests already exist and pass (tests/runtime/test_extract.py, test_update_*.py, tests/test_prototype_smoke.py run the real binary); they are the guard the refactor must keep green.
