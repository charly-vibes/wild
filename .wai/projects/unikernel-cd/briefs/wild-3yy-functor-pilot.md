# Brief: wild-3yy — functor-signature extraction pilot on a MirageOS unikernel

## Why
Delegation rationale: wild-3yy is a bounded research-extraction slice (one new extractor
script over a pinned upstream checkout + a red-first smoke test with an embedded fixture +
a results file + one research-artifact paragraph), mechanically executable from the design
rulings below. It is the last open child of epic wild-wsz. No Rust, no openspec, no
changes to existing prototype files.

## Toolchain ruling (lead-approved, resolves the ticket's "pin at claim time")
- **No opam/OCaml compiler install.** The pilot extracts functor signatures from SOURCE
  text — the compiler is not needed. "Pin at claim time" means: record the mirage version
  that mirage-skeleton itself declares (dune-project / opam files / README), not install it.
- Parser: `tree-sitter-ocaml==0.26.0` (verified parsing module bindings, parameters, and
  signatures on this machine, 2026-10-14). Ambient env already carries
  `tree-sitter==0.26.0` and `tree-sitter-rust==0.24.2` (used by `prototype/wild_proto.py`)
  — both currently UNDECLARED in requirements-dev.txt; this slice pins all three
  (required + pinned + explained per the anti-goal). Network access for the clone is
  lead-authorized this session.

## Ticket
- **ID**: wild-3yy (P2, claimed in this run; bd in_progress)
- **Desired outcome**: measured answer, for a real MirageOS example, to "what does the
  OCaml type system give for free at functor boundaries vs what wild's laws/tombstones
  add" — with real numbers in the results file and the research artifact, and honest gap
  disclosure for every construct the extractor does not interpret.

## Design rulings (PRE-APPROVED by lead session — implement as stated)
- **D1 — additive, not destructive**: new `experiments/functor_pilot.py` (imports: stdlib
  + `tree_sitter_ocaml` only). No existing file changes except `requirements-dev.txt`
  (the three pins above, one comment line explaining the pilot) and the research artifact
  paragraph (D6). All prototype scripts stay byte-stable.
- **D2 — corpus acquisition (pinned, reproducible)**: the script clones
  `https://github.com/mirage/mirage-skeleton` shallowly at the pinned commit
  `52abe5aedb1f19f6dd3a18dc9ad81c766f813ebc` (verified reachable at claim time) into
  `~/.cache/wild-functor-pilot/mirage-skeleton` (clone if absent, else reuse and verify
  HEAD == pin). Corpus = the whole checkout's `*.ml`/`*.mli` under `tutorial/` and
  `example/` EXCLUDING any `_build`/vendored dirs. Record in the output header: the
  pinned commit and the mirage version declared by the repo's own files (grep
  `dune-project`, `*.opam`, README — report what is found, honestly, even if only an
  opam constraint like `mirage >= 4.x`).
- **D3 — extractor (gap-disclosing)**: tree-sitter-ocaml walk over each file, extracting:
  (a) `module_type_definition` (name + counts of `value_specification` and type
  declarations inside its signature), (b) functor `module_binding` — parameters with
  their module types and the result module type, (c) module applications
  (`Make (X)` style). **Disclose-every-unsupported-mechanism**: constructs the extractor
  does not interpret — first-class modules, `include module type of`, `with type`
  constraints, `module type of`, signatures it cannot attribute — are COUNTED per file
  as `unsupported_constructs` with a per-kind breakdown and never silently dropped
  (wild's gaps-uncuring law). Sort all iteration (files, names) for determinism.
- **D4 — measurement (the thesis, stated as classification, not fabricated evidence)**:
  per functor boundary map to wild vocabulary: `requires` = parameter module types;
  `provides` = result-signature items. Then report the comparison in three explicit
  sections: (1) WHAT OCAML GIVES FREE — counts of machine-checked signature boundaries,
  and the statement (with the counted evidence) that every signature item is shape-only:
  0 behavioral predicates expressible; (2) WHAT WILD ADDS PER BOUNDARY — classified table
  of the wild_sim vocabulary the signature cannot express: law slots, accretion relation
  (provides grow / requires shrink vs OCaml's any-change-breaks), tombstone eligibility
  (name can never return with different meaning), artifact-bound evidence; (3) the
  honest pilot verdict line citing the printed numbers.
- **D5 — determinism**: fixed walk order; two consecutive full runs byte-identical. If
  any timing is printed, mark it `MEASURED` and exclude from the byte-identity claim
  (style of `wild_cd_sim` bench D) — but prefer printing no timings at all.
- **D6 — results + research update**: save the full run output to
  `results/functor-pilot-2026-10-14.txt`; append one paragraph starting
  `Measured (functor pilot, mirage-skeleton @ <short-sha>, mirage <declared version>):`
  to the MirageOS observation section of
  `.wai/projects/unikernel-cd/research/2026-10-14-unikernel-cd-mapping-wild-deploy-onto-a-compose.md`
  citing the headline numbers (functors, module types, signature items,
  unsupported_constructs, and the verdict).
- **D7 — smoke test, red-first**: extend `tests/test_prototype_smoke.py` with a test that
  embeds a small OCaml fixture INLINE (module type with two value specs + a functor
  taking it, plus one `include module type of` to exercise the gap path), runs the
  extractor's parse/extract function on the fixture STRING, and asserts: functor found
  with correct parameter/result module types, item counts correct,
  `unsupported_constructs` counts the include, and determinism (two calls, identical
  result). Prove it red first (ImportError before the change), paste the red output in
  the report. Keep the test under the existing smoke budget (pure in-memory parse, no
  network).

## Red/green/refactor sequence
1. **Red**: add the smoke test; run `python3 -m pytest tests/test_prototype_smoke.py -q`
   — new test fails (RED). Paste the red output in the report.
2. **Green**: implement D1–D6 in `experiments/functor_pilot.py`; the new test passes;
   existing smoke tests stay green.
3. **Refactor**: none expected; flat function style, no classes.

## Exact files
- `experiments/functor_pilot.py` (new)
- `tests/test_prototype_smoke.py` (one new test appended)
- `requirements-dev.txt` (three pins + one comment line)
- `results/functor-pilot-2026-10-14.txt` (new)
- `.wai/projects/unikernel-cd/research/2026-10-14-unikernel-cd-mapping-wild-deploy-onto-a-compose.md` (one paragraph appended)
- `.wai/projects/unikernel-cd/runs/wild-3yy.report.md` (implementor report)

## Completion criteria (exit 0 = done)
- `python3 -m pytest tests/test_prototype_smoke.py -q` → all pass including the new test
  (proven red-first: paste the red output in the report)
- `python3 experiments/functor_pilot.py` → exit 0; output header carries the pinned
  commit + declared mirage version; per-file and summary counts present;
  `unsupported_constructs` breakdown present; the three D4 sections + verdict line
  printed
- two consecutive full runs byte-identical (`cmp` exit 0, unless a MEASURED line exists —
  then deterministic-portion cmp and disclose)
- `cp` the run output to `results/functor-pilot-2026-10-14.txt`
- atomic commits: test commit (red), feat commit (green), results+research commit; never
  `git add .beads`; do not touch anything outside the exact files above
- do NOT push — the lead ships

## Out of scope
- any opam/OCaml compiler install or unikernel build; README/docs edits beyond the one
  research paragraph; changes to `prototype/*`, `openspec/`, `schemas/`; functor
  extraction for non-MirageOS corpora; signing/registry work.

## Follow-up threshold
If the tree-sitter-ocaml grammar cannot reliably attribute functor parameters or result
module types on the real corpus (not just the fixture), or the declared mirage version
cannot be located in the checkout, STOP, commit what is green, and file the finding to
bd — do not expand the slice or improvise a hand-rolled OCaml parser.

## Spawn model
- Implementor session name: `subagent:wild-3yy`
- Model: session default — same family as lead; acceptable for a mechanical,
  fully-ruling-specified slice
- Context ceiling: ≤ 60% of the model window, computed at spawn
- Wall-clock budget: `timeout 3600` around the spawn; background + log + poll, never
  blind-blocking
- Log: `.wai/projects/unikernel-cd/runs/wild-3yy.spawn.log`
- Report: `.wai/projects/unikernel-cd/runs/wild-3yy.report.md`
- Verifier evidence contract (wai-px4g): the verify step's review artifact must cite the
  artifacts it read and include fresh test-run output (actual command + result pasted)
  before recording CONFIRM — otherwise REVIEW_REQUIRED
