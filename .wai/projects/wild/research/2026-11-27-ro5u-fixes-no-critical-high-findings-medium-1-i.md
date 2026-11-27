---
tags: [pipeline-run:tdd-ro5-2026-11-27-widen-method-receiver-demands-wild-8j4, pipeline-step:fix-review]
---

RO5U-FIXES: no critical/high findings. MEDIUM(1) implicit pre-pass skip on unparseable mod files: DEFERRED - the walk still emits the named unsupported-construct gap for those files, so no silence; surfacing a duplicate note would double-report. MEDIUM(2) impl-level self gate: DEFERRED - deliberate declared choice matching the design wording 'public inherent impl'; per-method gating would contradict it; documented in account_impl comment and review. LOW(3) per-file map clones: TRACKED (cheap Arc later if bundle sizes grow). LOW(4) pre-existing scan_impl multi-segment self-type keying: TRACKED (pre-existing wild-158 shape, not introduced here). No behavior-impacting fixes; no new tests needed. Suites remain green (15 passed -k widen).
