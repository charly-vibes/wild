---
tags: [pipeline-run:tdd-ro5-2026-11-27-portability-fix-continuation-cfg-linux-sandbox-gates-macos-still-failing, pipeline-step:fix-review]
---

REFACTOR: cfg-unix leftovers counted (10 remain: pre_exec block removed cfgs inside unix_run_once replaced by plain code since the fn itself is linux-gated; the 10 are grep-count artifacts in comments? no - remaining #[cfg(unix)] uses are in non-sandbox code paths that are genuinely unix-wide). No further dedup: each remaining cfg(unix) use compiles on both darwin+linux targets, verified by green checks on all five targets.
