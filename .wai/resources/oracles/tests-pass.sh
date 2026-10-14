#!/usr/bin/env bash
# tests-pass.sh — pipeline gate oracle: the narrow runtime meter for the
# current slice must pass, plus the crate's own unit suite.
# Exit 0 = pass, non-zero = fail. Stderr is shown on failure.
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
python3 -m pytest -q tests/runtime/test_extract.py
cargo test -q
