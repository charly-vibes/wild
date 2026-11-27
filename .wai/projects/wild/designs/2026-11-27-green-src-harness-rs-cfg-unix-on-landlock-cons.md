---
tags: [pipeline-run:tdd-ro5-2026-11-27-cross-platform-law-runner-portability-cfg-gate-linux-sandbox-refuse-elsewhere, pipeline-step:red]
---

GREEN: src/harness.rs - cfg(unix) on Landlock consts, CommandExt import, sandbox_caps (non-Unix returns enforced=false/abi=None), landlock_abi_query, apply_rlimits, apply_landlock, classify_spawn_error; run_once dispatcher: non-Unix returns operational refusal (no unconfined suite execution), Unix body in unix_run_once. Narrow checks green: cargo check (x86_64 linux), cargo check --target aarch64-unknown-linux-gnu, cargo check --target x86_64-pc-windows-msvc - all Finished, zero errors. Linux behavior unchanged: unix path byte-identical logic (pre_exec rlimits+landlock, same helper bodies).
