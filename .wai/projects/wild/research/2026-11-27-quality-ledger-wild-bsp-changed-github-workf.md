---
tags: [pipeline-run:tdd-ro5-2026-11-27-release-workflow-five-target-binaries-checksums-readme-install-wild-bsp, pipeline-step:quality-ledger]
---

QUALITY LEDGER (wild-bsp): Changed - .github/workflows/release.yml (new, five-target DDL-standard workflow), README.md (Install section), Cargo.toml/Cargo.lock (0.2.1), plus gate-pattern fix commit 12f3d75d98 (6 scenario TOMLs + tests/runtime/test_openness_scenarios.py) belonging to the prior run's contract set. Verified - just ci green; ah check --run-tests OK 14 passed; workflow YAML parse-checked; tag v0.2.1 pushed, release run 46066406609 launched (assets verified on completion). Review - RO5U pass; one MEDIUM (tag one commit behind main) dispositioned not-fixed; three LOW follow-ups to file. Risks - tagged tree fails test_gate_wiring until next tag (documented); crates.io/tap channels not wired (reported, not failed). Next - watch release run to completion, verify assets, close wild-bsp.
