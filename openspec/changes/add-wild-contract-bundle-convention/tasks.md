# Tasks: add-wild-contract-bundle-convention

## 1. Implementation — release-CI bundle attach (pilot: testaruda, bd follow-up with owner slot)

- [x] 1.1 In charly-vibes/testaruda's release workflow, add a bundle step: `wild extract` on the exact release checkout (same job/tree as the published artifact), write `manifest.toml` (tool, version, commit, profile, contract_sha256, extractor_version, extracted_at), pack tar+gzip, attach as `<tool>-<version>-contract-bundle.tar.gz` — landed testaruda 5a33d22: pinned wild-vibes 0.2.0 extractor install + scripts/make-contract-bundle.sh (attaches on extract exit 0/1, fails on exit 2)
- [x] 1.2 Verify the stamped digest: unpack the released bundle, recompute sha256(contract.json), compare to manifest; document the verification one-liner in the tool repo — verified end-to-end locally against the real checkout (stamped commit matches HEAD); one-liner documented in testaruda README (Contract bundle section)

## 2. Implementation — ddl consumer side (bd follow-up, ddl repo owner)

- [ ] 2.1 D2 refusal law in the bundle loader: recompute sha256(contract.json), refuse on `bundle-digest-mismatch`; refuse on `bundle-commit-mismatch` when manifest commit ≠ target release commit; named diagnostics, never silent acceptance
- [ ] 2.2 D3 base-contract cache: cache the base bundle at install/upgrade commit time under `contracts/<tool>/<version>/` in the ddl state dir; record the contract digest in the lock entry; missing/corrupt cached base → `missing-base-contract` diagnostic and Unknown verdict (never fabricated, never skipped)
- [ ] 2.3 D4 shadow rendering: in `dulce_de_leche::installer::upgrade_tool` / `upgrade_all_tools` (observed at `src/main.rs::cmd_upgrade`), fetch + verify the candidate bundle, run `wild check` candidate-vs-installed-base, render compatible / incompatible / unknown + named reasons beside the existing semver/age decision; exit codes and gating unchanged

## 3. Pilot cross-check and fleet rollout

- [x] 3.1 Run `experiments/wild_adopt_audit.py --crate testaruda` against released bundles and cross-check shadow verdicts with the measured rung-1 verdicts (`results/adopt-audit-158-1.txt`); record as `results/shadow-pilot-<n>.txt` — results/shadow-pilot-1.txt: 14/14 pairs abstained (was 12/12 pre-0.5.7), determinism pass, 100% abstention — the expected honest outcome; released bundle testaruda-0.5.7-contract-bundle.tar.gz digest-verified from the live release asset (stamped commit d573796 == tag commit)
- [ ] 3.2 Work the per-tool owner tickets (filed by wild-cdp.3) in owner order: bundle step per repo's `release.yml`
- [ ] 3.3 Rung-3 gating remains out of scope until real gap rates are measured from the pilot data

## 4. Validation

- [ ] 4.1 `openspec validate --all --strict`; `spk lint openspec`; `ah check` (contracts bind at archive)
- [ ] 4.2 Archive the change only after all gates are green; baseline `ah check --run-tests` post-archive
