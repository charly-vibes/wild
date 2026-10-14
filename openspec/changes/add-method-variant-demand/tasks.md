# Tasks: add-method-variant-demand

## 1. Red — conformance fixtures (bd wild-158)
- [x] 1.1 Add failing `-k widen` tests to `tests/runtime/test_extract.py`: same-crate constructor-receiver method demand resolves; method absent from inventory gaps naming the full path; unbounded chain receiver gaps naming the receiver while keeping the one-hop demand; enum variants inventory as named slots (opaque enum item gone) and dep-qualified + same-crate variant demands resolve; unknown variant paths gap naming the path; per-construct impl accounting (no blanket gap, type-qualified slot, named gaps for trait impls and `pub(crate)` method)
- [x] 1.2 Prove red (6/6 failing against the pre-widening extractor) and confirm existing gates still pass

## 2. Green — extractor semantics (bd wild-158)
- [x] 2.1 D2: variant inventory in `src/extract/type_inventory.rs` (versioned meanings, cfg/generic honest gaps) + bounded same-crate demand resolution (`bounded_target`) + multi-segment expression paths and struct-literal demand recording
- [x] 2.2 D1: bounded receiver resolution in `src/extract/method_demands.rs` (`resolve_method_receiver`, `handle_method_call`) + per-file return-type pre-pass (`scan_fn_returns`, hooked in `walk_crates` and `mod_files::resolve_mod_file`)
- [x] 2.3 D3: per-construct impl accounting in `type_inventory::account_impl` (type-qualified pub method slots, private items without public surface, named gaps for restricted items and trait impls, bodies walked)
- [x] 2.4 All suites green: pytest tests/runtime 122 passed, cargo test 12 passed, pretender ratchets green (extract.rs under 1200 lines)

## 3. Spec, docs, validation
- [ ] 3.1 `openspec validate --all --strict`; `ah check` (overlay while change open)
- [ ] 3.2 Update `docs/wild-local-v1.md` supported-set description
- [ ] 3.3 Audit re-run `python3 experiments/wild_adopt_audit.py --crate testaruda` recorded as `results/adopt-audit-158-<n>.txt`; record gap distribution vs `results/adopt-audit-cdp4-1841.txt` in the rung-1 addendum of the dogfooding research doc
- [ ] 3.4 Archive the change only after all gates are green; baseline `ah check --run-tests` post-archive
