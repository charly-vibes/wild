# Brief: wild-58c — false-break census on a large real crate release history

## Why
Mistral evaluation experiment #4: the extract+check pipeline has never been run across a large real crate's public API history — opaque share and false-break rate of the current extractors at scale are unknown. Complements the scaled held-out corpus (wild-zfw, landed). Delegated: self-contained census engineering; the lead orchestrates only (epic-orchestrator run 5/6).

## Ticket
- **ID:** wild-58c (claimed, P3, m, afk) — `bd show wild-58c`

## Desired outcome (Must)
ONE crate with >=300 public slots replayed across its FULL release history; opaque-share and false-break rate recorded PER RELEASE with explicit denominators. Meter: census script output committed under experiments/.

## Task
1. RED first: no census artifact exists under experiments/ — capture.
2. PRE-REGISTER: choose the crate (suggest `serde` or `clap` — long history, large public surface, real-world relevance) and commit the choice + full sorted version list + slot-count methodology BEFORE grading any transition. The pre-registration commit is what makes the census auditable; do not reorder.
3. Census mechanics (`experiments/census.py` + output `experiments/census_results.txt`):
   - Fetch all release versions (crates.io API; cache .crate tarballs under /tmp/wild-58c-scratch/, see hygiene rules).
   - Per version: count public slots (the wild extract path — `cargo run -q --release -- extract <src>` or the experiments tree-sitter path; record which + the binary commit).
   - Consecutive transitions: classify contract verdict (accretion / break / opaque share = fraction of slots Unknown) AND Cargo caret verdict (compatible/incompatible).
   - False-break rate = transitions where the contract pipeline says break but Cargo says compatible AND no documented/digestible break evidence exists — with the numerator AND denominator explicit. Opaque share = Unknown slots / total slots, per release.
   - Record toolchain + binary provenance in the output header (same discipline as experiments/compile_oracle_results.txt).
4. RESULTS.md gets a short census section (or pointer paragraph) with headline numbers + denominators.
5. Honest partial is valid: if API limits/toolchain gaps truncate the history, record exactly how many versions were replayed and why. BLOCKED (e.g., crates.io unreachable) with evidence is a valid terminal state.

## HARD CONSTRAINTS
- Pre-registration before grading; no post-hoc crate/version swaps.
- Scratch hygiene: /tmp quota ~19G/25.4G. ALL scratch under /tmp/wild-58c-scratch (env-overridable), `df -h /tmp` per batch, delete extracted tarballs after slot-count per version. Errno 122 → clean, retry once, then honest BLOCKED with df output. Never scratch into the repo.
- Do NOT touch src/, tests/, specs/, docs/, .beads/, other experiments' committed artifacts (heldout/ stays untouched).
- Do NOT close the bd ticket; do NOT push.
- Commit ONLY: experiments/census.py, experiments/census_results.txt, experiments/RESULTS.md (census section). Never `git add -A`; leave .wai/**, cv/ unstaged.

## Exact files
- `experiments/census.py` (new)
- `experiments/census_results.txt` (new; per-release table + headline denominators)
- `experiments/RESULTS.md` (census paragraph)

## Completion criteria (each must exit 0)
- `python3 experiments/census.py` → exit 0 (replay at least the committed version list)
- slot count of the chosen crate >= 300 (recorded in census_results.txt header)
- `grep -c 'denominator' experiments/census_results.txt` → >=1; opaque-share and false-break lines present with numerators+denominators
- `pytest -q tests/runtime/test_extract.py` → still 35 passed
- `git status --porcelain` → only the exact files above

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 55%.
- Wall-clock budget: 70 min, enforced by orchestrator `timeout`. Approaching budget with honest partials → commit partial + say so.
- Session name: `subagent:wild-58c:implement` (retry: fresh `-retry` session); log `.wai/projects/wild/runs/wild-58c.impl.log`; report → `.wai/projects/wild/runs/wild-58c.report.md`.

## Evidence contract (report is a claim, not fact)
Final report ≤200 words: fresh Must-gate outputs (crate chosen, version count, slot count, opaque share, false-break rate with denominators), commit SHAs, honest gaps. Independent verification follows; contradictions fail the run.
