# Brief: wild-adc — on_absent: fallible (absence as policy)

## Why
A required input slot makes absence a caller violation, but "the outside world lacked the fact" is not "my program is broken" — consumers need a way to declare absence as a handled value outcome. Delegated to a subagent: bounded spec+src+test implementation per an already-approved openspec proposal; the lead orchestrates only (epic-orchestrator run, hickey pair 2/3).

## Ticket
- **ID:** wild-adc (claimed, P2) — `bd show wild-adc`
- **Proposal (read first):** `openspec/changes/add-on-absent-fallible/` — proposal.md, deltas for wild-core + wild-tiers, tasks.md. Design constraints from research lesson 9 (`.wai/projects/semantic-composition/research/2026-10-21-lessons-from-hickey-in-context-clojure-conj.md`, "lesson 9", lines ~89-100): missing is a policy, not a truth.
- **Implementation precedent:** the landed wild-hyk conveys clause is the closest sibling — read `git show 1a66798 --stat` and `src/extract/conveys.rs` for how a contract clause flows through formats → check → claims. Follow that shape.

## Task (TDD — red, green, then gates)
1. RED: write failing contract tests FIRST in `tests/runtime/test_on_absent.py` (mirror `tests/runtime/test_conveys.py` structure):
   a. `test_absent_input_at_fallible_slot_is_handled_outcome` — required input slot declares `on_absent: fallible`; absent input yields a fallible-absence outcome recording the scoped claim, NOT a caller-violation refusal.
   b. `test_absent_input_without_clause_still_refuses` — same slot without the clause → current refusal preserved.
   c. `test_clause_direction_gaining_accretes_losing_breaks` — adding `on_absent: fallible` to a retained input accretes; revoking it is a break.
   d. `test_new_fallible_required_slot_is_still_non_accretion` — a NEW required slot (even fallible) appearing is a non-accretion (accretion_monotone unchanged).
   e. `test_fallible_slot_stays_in_closure_validation` — substitution introducing a new required input near a fallible slot still lists it (closure integrity unchanged).
   f. `test_no_new_static_verdict_kind` — the static verdict kind set is unchanged by the clause; the clause records a scoped claim (tier-1) only; tier-3 observation is DESIGN-ONLY (see below).
2. GREEN: implement.
   - `src/formats.rs`: parse `on_absent` ("fallible") on required input slots; `docs/wild-formats-v1.md` + `schemas/wild-v1.schema.json` document it.
   - `src/check.rs`: fallible-absence outcome + scoped claim instead of caller-violation refusal; refusal preserved without the clause.
   - `src/update.rs` (accretion checker): direction per test (c) and (d) — clause on a RETAINED input accretes; revoking breaks; NEW fallible slots remain non-accretions.
   - Tier-3: NO src surface — wild-tiers is a normative design capability (design acceptance cases, not prototype code). Only the spec row + mirrored requirement land.
3. Deploy spec rows (specodelic format, mimic sibling rows exactly):
   - wild-core Constraints: `| absence_as_policy | invariant | `a required input slot may declare on_absent fallible; the slot stays required in demand and closure validation and its absence is a value outcome the consumer handles instead of a caller violation; adding the clause to a retained input is an accretion and revoking it narrows demand and is a break; a new fallible-required slot is still a new required input` | [[wild.core]] |`
   - wild-core Properties (derives_from [[wild.core.absence_as_policy]]): `fallible_absence_handled_not_refused` (unit, `required_slot_declared_on_absent_fallible()`, `absent input at the slot yields the fallible-absence outcome ∧ no caller-violation refusal`); `absence_clause_direction_is_accretion` (unit, `retained_input_gaining_then_losing_on_absent_fallible()`, `gaining: accretes == true ∧ losing: accretes == false`); `fallible_slot_stays_in_closure` (unit, `substitution_introducing_required_input_near_fallible_slot()`, `closure validation unchanged ∧ new required inputs still listed`)
   - wild-tiers Constraints: `| absence_observed_at_runtime | invariant | `absence at a slot declared on_absent fallible is a tier-3 observation (canary or replayed traffic) recorded as scoped evidence; it is never a new static verdict kind and never overrides structural results` | [[wild.tiers]] |`
   - wild-tiers Properties: `absence_is_observation_not_verdict` (unit, [[wild.tiers.absence_observed_at_runtime]], `canary_observing_absent_input_at_fallible_slot()`, `absence appears as tier-3 evidence ∧ verdict kinds unchanged ∧ structural results unaffected`)
   - Mirrored Requirements: deploy the deltas as `### Requirement: Absence is declared policy, not violation` (wild-core) and `### Requirement: Absence surfaces as runtime observation` (wild-tiers) under each spec's `## Requirements`, with acceptance cases in the corpus's `#### Acceptance case:` style (see how 1a66798 deployed the conveys requirement — per-scenario `#### Scenario:` headers were required by ah; follow the corpus convention that landed there).
4. Tick tasks.md items 2.x/3.x as done.

## HARD CONSTRAINTS
- The slot STAYS required: `on_absent: fallible` changes absence HANDLING, never closure membership. Tests (d)/(e) are the guards — if your implementation weakens accretion_monotone or closure validation, stop and record the conflict.
- NO new static verdict kind; NO src surface for canary/tier-3 (design rows only).
- Do NOT close the bd ticket; do NOT push; do NOT archive the openspec change (lead does that at ship).
- Do NOT touch: experiments/, results/, .beads/, other capabilities' specs.
- Never `git add -A`. Commit ONLY: openspec/changes/add-on-absent-fallible/** (proposal committed by lead — leave its committed state alone), openspec/specs/wild-core/spec.md, openspec/specs/wild-tiers/spec.md, src/**, tests/runtime/test_on_absent.py, docs/wild-formats-v1.md, schemas/wild-v1.schema.json, openspec/changes/add-on-absent-fallible/tasks.md.
- Commit sequence: (1) red tests, (2) green impl + spec rows.
- **Gate claims must be REAL**: paste fresh command output for every gate you claim. A gate output you did not run in this session is fabrication — the previous run's fabricated `just ci` claim was caught and dispositioned; do not repeat it.

## Completion criteria (each must exit 0)
- `uv run --with pytest pytest tests/runtime/test_on_absent.py -q` → 6 passed (red proven first: paste failing output in the report before the green commit)
- `uv run --with pytest pytest tests/runtime/ -q` → all pass (no regressions in conveys/update tests)
- `spk lint openspec/specs` → clean
- `openspec validate add-on-absent-fallible --strict` → valid
- `ah check --run-tests` → 0 findings
- `git status --porcelain` → only the exact files above
- do NOT run `just ci` — it is the lead's ship gate; report your surface gates only

## Spawn model
- Model: openrouter/z-ai/glm-5.3-flash. Context ceiling ≤ 50%.
- Wall-clock budget: 45 min, enforced by orchestrator `timeout` (background + poll, never bare blocking).
- Session name: `subagent:wild-adc:implement` (retry: fresh `-retry` session); log `.wai/projects/wild/runs/wild-adc.impl.log`; report → `.wai/projects/wild/runs/wild-adc.report.md`.

## Evidence contract (report is a claim, not fact)
Final report ≤150 words: red-first evidence (failing output), pasted fresh outputs for each surface gate, commit SHAs, files touched, any conflicts with accretion/closure invariants. The lead runs `just ci` at ship; contradictions fail the run.
