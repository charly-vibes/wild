---
tags: [pipeline-run:tdd-ro5-2026-10-13-wild-m7f-std-macro-demand-support, pipeline-step:fix-review]
---

RO5U-FIXES (wild-m7f.3): 0 CRITICAL / 0 HIGH. MEDIUM both fixed: M1 — format_args! omission documented in design.md exclusion note + follow-up bd ticket filed (bd comment on epic wild-m7f); NOT added to whitelist (would exceed approved proposal semantics). M2 — new permanent test test_relocation_and_formatting_preserve_semantic_identity_with_macro pins contract-byte identity across formatting with a whitelisted macro present (provenance stays location-accurate); verified empirically before pinning. LOW deferred with reason: std-aliased macro head (use std::println as p; p!()) refuses — conservative and consistent with the alias law; covered by the unlisted-head rule. Tests after fixes: tests/runtime/test_extract.py 18/18 green.
