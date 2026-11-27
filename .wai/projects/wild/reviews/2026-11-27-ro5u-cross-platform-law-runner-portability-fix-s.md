---
reviews: 2026-11-27-refactor-the-fix-itself-is-the-restructure-run.md
verdict: pass
tags: [pipeline-run:tdd-ro5-2026-11-27-cross-platform-law-runner-portability-cfg-gate-linux-sandbox-refuse-elsewhere, pipeline-step:ro5u-review]
---

RO5U: cross-platform law-runner portability fix (src/harness.rs, uncommitted at review).

CRITICAL: none.

HIGH: none.

MEDIUM: none.

LOW:
- The refusal error on non-Unix is returned by run_once per executed law, so a
  multi-law check on macOS/Windows reports each law as an operational error
  (exit 2). Acceptable: non-Unix never built before; the refusal is honest and
  loud, and the invocation commitment already records enforced=false.
- sandbox_caps on non-Unix returns enforced=false without probing anything;
  on macOS no equivalent probe exists (sandbox-exec is not used), so the
  constant is the truth, not a lie of omission.
- constants now carry 10 #[cfg(unix)] attributes instead of a cfg module -
  flatter but repetitive; fine at this size.

Evidence: cargo check green on x86_64-unknown-linux-gnu,
aarch64-unknown-linux-gnu, x86_64-pc-windows-msvc (zero errors); Linux-path
logic unchanged (same helper bodies, same pre_exec closure).

