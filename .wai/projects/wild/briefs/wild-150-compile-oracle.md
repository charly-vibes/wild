# Brief: wild-150 — compile oracle for the genesis/specodelic Rust experiment

## Why
RESULTS.md:15 carries "Not done: a compile oracle" — the value proposition (false-break/missed-break rates) hangs on the 17 disputed transitions with no compile evidence. Ranked #1 cheapest decisive step by independent evaluations (mistral/grok thread 006, chatgpt F3 thread 029). Delegated to a subagent: self-contained experiment coding; the lead orchestrates only (epic-orchestrator run 2/6).

## Ticket
- **ID:** wild-150 (claimed, P2, m, afk) — `bd show wild-150`
- **Environment fact (verified by lead, overrides the ticket's constraint note):** local cargo/rustc 1.98.1 ≥ 1.85 — edition 2024 compiles LOCALLY. Do not stall on toolchain provisioning.

## Desired outcome
Every one of the 17 disputed genesis transitions (RESULTS.md §1: 14 Cargo-incompatible-but-accretion + 3 Cargo-compatible-but-break over all 120 pairs) has a recorded compile verdict (pass/fail + toolchain version) in `experiments/RESULTS.md` §1; the "Not done: a compile oracle" caveat is deleted.

## Approach
1. RED first: the Must gates below currently fail — capture that.
2. Data acquisition: fetch genesis-vibes crate sources 0.2.0–0.12.0 (16 versions). Try `curl https://static.crates.io/crates/genesis-vibes/genesis-vibes-<ver>.crate -o` then untar (GET works even if HEAD 403s). Fallback: `cargo download`-style via a scratch cargo project with `cargo fetch` + `~/.cargo/registry` extraction. Consumer: specodelic sources at its 6 tags v0.1.0–v0.5.0 — local repo `/var/home/sasha/para/areas/dev/gh/charly/specodelic` (git worktree per tag: `git worktree add /tmp/spk-<tag> <tag>`; READ-ONLY on that repo — no branches/commits there).
3. Oracle script `experiments/compile_oracle.sh` (or .py driving cargo): for each of the 17 disputed (provider_from → provider_to) transitions × the consumer tag that uses that provider (see RESULTS.md demand lines), attempt `cargo check` (or `cargo build`) of consumer against each provider endpoint; verdict = compiles / fails(+first error class). Pin and record `cargo --version` + `rustc --version` in output. Keep scratch under /tmp; commit ONLY the script + RESULTS.md edits (+ small verdicts artifact if needed, e.g. `experiments/compile_oracle_results.txt`).
4. SEMANTICS (do not invent): compile verdict per transition = does the consumer at its pinned demand still compile against provider_to (missed-break probe: compiles ⇒ break missed or contract right) and against provider_from (control). Record denominators (which consumer tags apply per transition). Where a transition has NO consumer demand line, record the compile matrix of the raw pair (from/to on a minimal consumer derived from the demand slots) or mark N/A with reason — honesty over completeness; an honest partial matrix beats fabricated totals.
5. GREEN: RESULTS.md §1 gets a new "Compile oracle" block: per-transition verdict table (transition | consumer tag | provider pair | verdict | toolchain), the caveat line DELETED, denominators explicit. The ticket's Meter (CI matrix): add `.github/workflows/compile-oracle.yml` running the script on ubuntu-latest (toolchain: dtolnay/rust-toolchain@stable or setup with 1.85+ pin) uploading verdicts as artifact — local run is the recorded evidence; CI reproduction is a follow-up (do NOT wait for a CI run to finish).
6. No refactor step. Pre-registration anti-goal (from ticket family): decide the 17 transitions + method BEFORE looking at compile outcomes — they are already enumerated in RESULTS.md §1; do NOT add/remove transitions after seeing results.

## HARD CONSTRAINTS
- Do NOT touch the specodelic repo (read-only worktrees), src/, tests/, specs/, .beads/.
- Do NOT close the bd ticket; do NOT push.
- Commit ONLY: experiments/compile_oracle*.{sh,py,txt}, experiments/RESULTS.md, .github/workflows/compile-oracle.yml. Never `git add -A`.
- Untracked .wai/projects/**, cv/, .wai/pipeline-runs/** are orchestrator WIP — leave unstaged.
- If crates.io is unreachable → record the blocker honestly, commit nothing fake, write the report as BLOCKED with evidence (curl output). Do not fabricate verdicts.

## Exact files
- `experiments/RESULTS.md` (§1 edit: verdicts + delete caveat)
- `experiments/compile_oracle.sh` or `.py` (new) + `experiments/compile_oracle_results.txt` (new)
- `.github/workflows/compile-oracle.yml` (new)

## Completion criteria (each must exit 0)
- `bash experiments/compile_oracle.sh` (or py equivalent) → exit 0, prints per-transition verdict table incl. toolchain versions
- `grep -c 'Not done: a compile oracle' experiments/RESULTS.md` → 0
- `git status --porcelain` → only the exact files above modified/added
- `python3 -m pytest -q tests/runtime/test_extract.py 2>/dev/null || pytest -q tests/runtime/test_extract.py` → still 35 passed (docs+experiments change must not break runtime suite)

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 55% of its 1M window.
- Wall-clock budget: 55 min, enforced by orchestrator `timeout`.
- Session name: `subagent:wild-150:implement` (retry: `-retry` suffix, fresh session).
- Log: `.wai/projects/wild/runs/wild-150.impl.log`; report lands at `.wai/projects/wild/runs/wild-150.report.md`.

## Evidence contract (report is a claim, not fact)
Final report ≤200 words with: fresh Must-gate outputs pasted (incl. toolchain versions), the verdict table (or BLOCKED evidence), commit SHAs. Independent verification follows; contradictions fail the run.
