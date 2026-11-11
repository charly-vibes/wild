# Brief: wild-zfw — scale held-out corpus to n>=50 multi-ecosystem cases

## Why
The held-out protocol (wild-1xk/wild-f4i) has only 4 adjudicable held-out cases (experiments/RESULTS.md:49). Mistral evaluation ranks a scaled multi-ecosystem corpus (n>=50, same freeze/seal discipline, plus a cargo-semver-checks arm) as the top uncertainty-reducer testing H1+H3 simultaneously. Delegated: self-contained corpus engineering; the lead orchestrates only (epic-orchestrator run 4/6 — heaviest ticket).

## Ticket
- **ID:** wild-zfw (claimed, P2, l, afk) — `bd show wild-zfw`

## Desired outcome (Must)
>=50 adjudicable held-out cases across >=2 ecosystems with freeze/seal digests recorded; aggregate accuracy (previously absent by design) recorded WITH explicit denominators. Meter: `heldout_eval.py compare` run + counts committed.

## Existing machinery (reuse, do not reinvent)
- `experiments/heldout_corpus.py build` → cases.json / oracle.json / excluded.json / case_context.json / checkers.json (read `experiments/heldout/README.md` FIRST — the artifact map + design rulings are the protocol spec).
- `experiments/heldout_eval.py freeze|split|seal|compare|report` — same pipeline, now over the bigger corpus.
- Adapters: `experiments/heldout_adapters/{wild,ci,cargo_semver,ecosystem}.py` — cargo_semver arm already scaffolded; ecosystem.py hints at multi-ecosystem support.
- **Ready second ecosystem:** the §2 python execution-oracle matrix (RESULTS.md §2; experiments/eval_py.py + smoke_flask.py + smoke_requests.py) holds 28 side-by-side flask×werkzeug / requests×urllib3 cells with REAL recorded outcomes (24 pass / 4 fail). Those are adjudicable cases — import them into the corpus format with their real outcomes as oracle verdicts.

## Task
1. RED first: current counts <50 (8 cases, 1 ecosystem) — capture.
2. PRE-REGISTER (anti-goal enforcement): commit the corpus definition + oracle outcomes BEFORE running any wild verdict on new cases. Sequence: build corpus → freeze → seal oracle → commit → THEN compare. The freeze/seal digests make this auditable; do not reorder.
3. Corpus sourcing to reach >=50 adjudicable across >=2 ecosystems:
   - cargo arm: existing e5-derived cases (12 total, 8 adjudicable) + optionally more real cargo pairs IF each new pair gets a real Cargo-replay outcome (never a guessed verdict).
   - python arm: the 28 §2 cells (real install + smoke-test outcomes already recorded).
   - cargo-semver-checks arm as an additional checker on cargo cases (adapter exists).
   - If honest sourcing cannot reach 50 adjudicable: record exactly what was achieved (count + denominators + why the rest are missing) as a partial result. A truthful 40/2-ecosystems beats a fabricated 50. BLOCKED is a valid terminal state.
4. Run freeze → split → seal → compare → report; record aggregate accuracy in report.md WITH per-class denominators (missed breakages / false blocks / true pass / Unknown), keeping the existing separate-metrics sections intact.
5. Commit: corpus + digests + compare.json + report.md + any new adapter glue. RESULTS.md gets a one-paragraph pointer update in the held-out section (new counts + delta vs 4).

## HARD CONSTRAINTS
- Pre-registration: corpus selection + oracle outcomes committed before wild verdicts on new cases. No post-hoc swaps, no cherry-picking; excluded cases keep recorded reasons.
- Scratch hygiene (tickets filed on this): /tmp quota is 18G/25.4G used. Keep ALL scratch under /tmp/wild-zfw-scratch (or env override), `df -h /tmp` before each batch, clean venvs/targets between pairs. On Errno 122: clean scratch, retry ONCE, then stop and report BLOCKED with the df output. Never write scratch into the repo.
- Do NOT touch src/, tests/, specs/, docs/, .beads/, the specodelic repo.
- Do NOT close the bd ticket; do NOT push.
- Commit ONLY: experiments/heldout/**, experiments/heldout_corpus.py, experiments/heldout_eval.py, experiments/heldout_adapters/**, experiments/RESULTS.md (held-out section pointer). Never `git add -A`; leave .wai/**, cv/ unstaged.

## Completion criteria (each must exit 0)
- `python3 experiments/heldout_corpus.py build` (or its committed invocation) → exit 0 with >=50 adjudicable across >=2 ecosystems in cases.json/oracle.json
- `python3 experiments/heldout_eval.py compare` → exit 0, compare.json carries freeze/oracle digests
- `grep -c 'aggregate' experiments/heldout/report.md` → >=1 with denominators
- `pytest -q tests/runtime/test_extract.py` → still 35 passed
- `git status --porcelain` → only the exact file scopes above

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 60%.
- Wall-clock budget: 90 min, enforced by orchestrator `timeout`. If you approach the budget with honest partial results, COMMIT the partial corpus + report as partial and say so — do not rush fabrication.
- Session name: `subagent:wild-zfw:implement` (retry: fresh `-retry` session); log `.wai/projects/wild/runs/wild-zfw.impl.log`; report → `.wai/projects/wild/runs/wild-zfw.report.md`.

## Evidence contract (report is a claim, not fact)
Final report ≤200 words: fresh Must-gate outputs (case counts per ecosystem, freeze/seal digest confirmations, aggregate accuracy with denominators), commit SHAs, honest gaps. Independent verification follows; contradictions fail the run.
