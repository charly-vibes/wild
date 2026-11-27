---
tags: [pipeline-run:tdd-ro5-2026-11-27-release-workflow-five-target-binaries-checksums-readme-install-wild-bsp, pipeline-step:refactor]
---

REFACTOR: no production code changed in this slice (CI config + docs only). Rework during the run: v0.2.0 tag discovery forced the version-bump path (0.2.1) instead of re-tagging; README install section rewritten to lead with the no-toolchain curl|tar path after first draft. Openness-contract gate-pattern fix (12f3d75d98) landed as a separate commit since it belongs to the prior run's contract set, recorded in its own artifact trail.
