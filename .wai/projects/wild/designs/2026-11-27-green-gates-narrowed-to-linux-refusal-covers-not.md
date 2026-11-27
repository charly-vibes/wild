---
tags: [pipeline-run:tdd-ro5-2026-11-27-portability-fix-continuation-cfg-linux-sandbox-gates-macos-still-failing, pipeline-step:red]
---

GREEN: gates narrowed to linux; refusal covers not(linux). Verified: cargo check green on x86_64-unknown-linux-gnu, aarch64-unknown-linux-gnu, x86_64-apple-darwin, aarch64-apple-darwin, x86_64-pc-windows-msvc - zero errors each. Linux path unchanged; macOS/Windows both hit the same refusal branch (operational error, no unconfined suite execution).
