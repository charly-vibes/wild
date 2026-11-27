---
tags: [pipeline-run:tdd-ro5-2026-11-27-portability-fix-continuation-cfg-linux-sandbox-gates-macos-still-failing, pipeline-step:quality-ledger]
---

QUALITY LEDGER (portability continuation): Changed - src/harness.rs only (cfg(unix) -> cfg(target_os='linux') on all Linux-sandbox items; refusal branch not(linux)). Verified - cargo check zero errors on x86_64-unknown-linux-gnu, aarch64-unknown-linux-gnu, x86_64-apple-darwin, aarch64-apple-darwin, x86_64-pc-windows-msvc. Review - RO5U pass (LOW-only dispositions). Risks - darwin is check-only locally; the real proof is the next release run's Build macOS. Next - commit, re-move unconsumed v0.2.1 tag to the fixed HEAD, watch the third release run.
