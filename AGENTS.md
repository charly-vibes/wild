<!-- PODRAS:START -->
## podras

- Run `podras brief --json` first; it is the machine-readable status contract.
- Check freshness before inference: stale or missing sources are warnings, not facts.
- Beads owns issue lifecycle; focus is intent, not permission.
- Never silently change focus or unpark an item; ask the human and use the verbs.
- Never hand-edit committed renders; regenerate them with `podras brief --write`.
- Roadmap `later`/`shaping`/`deferred` items are not requirements; no-gos are hard constraints.
- Never edit `.podras/roadmap.toml`; admission, deferral and kill are human decisions.

<!-- provenance: generator=podras version=0.13.2 source=PODRAS sha=1ace28e8 -->
<!-- PODRAS:END -->

<!-- SPECODELIC:START -->
## Specodelic — spec format rules (managed block)

This repo's `specs/`-style markdown spec files (YAML frontmatter +
fixed-schema tables) are linted by `spk` (crates.io: specodelic).
Write specs so `spk lint` passes; embedded format revision: specodelic.md Revision 22

### Lint rules (every violation names its `rule_id`)

- `linter.frontmatter_valid` — frontmatter `kind` must be `intent` — the only top-level intent kind
- `linter.id_matches_file` — frontmatter `id` must equal the filename stem with `-` mapped to `.` (`_` is literal); a `spec.md` file derives its expected id from its parent directory (Revision 18)
- `linter.unique_id` — every row id in a file must be unique across all of the file's tables
- `linter.guard_required` — every transition must carry a non-null guard (a guard may be prose, or cite an invariant Constraint or a State — target typing is `ref_kind_compatible`'s beat)
- `linter.model_present` — the Model section must contain both a States list and a Transitions table
- `linter.ears_syntax` — the intent statement must contain an imperative `SHALL` and match one of the five EARS patterns
- `linter.no_conjoined_id` — an id must not encode two capabilities joined by `and`/`or`
- `linter.no_universal_in_id` — an id must not contain a universal token (all/every/any/always/never)
- `linter.total_refs` — every structured-field [[link]] must resolve to a definition somewhere in the corpus (Revision 18: all files resolve corpus-wide — the former `id: spec` self-containment retired)
- `linter.ref_kind_compatible` — every resolved [[link]] in a Reference Typing field must target a kind-compatible row — read from the Schema-as-data table, not hardcoded per field; dangling targets stay `total_refs`' beat, from/to stays `every_transition_valid`'s (openspec/specs/linter-referential_integrity/spec.md)
- `linter.coverage` — every constraint must have a deriving property (`∃ property.derives_from == <constraint>`)
- `linter.no_orphan_property` — every property must derive from at least one constraint
- `linter.law_cases` — every law-kind property must enumerate its required cases as **name:** labels in its own predicate — the identity and associativity floor is mandatory, extra named cases are checkable declarations
- `linter.terminal_states_emit` — every failure terminal state must emit exactly one file-owned effect Constraint — a mute failure terminal is a finding (openspec/specs/linter-failure_shape/spec.md; timed_out/exploration_only are the stated v1 non-goal)
- `linter.error_labels_unique` — within one file, no two error Constraints may share a variant head — the label is file-id-namespaced (errors.md error_expr_shape), so collisions are a per-file property
- `linter.guard_negation_total` — every failure transition must cite exactly the union of its success siblings' citation sets, or be on the recorded carve-out list (orchestrate.md's stage-fail transitions) — a zero-citation failure guard off the list is a finding
- `linter.every_state_used` — every declared state must appear as from or to in at least one transition — a state no transition reaches is machinery the model can never enter or leave
- `linter.every_transition_valid` — every transition's from and to must name states declared in the same file's States section
- `linter.no_self_ref` — a row must not reference itself via traces_to or derives_from — a self-tracing row has no owning purpose
- `linter.acyclic` — the directed graph formed by constraint-traces_to ∪ property-derives_from ∪ guard-as-edge must contain no cycle (derives_from edges are property-sourced — the Reference Typing Appears-on column is normative, so a Constraint-row derives_from is typing's beat, never an edge)
- `linter.single_root_reachable` — every constraint/property/state/transition row must reach its file's OWN intent row through own-file primary linkage (traces_to/derives_from chains resolved within the file, plus the model's own from/to/guard/emits edges) — cross-file typed edges (guard citations of foreign constraints, satisfies, observes) are outbound leaves, never reachability paths; tiered: cross-file-only rows warn (advisory, exit 0), rows with no path to ANY intent hard-fail
- `linter.observability` — every effect Constraint must be the target of ≥1 `observes` reference from a different row — advisory: warned on the warnings channel (exit 0), never a failure
- `linter.checklist_well_formed` — a declared checklist manifest (`*.checklist.md`) must be a flat item list with stable ids plus a mapping table with exactly item/status/mapped_ids/rationale columns — a manifest the linter cannot read is a checklist going silently unconsulted
- `linter.every_item_accounted` — every checklist item must have exactly one mapping row with status `covered` or `waived` — an unconsulted item is the failure this checker exists to prevent
- `linter.covered_maps_resolve` — a `covered` mapping row must name a non-empty mapped_ids list whose ids resolve to real constraint or property rows — a claim resting on nothing is not a claim
- `linter.waiver_has_rationale` — a `waived` mapping row must carry non-empty rationale prose — an unexplained waiver is an unconsulted item with extra steps
- `linter.no_duplicate_claim` — no two mapping rows may target the same checklist item — one claim per item, on the record
- `linter.constraint_kind_closed` — every Constraint row's kind must be in {invariant, advisory, effect, extension_point} — an unreadable kind cell is outside the closed set (openspec/specs/linter-schema_shape/spec.md)
- `linter.property_kind_closed` — every Property row's kind must be in {unit, law} — an unreadable kind cell is outside the closed set (openspec/specs/linter-schema_shape/spec.md)
- `linter.row_shape_closed` — every Constraint/Property/State/Transition row's field set must be exactly the base fields its kind declares plus the typed reference columns the Reference Typing table declares — an undeclared column is a finding; the reference columns are read from the Schema-as-data, never a hardcoded list (openspec/specs/kinds/spec.md constraint_row_shape / state_row_shape / transition_row_shape / property_row_shape)
- `linter.pack_shape` — a kind: profile pack file's manifest must carry all six facet tables (Sections/Kinds/References/Checkers/Floors/Requires) with well-formed two-column rows, its Kinds rows must be pack-qualified (never a base closed-set name — the narrowing rejection), and manifest tables may not appear on non-profile files (openspec/specs/packs/spec.md, Revision 14)
- `linter.orphan_vocabulary` — orphan vocabulary is a labeled failure naming the candidate pack and both remediations (enable/declare the pack, or fix the vocabulary) — a declared uses edge targeting an id no discovered kind: profile pack carries, or a pack-qualified token used in a kind/field position with no discovered pack in its namespace (candidate prefix-derived when only the namespace is known) (openspec/specs/packs/spec.md, Revision 14)
- `linter.skew_advisory` — a declared pack's Requires base pin older than the workspace corpus revision is a warnings-channel advisory naming the pack's base pin and the corpus revision — never silent, never failing (openspec/specs/packs/spec.md, Revision 14)
- `linter.schema_matches_typing_table` — when the lint target carries the format doc, its Reference Typing table must equal the Schema value row for row — the document and the code cannot drift; a corpus without the format doc is out of the gate's scope (no-op, never fabricated expected rows) (add-acset-core, linter-schema_shape family)
- `linter.placeholder_content` — a structured content cell must not be an untouched scaffold: its whole trimmed text is TODO/TBD/FIXME (optionally with a separator and a note), a row id begins with `scaffold_` in a file that still carries the scaffold signature (its intent statement is a placeholder, or a constraint expr / property predicate is a placeholder or a tautology), or the intent statement is a placeholder (`THE system SHALL …` or a placeholder word) — never a substring scan inside a `**rust:**` fragment; the real producers are the `spk new` stub/TODO cells and `spk migrate`'s `scaffold_constraint`/`scaffold_transition`/`scaffold_property` sidecar rows; advisory — warned on the warnings channel (exit 0), never a failure (openspec/specs/linter-content_advisories/spec.md)
- `linter.tautological_predicate` — a property predicate or invariant constraint expr must not be trivially true: its whole trimmed text is `true`/`⊤`, or one identifier is compared equal to itself (`x == x`) — no calls, arithmetic, or compound expressions are judged, and an `effect`/`advisory` constraint expr is never judged; advisory — warned on the warnings channel (exit 0), never a failure (openspec/specs/linter-content_advisories/spec.md)
- `linter.fragment_binds_nothing` — an invariant constraint expr or a unit property predicate that carries a `**rust:**` fragment must cite at least one declared model element — a Model state or transition id, or a Constraint/Property row id of at least 3 characters (the intent id is not a model element; one-/two-character ids never satisfy the identifier check) — a fragment citing none is green yet vacuous: nothing was checked; citation is a textual proxy: string/char literals and `//` line comments are stripped for identifier coincidence, EXCEPT that a whole unescaped string literal whose content exactly equals a declared Model/States id IS a citation (an invariant comparing the `state` binder against a declared state is genuinely bound; literal equality is length-independent, and an UNDECLARED state literal never binds — that is `vacuous_invariant`'s surface), and a fragment containing a path-qualified `::` call is exempt (it invokes production code); a declared element that is simply never exercised is never flagged (citation-versus-declared-ids, never coverage-of-declared-ids); law-kind predicates are outside the surface; the finding is FILE-SCOPED: one summary warning per file names the count and every offending row id; advisory — warned on the warnings channel (exit 0), never a failure (openspec/specs/linter-content_advisories/spec.md, specodelic-h5ks)
- `linter.vacuous_invariant` — an invariant constraint's `**rust:**` expr that forbids a state literal (`state != "<state>"`, or its mirror, with the binder named exactly `state` — `model.state`/`state.field`/`crate::state` are not judged) must name a state declared in `Model/States`; `//` line comments are skipped, so a commented-out comparison never warns — an undeclared forbidden state cannot exist, so the invariant is structurally vacuous; a DECLARED but unreachable phase state never warns, because a legitimate phase-style model may keep a defensive invariant over a phase its correct runs never enter (citation-versus-declared-ids, never reachability from any seed state — never a nudge off good design pressure); advisory — warned on the warnings channel (exit 0), never a failure (openspec/specs/linter-content_advisories/spec.md, specodelic-h5ks)

### Commands

- `spk lint <dir>` — check the invariants (fails with a hint on zero files)
- `spk graph <dir>` — typed reference graph (state edges, typing
  violations, supersedes cycles; blast-radius lands later)
- `spk compile <files>` — emit TOML / proptest / TLA+ artifacts
- `spk model-check <files>` — run the model checker against compiled
  output (stateright; reports land as `*.check.json`)
- `spk explain [topic]` — the embedded format primer (works offline)
- `spk doctor` — diagnose workspace + block currency
- `spk feedback bug --dry-run` — file an issue against upstream

Refresh this block after upgrading: `spk init --force`.
<!-- SPECODELIC:END -->

<!-- BEADS:START -->
<!-- BEGIN BEADS INTEGRATION v:1 profile:minimal hash:ca08a54f -->
## Beads Issue Tracker

This project uses **bd (beads)** for issue tracking. Run `bd prime` to see full workflow context and commands.

### Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --claim  # Claim work
bd close <id>         # Complete work
```

### Rules

- Use `bd` for ALL task tracking — do NOT use TodoWrite, TaskCreate, or markdown TODO lists
- Run `bd prime` for detailed command reference and session close protocol
- Use `bd remember` for persistent knowledge — do NOT use MEMORY.md files

## Session Completion

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY.
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session
<!-- END BEADS INTEGRATION -->
<!-- BEADS:END -->

<!-- ah:managed:start -->
## espectacular

Run `ah check` to verify spec-test correspondence before committing.

- `ah check` — validate all deployed specs
- `ah check --changes <name>` — validate with a change overlay
- `ah init` — set up or refresh espectacular project files
- `ah doctor` — diagnose setup issues
- `ah explain <topic>` — playbook guidance for finding kinds and suggested actions
- `ah doctor --enable <adapter>` — write adapter config into .espectacular/config.toml
- `ah signals` — emit dont drift signals
<!-- ah:managed:end -->

<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

## Test runner (DDL standard — recorded in the dulce-de-leche repo)

- **TDD loop**: agents run `just test` (testaruda exec loop, working diff)
  instead of `cargo test` directly — it selects the affected test set,
  runs only those tests, and ingests results for future selection.
  Tolerance contract: exit 0/10/20 green; stale store self-heals
  (wild-z56). `just test-blast` previews the affected set without running
  anything.
- **Full suite**: `just test-full` is the plain cargo test run. The push
  gate is `just testaruda-gate` (base/head comparison, what lefthook/CI
  run); selection is for fast feedback, never a gate substitute.