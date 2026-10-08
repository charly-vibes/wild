# AFK runbook — wild-aoq.5 bootstrap fixture tracer bullet

Autonomous implementation loop for beads `wild-aoq.5`
(Replay minimal independent Rust update and protection cases).

## Goal

Make `tests/test_initial_update_fixtures.py` go green by building the
immutable bootstrap fixtures it demands. Nothing else. The tests are the
agreed scoped outcomes — do not weaken or rewrite them.

## The loop

1. `python3 -m pytest tests/test_initial_update_fixtures.py -q` — red list
2. Implement one fixture artifact at a time under
   `experiments/update_fixtures/bootstrap/`:
   - `cases.json` — schema `wild-bootstrap-cases-v1`; fields per test:
     `schema`, `toolchain.rustc` (exact `rustc --version` output),
     `catalog` (`dept`: 1.2.3, 1.2.4, 2.0.0), `cases[]` each with `id`,
     `class`, and for the two native cases `native_outcome` + `target`,
     for declaration cases `declared` (with `verified` absent or false),
     plus `artifacts[]` (`path` + `sha256`)
   - `registry/` — frozen local git-index Cargo registry serving `dept`
     1.2.3 / 1.2.4 / 2.0.0. Must enforce ranges through real Cargo
     resolution. **No path replacement** of the dependency.
   - `consumer/` — small Cargo crate depending on `dept = "~1.2"`, with a
     test exercising an API removed in 1.2.4 (used) and code untouched by
     the 2.0.0 removal (unused), plus rustfmt-canonical source
   - `README.md` — fixture provenance and versioning policy
3. Re-run pytest until green. Behavioral red only; if a test fails for an
   environment reason, fix the environment, never the expectation.
4. Full gates: `JUST_TEMPDIR=/tmp just ci` and
   `openspec validate --all --strict --no-interactive`
5. `bd close wild-aoq.5`, push branch, open/merge per project flow.

## Constraints (from the ticket — verbatim anti-goals)

- No full reporting engine, no E5 strata, no agent runner, no new public
  protocol in this slice
- No weakening existing tests, no overwriting oracle expectations to match
  a miner, no path replacement to claim overcoming a version range
- New dependencies must be required for scope, pinned and explained
- Fixture commitments are immutable: changing an expectation appends a
  version with justification, never rewrites history
- New source files carry Purpose / Responsibilities / Rationale headers
- The caller's checkout must not be modified by test replays (tests copy
  to tempdirs already)
- Expected checker/protection outcomes stay declarations — `verified`
  must never be true until a checker exists

## Gates (already verified green before the loop starts)

- `ah check --run-tests` → 23 checks OK
- `pretender check` → green (`.devenv/**` excluded)
- `spk lint openspec` → green
- `openspec validate --all --strict` → 12 passed
- `testaruda exec --base origin/main --head HEAD` → will run the fixture
  suite at file granularity; exit 1 until the tests go green

## Known-good environment

cargo 1.98.1 / rustc 1.98.1 / Python 3.14.7 / pytest 9.0.3 (global; devenv
venv pending under wild-r03). `testaruda.toml` has an intentional uncommitted
user edit — leave it untouched.
