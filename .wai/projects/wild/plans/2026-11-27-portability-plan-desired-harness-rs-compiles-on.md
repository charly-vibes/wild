---
tags: [pipeline-run:tdd-ro5-2026-11-27-cross-platform-law-runner-portability-cfg-gate-linux-sandbox-refuse-elsewhere, pipeline-step:plan]
---

portability plan - Desired: harness.rs compiles on x86_64-pc-windows-msvc and aarch64-unknown-linux-gnu without changing Linux behavior. Narrow check: cargo check --target x86_64-pc-windows-msvc (red pre-fix: E0425 expected_wall/classify_spawn_error/rlimit symbols), cargo check --target aarch64-unknown-linux-gnu, cargo check (unix). Shape: cfg(unix) on the Landlock/rlimit consts, CommandExt import, sandbox_caps/landlock_abi_query, apply_rlimits/apply_landlock, classify_spawn_error (unix errno match); run_once becomes a dispatcher - non-Unix returns the operational refusal error, Unix body moves to unix_run_once. Files: src/harness.rs only. Out of scope: Windows/macOS sandbox alternatives, PATH/cwd env shaping semantics on non-Unix (unreachable - refusal precedes spawn).
