---
tags: [pipeline-run:tdd-ro5-2026-10-09-wild-mh5-1-extract-rust-contracts-local-1-schema-canonical-reader-extract-path, pipeline-step:refactor]
---

REFACTOR: collapsed main.rs outcome flow from (closure -> Option<ExtractionOutcome> -> triple match with unreachable Ok(Some)/Ok(None) arms) to a single Result<ExtractionOutcome, String> with a two-arm match producing (exit_code, envelope_value, report). No behavior change: pytest 11/11 green, cargo test 2/2 green.
