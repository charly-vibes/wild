---
tags: [pipeline-run:tdd-ro5-2026-11-27-cross-platform-law-runner-portability-cfg-gate-linux-sandbox-refuse-elsewhere, pipeline-step:red]
---

RED: command='cargo check --target x86_64-pc-windows-msvc'; expected failure=same class as release run 46066406609 Build Windows (E0433 cannot find 'unix' in std::os, E0425 libc rlim_t/rlimit/setrlimit/RLIMIT_*/syscall/prctl) and Build macOS (exit 101); observed locally before the fix: E0425 'cannot find value expected_wall' + 'cannot find function classify_spawn_error' (after partial cfg) and the same symbol set reported by CI before any edit. Failure is the missing portability (Unix-only code compiled unconditionally), not setup breakage. Also 'gh run view 46066406609 --json jobs': Build Windows failure, Build macOS failure, publish skipped.
