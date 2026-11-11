# Brief: wild-pe1 — dynamic-language arm: JS/Python metaprogramming extraction coverage

## Why
Mistral evaluation experiment #5: does honesty-refusal degrade to impracticality on metaprogramming-heavy dynamic code, or does Unknown-with-diagnostics stay useful? An INCONCLUSIVE outcome is a valid pre-registered result (scope-narrowing signal) — recent evidence (wild-58c: wild binary 100% opaque on serde's macro_rules!/glob surface) already points that way; this ticket measures the Python/JS arm properly. Delegated: self-contained fixture matrix; the lead orchestrates only (epic-orchestrator run 6/6 — final).

## Ticket
- **ID:** wild-pe1 (claimed, P3, m, afk) — `bd show wild-pe1`

## Desired outcome (Must)
>=10 metaprogramming-heavy fixtures; per-fixture Unknown rate AND diagnostic usefulness recorded; an overall inconclusive outcome recorded as scope-narrowing signal. Meter: fixture matrix + rates table committed.

## Task
1. RED first: no fixture matrix exists — capture.
2. PRE-REGISTER: commit the fixture list (>=10, metaprogramming-heavy) + the diagnostic-usefulness rubric BEFORE running any extraction. Suggested fixtures (mix real + constructed, justify each): Python — decorators with dynamic dispatch (`functools.wraps` chains), `__getattr__`/`__dir__` module tricks, metaclass-built classes (`type()` calls), monkey-patched module attrs, `exec`-built APIs, descriptor protocol; JS — Proxy traps, monkey-patched exports, CommonJS dynamic `require`, getter/setter object sprawl. Each fixture = small self-contained module with a KNOWN conventional public surface (documented in the fixture header) so refusal-vs-usefulness is adjudicable.
3. Matrix mechanics (`experiments/dynamic_arm.py` + `experiments/dynamic_arm_results.txt`):
   - Run the wild extract path per fixture (Python extractor exists in the prototype tree-sitter path — see experiments/census.py + experiments/wild_proto for the established invocation; JS arm: if no JS extractor exists in the prototype, that IS the finding — record JS as unsupported-extractor with per-fixture N/A and keep the Python arm as the measured arm; do NOT build a new extractor).
   - Per fixture: slots inventoried, Unknown/known split, refusal reason codes (e.g. unsupported-construct, incomplete-demand), and diagnostic usefulness graded against the rubric (e.g. 0=none, 1=names the mechanism, 2=names mechanism + locus). Rates table with numerators+denominators.
   - Verdict per ticket: useful (Unknown-with-diagnostics stays informative), impractical (refusal rate makes coverage useless), or inconclusive — all three valid; record which + evidence.
4. RESULTS.md gets a short dynamic-arm paragraph (or pointer) with the verdict + headline rates.
5. Honest partial/BLOCKED (toolchain/env gaps) with evidence is valid; no fabrication.

## HARD CONSTRAINTS
- Pre-registration before any extraction run; fixture list frozen at commit time.
- Do NOT build/modify extractors — measurement only. JS without an extractor = recorded finding, not a blocker to work around.
- Scratch under /tmp/wild-pe1-scratch with df checks (quota near-full; Errno 122 → clean, retry once, honest BLOCKED).
- Do NOT touch src/, tests/, specs/, docs/, .beads/, experiments/heldout/**, experiments/census*.
- Do NOT close the bd ticket; do NOT push.
- Commit ONLY: experiments/dynamic_arm.py, experiments/dynamic_arm_results.txt, experiments/RESULTS.md (arm paragraph). Never `git add -A`; leave .wai/**, cv/ unstaged.

## Exact files
- `experiments/dynamic_arm.py` (new)
- `experiments/dynamic_arm_results.txt` (new)
- `experiments/RESULTS.md` (arm paragraph)

## Completion criteria (each must exit 0)
- `python3 experiments/dynamic_arm.py` → exit 0
- fixture count >=10 recorded in dynamic_arm_results.txt header
- `grep -c 'denominator' experiments/dynamic_arm_results.txt` → >=1; per-fixture Unknown rate + usefulness grades present
- verdict line present (useful / impractical / inconclusive + one-sentence evidence)
- `pytest -q tests/runtime/test_extract.py` → still 35 passed
- `git status --porcelain` → only the exact files above

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 55%.
- Wall-clock budget: 60 min, enforced by orchestrator `timeout`.
- Session name: `subagent:wild-pe1:implement` (retry: fresh `-retry` session); log `.wai/projects/wild/runs/wild-pe1.impl.log`; report → `.wai/projects/wild/runs/wild-pe1.report.md`.

## Evidence contract (report is a claim, not fact)
Final report ≤200 words: fresh Must-gate outputs (fixture count, per-fixture Unknown rates, usefulness grades, verdict), commit SHAs, honest gaps. Independent verification follows; contradictions fail the run.
