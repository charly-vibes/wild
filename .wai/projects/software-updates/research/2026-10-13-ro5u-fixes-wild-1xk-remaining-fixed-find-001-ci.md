---
tags: [pipeline-run:tdd-ro5-2026-10-13-wild-1xk-held-out-corpus-execution-seal-corpus-register-real-adapters-run-comparison-produce-report, pipeline-step:quality-ledger]
---

RO5U-FIXES wild-1xk-remaining: fixed FIND-001 (ci.py inner replay timeout aligned to ADAPTER_TIMEOUT_SECONDS=55 < harness CHECKER_TIMEOUT_SECONDS=60, with a pinned unit test asserting the constant stays under the cap) and FIND-002 (heldout_corpus.py pre-scans cohort case ids upfront and refuses duplicates with exit 2 + red-first test test_corpus_build_refuses_duplicate_case_ids). Narrow suite 14/14 green. Freeze re-frozen after code changes; comparison + report re-run for artifact/code consistency; compare.json carries freeze_sha256 + oracle_sha256 provenance. No remaining unfixed findings.
