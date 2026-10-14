---
tags: [pipeline-run:tdd-ro5-2026-10-13-wild-1xk-held-out-corpus-execution-seal-corpus-register-real-adapters-run-comparison-produce-report, pipeline-step:fix-review]
---

---
tags: [ro5u, wild-1xk]
---

# RO5U Review — wild-1xk held-out corpus execution slice

Scope: experiments/heldout_corpus.py, experiments/heldout_adapters/{_cargo_semver,host_ranges,ci,ecosystem,wild}.py, tests/test_heldout_corpus.py.

Five passes: correctness, edge cases, clarity, consistency, tests.

## Findings

- **Critical: 0**
- **High: 0**
- **Medium: 0**
- **Low: 2**

### FIND-001 (low) — experiments/heldout_adapters/ci.py
Evidence: inner replay subprocess timeout=120s vs heldout_eval.CHECKER_TIMEOUT_SECONDS=60; a hung replay would be attributed to the harness kill, not the adapter.
Fix: align inner timeout to 55s with a comment citing the harness cap.

### FIND-002 (low) — experiments/heldout_corpus.py
Evidence: corpus build does not refuse duplicate case ids; a duplicated id would silently dedup in the harness split document.
Fix: refuse duplicates with exit 2; add red-first test.

## Verdict

pass — no behavior-impacting critical/high findings; comparison artifacts remain valid.

