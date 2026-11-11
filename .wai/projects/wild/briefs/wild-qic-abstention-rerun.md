# Brief: wild-qic — re-run abstention pilot after extractor widening

## Why
The 14/14 Unknown shadow-pilot baseline (results/shadow-pilot-1.txt, wild-xc4) predates wild-m7f (std macro surface) + wild-7e9 (string types) landing — no replay measures the abstention delta those extractor widenings bought. Delegated to a subagent: bounded replay + measurement; the lead orchestrates only (epic-orchestrator run 3/6).

## Ticket
- **ID:** wild-qic (claimed, P3, s, afk) — `bd show wild-qic`
- **Desired outcome:** the SAME 14-pair shadow-pilot replay re-run with the CURRENT wild binary; Unknown-rate delta vs the 14/14 baseline recorded under results/.

## Task
1. RED first: the Must gate below currently fails (no delta file under results/). Capture that.
2. Locate the baseline replay mechanics: read `results/shadow-pilot-1.txt` (its header/script refs + the exact 14 pairs), and `experiments/wild_adopt_audit.py` for how the CLI was invoked. If the original script isn't committed, reconstruct the replay from the recorded pair set — the PAIR SET must be identical to the baseline (pre-registration: do NOT swap pairs; a pair no longer replayable gets recorded as such, never replaced).
3. Build current binary: `cargo build --release` (target/release/wild — check Cargo.toml [[bin]] name if different).
4. Run the same 14 pairs through the current binary; per-pair verdict (Known/Unknown + which widened construct flipped it, if recorded); compute delta vs 14/14.
5. GREEN: write `results/shadow-pilot-2.txt` (or `shadow-pilot-delta-<date>.txt`): per-pair table, Unknown rate now vs baseline, delta line, binary commit (git rev-parse --short HEAD), wild version. Meter: pilot replay script — if a committed script doesn't exist, add `experiments/shadow_pilot.py` (or .sh) that reproduces BOTH runs given the binary, committed.
6. Update nothing else: no RESULTS.md edits required by this ticket (that's the other tickets' surface).

## HARD CONSTRAINTS
- Pair set frozen to the baseline's 14 — pre-registered, no cherry-picking, no additions.
- Do NOT touch src/, tests/, specs/, docs/, experiments/RESULTS.md, .beads/.
- Do NOT close the bd ticket; do NOT push.
- Commit ONLY: results/shadow-pilot-2*.txt (or delta file) + experiments/shadow_pilot.py if created. Never `git add -A`.
- Untracked .wai/**, cv/ are orchestrator WIP — leave unstaged.
- If the binary or a pair is unreplayable → record it honestly in the delta file (denominator = pairs actually replayed) and say so in the report. No fabrication.

## Exact files
- `results/shadow-pilot-2.txt` (new; per-pair table + delta line)
- `experiments/shadow_pilot.py` (new, only if no committed replay script exists)

## Completion criteria (each must exit 0)
- the replay script (existing or new) runs against the current binary → exit 0
- `grep -c 'delta' results/shadow-pilot-2*.txt` → ≥1 with explicit now-vs-baseline Unknown rates and denominators
- `git status --porcelain` → only the exact files above
- `pytest -q tests/runtime/test_extract.py` → still 35 passed

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 50%.
- Wall-clock budget: 25 min, enforced by orchestrator `timeout`.
- Session name: `subagent:wild-qic:implement` (retry: fresh `-retry` session); log `.wai/projects/wild/runs/wild-qic.impl.log`; report → `.wai/projects/wild/runs/wild-qic.report.md`.

## Evidence contract (report is a claim, not fact)
Final report ≤150 words: fresh Must-gate outputs, per-pair delta table, commit SHAs, any unreplayable pairs. Independent verification follows; contradictions fail the run.
