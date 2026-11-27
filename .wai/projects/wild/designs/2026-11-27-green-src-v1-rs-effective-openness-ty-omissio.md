---
tags: [pipeline-run:tdd-ro5-2026-11-27-implement-update-wild-openness-default-open-by-default-with-justified-closure-v1-in-place, pipeline-step:green]
---

GREEN: src/v1.rs - effective_openness(ty) (omission resolves true), closed_reason(ty) helper, closure-unjustified validation in validate_type record/sum branches (open==Some(false) requires non-empty closed_reason), subtype closed-pair reason-equality rule in record_subtype/sum_subtype, inhabits made pub for tests. schemas/wild-v1.schema.json - open off required, conditional closed_reason if/then, minLength 1. Narrow: cargo test --test v1_checker = 17 passed. Suite: just test green (263 python + 19 rust ingested, exit 0); pytest tests/test_spec_corpus.py 22 passed.
