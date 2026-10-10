# justfile — single QA entry point for wild (suite standard: `just ci`).
#
# Four hard gates, matching the charly-vibes tool suite:
#   ah         — behavioral verification: structure + linked contract tests
#   pretender  — quality ratchet in gate mode (only ratchets DOWN)
#   specodelic — spec corpus frontmatter mandate (`spk lint openspec`)
#   testaruda  — affected-test gate: full exec loop (select → run → ingest → calibrate)

default: ci

# CI: same command lefthook pre-push runs. Exactly one entry point.
ci: ah-gate pretender-gate spec-lint testaruda-gate

# ah: hard gate — structure + contract-test execution.
ah-gate:
    ah check --run-tests

# pretender: hard gate — full check (gate mode config already ratchets only DOWN).
pretender-gate:
    pretender check

# specodelic: spec corpus gate.
spec-lint:
    spk lint openspec

# testaruda: hard gate — full exec loop (select → run → ingest → calibrate).
# CI contract (TIA-CI-001..004): 0 = selection complete, 10 = full run,
# 20 = nothing to run — all green. Any other code = runner failure or
# hard error, red.
#
# wild-z56: a stale local calibration store can select test paths that no
# longer exist at HEAD (e.g. after a branch switch), making the runner
# exit 4 (file not found) on local state, not real breakage. Self-heal:
# on exit 4 only, prune the store, re-init, and retry exec exactly once.
# Hard errors keep the gate red without a wasteful full re-run.
testaruda-gate:
    #!/usr/bin/env bash
    set -uo pipefail
    git fetch origin main -q
    code=0
    testaruda exec --base origin/main --head HEAD || code=$?
    case "$code" in
      0|10|20) exit 0 ;;
      4)
        echo "⚠️ runner exit 4 — pruning stale local calibration and retrying once (wild-z56)" >&2
        rm -rf .testaruda
        testaruda init || { echo "❌ testaruda re-init failed" >&2; exit 1; }
        testaruda exec --base origin/main --head HEAD ;;
      *) echo "❌ testaruda gate failed (exit $code — test runner or hard error)" >&2; exit 1 ;;
    esac
