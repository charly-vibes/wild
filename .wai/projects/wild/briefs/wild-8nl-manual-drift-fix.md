# Brief: wild-8nl — manual/README status-marker drift fix

## Why
External provider evaluations (chatgpt F1, zai, qwen; threads 006/029) concluded "designed, not implemented" from `docs/wild-manual.md` status markers, directly producing mis-evaluations — while README says wild extract/check are implemented and runtime-tested. Delegated to a subagent: mechanical docs reconciliation; the lead orchestrates only (epic-orchestrator run 1/6).

## Ticket
- **ID:** wild-8nl (claimed, P2, complexity:s, lane:afk) — `bd show wild-8nl`
- **Desired outcome:** manual status markers reflect reality ([prototype]/[implemented] on implemented paths, no misleading "[designed]"); README spec counts and run-notes match the repo.

## Task
1. RED first: run the Must-gate commands below, capture failing output.
2. `docs/wild-manual.md`: fix the status paragraph at line ~5 ("intended interface" → states what is implemented: wild extract/check shipped as prototype, runtime-tested) and relabel section markers — implemented paths get `[prototype]` or `[implemented]`, genuinely not-built sections may keep `[designed]`. Verify actual implementation status per section before relabeling (check src/ + README claims; `cargo build` output names the binary if unsure). Do NOT invent claims of completeness.
3. `README.md`: "Nine specodelic specs" → ten (wild-evaluate was added); remove the stale "Last run: nine files" note (or update to current reality — check `ls openspec/specs | wc -l`).
4. GREEN: re-run Must gates, all pass.
5. No refactor step (docs-only); keep prose minimal and factual.

## HARD CONSTRAINTS
- Docs-only: do NOT touch src/, tests, specs, or CI files.
- Do NOT close the bd ticket (orchestrator ships).
- Do NOT push.
- Pre-existing untracked dirs (.wai/projects/wild/runs/, cv/) are orchestrator WIP — leave unstaged.

## Exact files
- `docs/wild-manual.md`
- `README.md`

## Completion criteria (each must exit 0)
- `grep -F '[designed]' docs/wild-manual.md | wc -l` → 0 matches on implemented paths (report any intentionally-remaining ones with justification)
- README spec count matches: `ls openspec/specs | wc -l` (expect 10)
- `grep -F 'nine files' README.md` → no matches
- `git status --porcelain` shows no modifications beyond docs/wild-manual.md + README.md

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 50% (200K window → ≤100K).
- Wall-clock budget: 20 min, enforced by orchestrator `timeout`.
- Session name: `subagent:wild-8nl:implement` — spawn dir-anchored; log streams to `.wai/projects/wild/runs/wild-8nl.impl.log`.
- Final report: ≤150 words — markers relabeled (which sections, what evidence of implementation status), README fixes, commits made, Must-gate outputs pasted.

## Evidence contract (report is a claim, not fact)
Your final message must cite: the exact Must-gate command outputs (fresh), and the commit SHAs you created. The orchestrator will spawn an independent verifier; contradictions fail the run.
