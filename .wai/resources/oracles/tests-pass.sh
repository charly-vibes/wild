#!/usr/bin/env bash
# tests-pass.sh — pipeline gate oracle: the narrow runtime meter for the
# current slice must pass, plus the crate's own unit suite.
# Exit 0 = pass, non-zero = fail. Stderr is shown on failure.
set -euo pipefail

cd "$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# NB: `python3 -m pytest` resolves to the brew python which lacks pytest;
# the user `pytest` shim (/usr/bin/python3) has it. 35 runtime tests, 0.3s.
pytest -q tests/runtime/test_extract.py
cargo test -q
