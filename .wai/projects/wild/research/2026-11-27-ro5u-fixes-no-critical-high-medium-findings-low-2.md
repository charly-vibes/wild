---
tags: [pipeline-run:tdd-ro5-2026-11-27-cross-platform-law-runner-portability-cfg-gate-linux-sandbox-refuse-elsewhere, pipeline-step:fix-review]
---

RO5U-FIXES: no Critical/High/Medium findings. LOW dispositions: per-law operational error on non-Unix kept (loud and honest; non-Unix never built before); non-probing sandbox_caps kept (macOS has no equivalent probe; constant is truth); repetitive cfg attrs kept over a cfg module (10 attrs, flat, fine at this size). No code changes from review. Re-verified after disposition: cargo check on x86_64-linux, aarch64-linux, windows-msvc all green.
