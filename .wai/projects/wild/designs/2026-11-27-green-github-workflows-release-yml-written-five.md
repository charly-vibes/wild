---
tags: [pipeline-run:tdd-ro5-2026-11-27-release-workflow-five-target-binaries-checksums-readme-install-wild-bsp, pipeline-step:green]
---

GREEN: .github/workflows/release.yml written (five target archives wild_{version}_{os}_{arch}.tar.gz/.zip + checksums.txt + provenance.json; build-linux/darwin/windows + test(cargo test --locked) + publish with pinned actions and publish-only contents:write; crates.io publish token-guarded); README Install section (curl|tar for linux amd64, naming note for darwin/windows + checksums/provenance, cargo install wild-vibes); Cargo.toml/Cargo.lock bumped to 0.2.1 (v0.2.0 tag already pushed, never released, workflow absent at push time - tag not moved). Verification: workflow YAML parses (5 jobs, publish needs all four); README install block's curl|tar is executable without rustup; release acceptance green only after push (recorded when the run completes).
