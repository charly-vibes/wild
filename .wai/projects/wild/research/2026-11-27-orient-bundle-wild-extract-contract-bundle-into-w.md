---
tags: [pipeline-run:tdd-ro5-2026-11-27-contract-bundle-release-ci-wild-zjv-wild-twd, pipeline-step:orient]
---

ORIENT: bundle wild extract contract bundle into wild release.yml (wild-zjv) and ddl release.yml (wild-twd) per add-wild-contract-bundle-convention task 3.2, mirroring the testaruda pilot (wild-xc4). RED = local end-to-end run of make-contract-bundle.sh: bundle contains exactly contract.json + manifest.toml, manifest commit == HEAD, contract_sha256 == recomputed digest, asset name wild-<version>-contract-bundle.tar.gz
