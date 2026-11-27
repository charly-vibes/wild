---
tags: [pipeline-run:tdd-ro5-2026-11-27-contract-bundle-release-ci-wild-zjv-wild-twd, pipeline-step:red]
---

RED: command=python3 -m pytest tests/test_contract_bundle_ci.py -q; expected failure=release.yml has no pinned extractor install, no bundle step, no contract-bundle asset in gh release create (test_workflow_installs_pinned_extractor_and_attaches_bundle fails on missing wiring); 2 of 4 pass because the bundle script landed pre-gate, gate caught it, run tdd-ro5-2026-11-27-contract-bundle-release-ci-wild-zjv-wild-twd now covers it
