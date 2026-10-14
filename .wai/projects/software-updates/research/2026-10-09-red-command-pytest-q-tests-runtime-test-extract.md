---
tags: [pipeline-run:tdd-ro5-2026-10-09-wild-mh5-1-extract-rust-contracts-local-1-schema-canonical-reader-extract-path, pipeline-step:red]
---

RED: command='pytest -q tests/runtime/test_extract.py' expected failure=every test errors at the session wild_binary fixture: 'cargo build failed: could not find Cargo.toml in <repo root>' — the Rust crate itself is the slice deliverable and does not exist yet, so the missing behavior is exactly the absent extractor. 11 red tests pin: 3-run byte identity, relocation/formatting invariance with distinct provenance, macro export incomplete inventory + unsupported-construct/incomplete-demand diagnostics, changed-build-input refusal (exit 2 input-mismatch), demand resolution direct+alias, 5 malformed-request refusals (exit 2), zero source writes.
