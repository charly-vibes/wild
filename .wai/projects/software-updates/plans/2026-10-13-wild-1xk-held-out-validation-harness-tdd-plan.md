---
tags: [pipeline-run:tdd-ro5-2026-10-13-wild-1xk-validate-wild-upgrade-decisions-on-a-held-out-corpus-against-existing-checks, pipeline-step:plan]
---

# wild-1xk — Held-out validation harness (TDD plan)

## Desired behavior

A committed, replayable held-out evaluation pipeline in `experiments/` that:

1. **Freezes the evaluation tooling** — a `freeze.json` manifest records sha256
   digests of every tool the evaluation depends on (wild binary, python harness
   files, fixture manifests). Any comparison run verifies the freeze first and
   refuses (exit 2) on drift — no re-extraction mid-evaluation.
2. **Enforces the sealed held-out/dev split** — a committed `split.json` assigns
   every case to `development` or `held_out` by repo/release family (never
   adjacent commits of the same family). Development-side commands refuse
   held-out case ids. Held-out oracle outcomes are **sealed** (digest-committed)
   before any Wild run; the comparison run refuses if the seal is missing or
   the sealed file changed.
3. **Runs a four-way comparison per case** — host declared version ranges, CI,
   an ecosystem compatibility tool, and Wild as an additional check. Each
   checker's verdict classifies into exactly one of: correct-accept,
   correct-reject, **missed-breakage**, **false-block**, unknown/error.
4. **Emits a separate-metrics report** — missed breakages, false blocks,
   Unknown rate, coverage, execution cost, human contract-maintenance time —
   each per checker, each with explicit denominators; zero denominators yield
   null ratios with named reasons (same discipline as `update_eval.py`).
   Aggregate accuracy is never a substitute.

Honesty framing is normative: outputs are value-proposition validation, NOT
evidence about future v1 runtime failure rates. The report must carry this
 disclaimer verbatim.

## Out of scope

- Any runtime semantics change to `src/` (would require the OpenSpec workflow).
- The full 600-run E5 pilot cohort (aoq scope).
- Introducing Nix pins if the build oracle is already hermetic (offline frozen
  registry + digest-verified fixtures, as in aoq.2/aoq.3) — record the
  decision explicitly in the freeze manifest instead.
- Authoring new real-repo case corpora; the held-out slice is authored under
  sealed-set discipline (oracle outcomes graded independently, committed
  before Wild runs) reusing the E5 fixture construction style.

## Test cases to write (red-first, `tests/test_heldout_eval.py`)

1. **Freeze build/verify round-trip** — build freeze manifest from fixture
   tooling; verify exits 0. Tamper one tool byte; verify exits 2 naming the
   drifted path.
2. **Split enforcement** — dev-side subcommand invoked against a held-out case
   id refuses with a leakage diagnostic; family assignment is deterministic
   (same input manifest → same split, stable across runs).
3. **Sealed-oracle discipline** — comparison run before seal exists refuses;
   run after sealed file is modified refuses with digest mismatch; run with
   intact seal proceeds.
4. **Verdict classification** — each checker verdict maps to exactly one
   outcome class; a staged 4-case set yields one each of missed-breakage,
   false-block, correct-accept, correct-reject for the right checkers.
5. **Separate-metrics report** — report emits per-checker sections with
   explicit denominators; zero-denominator metric renders null ratio + named
   reason; no metric is merged across checkers; disclaimer present.
6. **Exit mapping** — all-correct → 0; any missed-breakage/false-block → 1;
   harness/refusal errors → 2.

## Commands

- Narrow: `pytest tests/test_heldout_eval.py -q`
- Full: `JUST_TEMPDIR=/tmp just ci` (+ `openspec validate --all --strict`)

## Files likely touched

- NEW `experiments/heldout_eval.py` (single-file CLI: freeze/verify, split,
  seal, compare, report — kept separate from `update_eval.py` to respect the
  pretender file-lines ratchet)
- NEW `experiments/heldout_fixtures/` (freeze.json, split.json, sealed oracle,
  held-out case set)
- NEW `tests/test_heldout_eval.py`
- Possibly a docs note in the experiments README section
