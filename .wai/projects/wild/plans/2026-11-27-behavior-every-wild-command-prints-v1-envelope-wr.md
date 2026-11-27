---
tags: [pipeline-run:tdd-ro5-2026-11-27-wild-lof-genesis-envelope-wrap-of-v1, pipeline-step:plan]
---

Behavior: every wild command prints v1 envelope wrapped as data in genesis shell (ok/envelope_version/cli_version/envelope_kind/data/warnings/meta); decision accept->ok, refuse->check, else error; v1 payload bytes unchanged. Out of scope: serde/genesis-vibes dep, tests/ python fixtures, exit codes. Tests: src/genesis.rs in-file (verbatim payload, kind mapping). Narrow: cargo test genesis. Full: cargo test && cargo build. Files: src/genesis.rs, src/lib.rs, src/main.rs. (RED/GREEN already recorded; tests passing.)
