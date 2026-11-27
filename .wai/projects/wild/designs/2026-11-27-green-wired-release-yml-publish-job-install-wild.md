---
tags: [pipeline-run:tdd-ro5-2026-11-27-contract-bundle-release-ci-wild-zjv-wild-twd, pipeline-step:green]
---

GREEN: wired release.yml publish job (Install wild extractor cargo install wild-vibes --version 0.2.1 --locked; Extract contract bundle before provenance so the bundle digest is bound; asset added to gh release create). python3 -m pytest tests/test_contract_bundle_ci.py -q → 4 passed. Cargo.toml exclude gained scripts/** so the CI script never ships in the crate.
