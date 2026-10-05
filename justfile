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

# testaruda: hard gate — exec loop against the pushed base. Nonzero on
# test failure or calibrate-gate red.
testaruda-gate:
    git fetch origin main -q
    # Select-only-affected tests and run them (suite-proven wiring, matches
    # specodelic + espectacular; exec loop is the local dogfood pattern).
    testaruda select --safe --base origin/main --head HEAD
