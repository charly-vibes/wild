---
tags: [pipeline-run:tdd-ro5-2026-11-27-widen-method-receiver-demands-wild-8j4, pipeline-step:quality-ledger]
---

QUALITY LEDGER: widen-method-receiver-demands (wild-8j4).

Changed:
- src/extract/method_demands.rs — bundle-wide BundlePrepass (return types of public fns + inherent-impl methods, public named-field types; scans crate root + public non-inline module files), scan_crate returns the maps; scan_impl/scan_struct_fields are &self collectors; scan_mod_declarations merged into scan_items's Mod arm. let-bound single-assignment locals (record_let_binding/resolve_let_init/binding_type/clear_binding), inventoried field access, self/Self via current_impl_type, hop-folded chains in resolve_method_receiver.
- src/extract.rs — pre-pass call site extends shared_fn_tys/shared_field_tys from the returned maps.
- src/extract/type_inventory.rs — public inherent impls on single-segment path types set impl-type context (rule 4).
- src/extract/mod_files.rs — mod_file_candidates shared by walk and pre-pass.
- tests/runtime/test_extract_widen.py (new) + tests/runtime/test_extract.py — 9 receiver scenarios as 2 parametrized tests + 2 distinct tests; test_extract.py back under the file-lines cap.
- openspec/specs/wild-extract/spec.md + openspec/changes/widen-method-receiver-demands/** — delta mirrored, 6 contract TOMLs (re-pointed to parametrized ids).
- docs/wild-manual.md — demand-profile section.
- results/adopt-audit-8j4-20261127.txt — measured gate rerun + residual partition.

Verified:
- cargo build clean; cargo fmt clean; clippy: no warnings in touched files (remaining lib warnings pre-date this change in bump.rs/feedback.rs/main.rs/genesis.rs).
- pytest test_extract.py + test_extract_widen.py: 46 passed (17 widen-related).
- just test (testaruda loop): 160 results ingested, green.
- pretender check: rc=0, resolution 4 fixed since last check (void_mutator 6>3, file_lines, lazy_cluster, params all cleared).
- ah check: no issues; spk lint openspec: 0 issues; openspec validate --all --strict: 16/16.
- adopt-audit rerun: 16/16 abstained as before, residual partitioned (literal receiver by design, std::time::Duration::from_millis external-crate demand -> wild-90d, trait-impl Default unsupported-construct); no receiver-gap storm.

Review:
- RO5U review: no critical/high. MEDIUM(1) implicit pre-pass skip on unparseable mod files DEFERRED (walk still emits the named gap; no silence). MEDIUM(2) impl-level self gate DEFERRED (declared 'public inherent impl' semantics). LOW(3) per-file map clones TRACKED. LOW(4) pre-existing multi-segment scan_impl keying TRACKED.

Risks:
- Option A (typed-receiver facts as extraction inputs) filed as wild-6fe; wild-90d (external-crate awareness) remains the unlock for non-abstaining adopt-audit verdicts.

Next:
- Commit gate-fix round and push (pre-push gate now green).
