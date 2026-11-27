---
tags: [pipeline-run:tdd-ro5-2026-11-27-portability-fix-continuation-cfg-linux-sandbox-gates-macos-still-failing, pipeline-step:refactor]
---

GREEN: every Linux-sandbox item narrowed from cfg(unix) to cfg(target_os='linux'); refusal branch widened to not(linux) so macOS joins Windows in the refusal. Verified: cargo check green (zero errors) on x86_64-unknown-linux-gnu, aarch64-unknown-linux-gnu, x86_64-apple-darwin, aarch64-apple-darwin, x86_64-pc-windows-msvc. Linux path unchanged; macOS/Windows hit the identical refusal (operational error, no unconfined suite execution).
