# Brief: wild-5gb — unikernel-parameterized CD sim variant

## Why
Delegation rationale: wild-5gb is a bounded, fully-specified simulation slice (extend one
stdlib-only seeded Python script → run → record results), mechanically executable from the
design rulings below. The lead orchestrator must stay free to verify and ship rather than
carry implementation context, and the epic wild-wsz has two further children (wild-m8c,
wild-3yy) to orchestrate after this one. No Rust, no openspec, no schema changes — pure
prototype/ + results/ + one smoke test.

## Ticket
- **ID**: wild-5gb (P2, claimed in this run; bd in_progress)
- **Desired outcome**: `prototype/wild_cd_sim.py` gains a unikernel parameterization with
  four scenario arms comparable to the existing A/B/C/C2 outputs, a recorded results file,
  and an explicit hypothesis verdict isolating the value of data-plane floor logic.

## Design rulings (PRE-APPROVED by lead session — implement as stated)
- **D1 — additive, not destructive**: extend `wild_cd_sim.py` with new scenario functions;
  the existing classic-CD outputs (A, B, C, C2, D sections) stay byte-stable with the same
  seeds. Stdlib only, seeded like the rest (`random.Random(seed)` with stated seeds). New
  sections labelled E (rolling overlap, unikernel boot/roll times), F (deploy order under
  checked lockstep vs derived order vs baseline), G (pipeline with build-farm contention),
  H (sensitivity: data-plane floor logic on/off, hybrid fraction axis).
- **D2 — unikernel timing parameters**: boot/roll near-zero — image boot ~0.2 min
  (ASSUMED, Firecracker-class ~125 ms documented startup, stated in a module-level
  PARAMS dict with comments), roll window shrinks accordingly; `gated` staging replaced by
  parallel image builds contending on a build-farm resource pool (back pressure moves from
  the shared staging queue to the farm — model with a simple shared-capacity queue like the
  existing `free` variable, but K farm slots, K=4 ASSUMED).
- **D3 — data-plane concentration**: failure surface concentrated in storage-plane floors.
  In the wild arm, per-incident impact uses the data-plane assumptions; implement the
  "floors removed" arm by zeroing the pre-merge rejection benefit of floors only in the
  data-plane dimension, so the residual difference isolates floors' value. Print the
  residual explicitly (e.g. `floors_residual` line).
- **D4 — hybrid axis**: fleet fraction unikernelized (0.0, 0.5, 1.0). In hybrid fleets the
  floor ordering does NOT collapse — the unikernel subfleet uses checked lockstep, the rest
  keeps derived ordering; model as a weighted mix of the F arms.
- **D5 — hypothesis verdict**: after the sensitivity runs, print a one-line verdict
  stating whether the measured numbers support the review-corrected hypothesis: lead-time
  gap narrows, and removing data-plane floor logic erases most of wild's remaining
  impact-minutes advantage. The verdict cites the printed numbers; it is output, not a
  separate prose file.
- **D6 — results recording**: save the full run output to `results/unikernel-cd-sim-2026-10-14.txt`
  and reference it from the README table row (if results/ has an index) — results/ holds
  saved outputs of the simulation scripts.
- **D7 — smoke test, red-first**: extend `tests/test_prototype_smoke.py` with a test
  importing the new scenario functions and asserting they run deterministically (two calls,
  identical dict output) and complete under the existing smoke budget. Prove it red first
  (import error before the change), then green.

## Red/green/refactor sequence
1. **Red**: add the smoke test for the new scenario functions; run
   `python3 -m pytest tests/test_prototype_smoke.py -q` — new test fails (RED). Paste the
   red output in the report.
2. **Green**: implement D1–D6 in `prototype/wild_cd_sim.py`; the new test passes; existing
   smoke tests stay green; `python3 prototype/wild_cd_sim.py` exit 0 with the new sections
   after the existing ones; two consecutive full runs byte-identical.
3. **Refactor**: none expected; keep the flat function style of the file (no classes).

## Exact files
- `prototype/wild_cd_sim.py` (new scenario functions + PARAMS + main additions)
- `tests/test_prototype_smoke.py` (one new test appended)
- `results/unikernel-cd-sim-2026-10-14.txt` (new)
- `.wai/projects/unikernel-cd/runs/wild-5gb.report.md` (implementor report)

## Completion criteria (exit 0 = done)
- `python3 -m pytest tests/test_prototype_smoke.py -q` → all pass, including the new test
  (proven red-first: paste the red run output in the report)
- `python3 prototype/wild_cd_sim.py` → exit 0; sections A–D unchanged in shape; sections
  E–H present; `floors_residual` line printed; hypothesis verdict line printed
- two consecutive runs byte-identical (paste diff-empty proof, e.g. `cmp` exit 0)
- `cp` the run output to `results/unikernel-cd-sim-2026-10-14.txt`
- atomic commits: test commit (red), then feat commit (green), then results commit; never
  `git add .beads`; do not touch anything outside the exact files above
- do NOT push — the lead ships

## Out of scope
- wild-m8c (composition certificate) and wild-3yy (functor pilot) — separate runs
- any change to `prototype/wild_sim.py`, `wild_proto.py`, `wild_cat_sim.py`
- openspec/spec changes, docs/, README edits beyond none (research-only ticket)

## Follow-up threshold
If modeling the build farm or hybrid mix needs machinery beyond simple queues (e.g. a
discrete-event framework import), STOP, commit what is green, and file the finding to bd
— do not expand the slice.

## Spawn model
- Implementor session name: `subagent:wild-5gb`
- Model: session default (`z-ai/glm-5.3-flash` via openrouter) — same family as lead;
  acceptable for a mechanical, fully-ruling-specified slice
- Context ceiling: ≤ 60% of the model window, computed at spawn
- Wall-clock budget: `timeout 3600` around the spawn; background + log + poll, never
  blind-blocking
- Log: `.wai/projects/unikernel-cd/runs/wild-5gb.spawn.log`
- Report: `.wai/projects/unikernel-cd/runs/wild-5gb.report.md`
- Verifier evidence contract (wai-px4g): the verify session's review artifact must cite
  the artifacts it read and include fresh test-run output (actual command + result pasted)
  before recording CONFIRM — otherwise REVIEW_REQUIRED
