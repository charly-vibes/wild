---
tags: [pipeline-run:tdd-ro5-2026-11-27-implement-update-wild-openness-default-open-by-default-with-justified-closure-v1-in-place, pipeline-step:red]
---

RED: command='cargo test --test v1_checker'; expected failure=4 new tests (omitted_open_resolves_open, unjustified_closure_is_rejected, omitted_open_and_explicit_true_are_distinct_ids_that_accrete, closure_reason_edit_is_break); observed exactly 4 failed / 12 passed before implementation; schema gate test_v1_openness_default_omitted_is_open_and_closure_needs_reason red against required-open schema (python3 -m pytest tests/test_spec_corpus.py). Failure is the missing behavior (closed fallback, no closure validation), not setup breakage.
