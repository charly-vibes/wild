---
tags: [pipeline-run:tdd-ro5-2026-11-27-release-workflow-five-target-binaries-checksums-readme-install-wild-bsp, pipeline-step:orient]
---

wild-bsp plan - Desired: v* tag push builds five standard archives (linux amd64/arm64, darwin amd64/arm64, windows amd64) + checksums.txt + provenance.json and publishes a GitHub release; publish job gated on the tagged-commit test run; all actions pinned to reviewed SHAs; README install section points at release assets and cargo install wild-vibes. Test: gh release view v0.2.1 --json assets lists the six assets; README block works without Rust (curl|tar, no rustup). Files: .github/workflows/release.yml (new), README.md, Cargo.toml/Cargo.lock (0.2.1 bump). Deviations from the DDL file, both stated in the header: binary wild / crate wild-vibes; no tap/scoop steps (no formula exists - separate decision); crates.io publish guarded on token presence (DDL-9e7 pattern). Full check: gh run watch for the release run.
