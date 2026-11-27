---
tags: [pipeline-run:tdd-ro5-2026-11-27-widen-method-receiver-demands-wild-8j4, pipeline-step:green]
---

GREEN: bundle-wide pre-pass (BundlePrepass::scan_crate in method_demands.rs, called from walk_crates pass 1; mod_files scan call retired, mod_file_candidates shared), let-bound single-assignment locals (visit_local/visit_block/visit_expr_assign in extract.rs + record_let_binding/resolve_let_init/binding_type/clear_binding), inventoried field access (field_tys), self/Self via current_impl_type (type_inventory.rs, public inherent impls on named path types), hop-folded chains in resolve_method_receiver. Narrow cmd: python3 -m pytest tests/runtime/test_extract.py -k widen -q -> 11 passed (9 new red-to-green, 2 existing receiver tests stay green).
