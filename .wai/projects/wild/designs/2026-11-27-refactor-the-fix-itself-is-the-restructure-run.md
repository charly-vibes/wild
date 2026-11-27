---
tags: [pipeline-run:tdd-ro5-2026-11-27-cross-platform-law-runner-portability-cfg-gate-linux-sandbox-refuse-elsewhere, pipeline-step:ro5u-review]
---

REFACTOR: the fix itself is the restructure - run_once split into a platform dispatcher and unix_run_once body (single source of truth for the Unix path; no duplicate logic). One intermediate compile attempt had a brace mishandling caught immediately by cargo check (unclosed delimiter) and repaired in the same session before any test run; no behavior folded in. Linux path byte-equivalent: identical helper bodies, same pre_exec closure, same spawn/kill/validate sequence.
