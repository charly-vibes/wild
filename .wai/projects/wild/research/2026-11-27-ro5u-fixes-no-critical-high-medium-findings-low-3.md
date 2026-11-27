---
tags: [pipeline-run:tdd-ro5-2026-11-27-portability-fix-continuation-cfg-linux-sandbox-gates-macos-still-failing, pipeline-step:quality-ledger]
---

RO5U-FIXES: no Critical/High/Medium findings. LOW dispositions: remaining cfg(unix) uses verified compiling on both darwin targets and left as-is; unix_run_once name kept (rename would churn the semantic fix; tracked as a nit). No code changes from review. Re-verified: cargo check green on all five targets.
