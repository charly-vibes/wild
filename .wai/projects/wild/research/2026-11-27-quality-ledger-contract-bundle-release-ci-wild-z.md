---
tags: [pipeline-run:tdd-ro5-2026-11-27-contract-bundle-release-ci-wild-zjv-wild-twd, pipeline-step:quality-ledger]
---

QUALITY LEDGER: contract-bundle release CI (wild-zjv + wild-twd).
Changed: wild — .github/workflows/release.yml (pinned wild-vibes 0.2.1 install + Extract contract bundle step before provenance; bundle asset in gh release create), scripts/make-contract-bundle.sh (new), tests/test_contract_bundle_ci.py (new, 4 contract tests), README.md Contract bundle section, CHANGELOG.md Unreleased, Cargo.toml exclude scripts/**, openspec change add-wild-contract-bundle-convention tasks.md 3.2 status note. ddl — .github/workflows/release.yml (same two steps + asset line), scripts/make-contract-bundle.sh (new, tool=ddl), README.md Contract bundle section, CHANGELOG.md Unreleased.
Verified: pytest tests/test_contract_bundle_ci.py -q → 4 passed (RED first: wiring test failed before release.yml edits); ddl script end-to-end against the real ddl checkout: 405 tracked files committed, extract exit 1 (honest gap accounting) attached, manifest.toml stamped commit bcfe98d == HEAD, contract_sha256 recomputed clean (DIGEST-VERIFIED); both release.yml parse as YAML; bash -n clean on both scripts.
Review: RO5U pass, no critical/high; two deferred mediums (per-release extractor version bump policy; ddl-side shell verification is local-only — consumer law pinned by ddl Rust tests/contract_bundle.rs).
Risks: none known — bundles are advisory evidence (shadow_never_blocks); unknown-verdict bundles attach by design.
Next: orchestrator gates (just test, openspec validate --all --strict, spk lint openspec, ah check).
