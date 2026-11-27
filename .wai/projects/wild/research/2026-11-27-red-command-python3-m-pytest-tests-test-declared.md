---
tags: [pipeline-run:tdd-ro5-2026-11-27-declared-bump-derivation-wild-zh6, pipeline-step:red]
---

RED: command=python3 -m pytest tests/test_declared_bump.py -q expected=failing-first (no wild bump subcommand, no derivation) then green after src/bump.rs; final: 16 passed on test_declared_bump.py + test_contract_bundle_ci.py; pretender green; full just ci 297 results ingested green; ah check --run-tests 125 passed.
