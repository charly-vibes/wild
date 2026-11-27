---
tags: [pipeline-run:tdd-ro5-2026-11-27-portability-fix-continuation-cfg-linux-sandbox-gates-macos-still-failing, pipeline-step:plan]
---

continuation plan - Narrow cfg(unix) to cfg(target_os='linux') on every Linux-sandbox item (consts, CommandExt, sandbox_caps, landlock_abi_query, apply_rlimits, apply_landlock, classify_spawn_error, unix_run_once, dispatcher call); refusal cfg becomes not(linux) so macOS falls into the refusal branch. Check: cargo check on all five targets (linux x2, darwin x2, windows) - all green.
