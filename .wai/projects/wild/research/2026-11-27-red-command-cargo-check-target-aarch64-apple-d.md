---
tags: [pipeline-run:tdd-ro5-2026-11-27-portability-fix-continuation-cfg-linux-sandbox-gates-macos-still-failing, pipeline-step:red]
---

RED: command='cargo check --target aarch64-apple-darwin'; expected failure=same class as release run 46068214448 Build macOS (E0425 __rlimit_resource_t/prctl/SYS_LANDLOCK_* + E0308 mismatched types from misaligned cfg pairs); observed E0308 at src/harness.rs:386 (run_once body emptied on macOS because refusal was cfg(not(unix)) and dispatcher call was cfg(linux)). Windows was GREEN in the same run - unix-gating worked there, confirming the failure is macOS-specific unix-vs-linux divergence. Failure is the missing linux scoping, not setup breakage.
