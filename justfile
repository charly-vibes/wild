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
testaruda-gate:
    #!/usr/bin/env bash
    set -uo pipefail
    git fetch origin main -q
    code=0
    testaruda exec --base origin/main --head HEAD || code=$?
    case "$code" in
      0|10|20) exit 0 ;;
      *) echo "❌ testaruda gate failed (exit $code — test runner or hard error)" >&2; exit 1 ;;
    esac
