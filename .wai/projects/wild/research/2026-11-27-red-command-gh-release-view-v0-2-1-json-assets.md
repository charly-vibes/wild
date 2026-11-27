---
tags: [pipeline-run:tdd-ro5-2026-11-27-release-workflow-five-target-binaries-checksums-readme-install-wild-bsp, pipeline-step:red]
---

RED: command='gh release view v0.2.1 --json assets'; expected failure=release not found (no tag, no workflow); observed 'HTTP 404: release not found' before the bump+push, and 'workflow release.yml not found on the default branch' - the acceptance check is red at start: no release, no workflow. Failure is the missing artifact, not setup breakage. (TDD order note: the workflow file itself is CI config, not production code; its acceptance is the green release run on the tag, recorded as the GREEN step evidence.)
