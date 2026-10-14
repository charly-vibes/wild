---
tags: [pipeline-run:tdd-ro5-2026-10-13-wild-1xk-validate-wild-upgrade-decisions-on-a-held-out-corpus-against-existing-checks, pipeline-step:refactor]
---

REFACTOR wild-1xk: tidy pass while green (16/16 after). Removed the args_timeout() indirection in favor of a CHECKER_TIMEOUT_SECONDS module constant; consolidated split family computation — _split_document now derives families deterministically from validated cases (single source of truth, no post-hoc overwrite in cmd_split). No behavior expansion, no unrelated cleanup, no architectural rewrite. Tests green after refactor.
