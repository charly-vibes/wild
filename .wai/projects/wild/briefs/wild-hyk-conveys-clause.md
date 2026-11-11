# Brief: wild-hyk — conveys clause for well-behaved conveyance

## Why
Pass-through components (proxies, pipes, middleware) route input they never interpret, but wild currently refuses them for unextracted demand — honest conveyance is indistinguishable from silent dropping. Delegated to a subagent: bounded spec+src+test implementation per an already-approved openspec proposal; the lead orchestrates only (epic-orchestrator run, hickey pair 1/2).

## Ticket
- **ID:** wild-hyk (claimed, P2) — `bd show wild-hyk`
- **Proposal (read first):** `openspec/changes/add-conveys-clause/` — proposal.md, delta specs/wild-compose/spec.md, tasks.md. Design constraints come from research lesson 8 (`.wai/projects/semantic-composition/research/2026-10-21-lessons-from-hickey-in-context-clojure-conj.md`, "lesson 8", lines ~74-88): select + excess = all; claim scoped to declared paths; NEVER an exemption from validation.

## Task (TDD — red, green, then gates; refactor only if needed)
1. RED: write failing contract tests FIRST, following the pattern of `tests/runtime/test_direct_update.py::test_new_provider_dependency_is_not_hidden_by_demand_restriction` (closest existing analogue — read it). Three tests:
   a. `test_conveyed_slot_is_claimed_not_rejected` — contract declares a `conveys` clause over a path; extraction of an unknown input slot at that path yields a scoped conveyance claim, NOT a demand refusal.
   b. `test_undeclared_unknown_slot_is_still_refused` — same slot without clause coverage → current refusal preserved.
   c. `test_conveyed_path_new_required_input_still_caught` — scoped substitution whose replacement introduces a new required input under a conveyed path still refuses and lists it (scoped_substitution unchanged).
2. GREEN: implement.
   - Parse `conveys` (list of input paths) in the v1 contract format: `src/formats.rs`, `docs/wild-formats-v1.md`, `schemas/wild-v1.schema.json`.
   - Extraction/check: declared-path unknown slots → scoped conveyance claim instead of demand refusal (`src/extract.rs`, `src/extract/`, `src/check.rs`). Follow existing claim/verdict structures — do not invent a new verdict class.
3. Deploy the spec delta to `openspec/specs/wild-compose/spec.md` (specodelic format — mimic existing rows exactly):
   - Constraints table row: `| conveys_forwarding_scoped | invariant | `a contract may declare a conveys clause listing input paths that are forwarded not interpreted; extraction of a demanded slot at a declared path records a conveyance claim scoped to those paths instead of refusing for unextracted demand, and the claim never exempts scoped_substitution — restricting demand still never hides newly introduced required inputs` | [[wild.compose]] |`
   - Properties rows (derives_from [[wild.compose.conveys_forwarding_scoped]]): `conveyed_slot_claimed_not_rejected` (unit, generator `passthrough_contract_with_conveys_paths()`, predicate `slot at declared path → claim ∧ no demand refusal`) and `conveyed_path_new_required_input_still_caught` (unit, generator `replacement_introducing_required_input_under_conveyed_path()`, predicate `refusal lists new required input`)
   - Mirrored `### Requirement: Conveyance forwards uninterpreted input` under `## Requirements` with the three acceptance cases from the delta (match the corpus's `#### Acceptance case:` style used by sibling requirements).
4. Contract TOML: `.espectacular/wild-compose/conveyed-slot-is-claimed-not-rejected.toml` — copy the shape of `.espectacular/wild-compose/new-provider-dependency-is-not-hidden-by-demand-restriction.toml` (id/description/archetype/status/authored_with + [tests] pytest entries → your new test node ids).
5. Tick tasks.md items 2.x/3.x as done.

## HARD CONSTRAINTS
- scoped_substitution semantics MUST NOT change — test (c) is the guard. If your implementation weakens it, stop and record the conflict.
- Do NOT close the bd ticket; do NOT push; do NOT archive the openspec change (lead does that at ship).
- Do NOT touch: experiments/, results/, .beads/, other capabilities' specs.
- Never `git add -A`. Commit ONLY: openspec/changes/add-conveys-clause/** (already staged separately by lead — leave committed state alone), openspec/specs/wild-compose/spec.md, src/**, tests/**, docs/wild-formats-v1.md, schemas/wild-v1.schema.json, .espectacular/wild-compose/<new>.toml, openspec/changes/add-conveys-clause/tasks.md.
- Commit sequence: (1) red tests, (2) green impl + spec + TOML. No fabricated test output anywhere.
- Untracked .wai/**, cv/ are orchestrator WIP — leave unstaged.

## Completion criteria (each must exit 0)
- `uv run --with pytest pytest tests/runtime/ -q` → all pass including the 3 new tests (red proven first: paste the failing output in the report before the green commit)
- `spk lint openspec/specs` → clean
- `openspec validate add-conveys-clause --strict` → valid
- `ah check --run-tests` → 0 findings
- `just ci` → green
- `git status --porcelain` → only the exact files above

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 50%.
- Wall-clock budget: 45 min, enforced by orchestrator `timeout` (background + poll, never bare blocking).
- Session name: `subagent:wild-hyk:implement` (retry: fresh `-retry` session); log `.wai/projects/wild/runs/wild-hyk.impl.log`; report → `.wai/projects/wild/runs/wild-hyk.report.md`.

## Evidence contract (report is a claim, not fact)
Final report ≤150 words: red-first evidence (failing output), the 3 gate outputs pasted fresh, commit SHAs, files touched, any conflicts with scoped_substitution. Independent verification follows; contradictions fail the run.
