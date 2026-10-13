# Brief: wild-7e9 — string types in the rust-cargo-local-1 signature subset

## Why
Delegation rationale: wild-7e9 is a bounded, fully-specified implementation slice (proposal
→ red tests → implement → meters) whose context fits one focused session. The lead
orchestrator is coordinating the remaining epic batch (wild-1gm, wild-f4i, wild-m7f close)
and must stay free to verify and ship rather than carry implementation context. The ticket
is the filed blocker for the epic goal: wild-m7f.4's re-run proved the wild arm's held-out
Unknowns trace to the provider-side signature subset, not the macro surface.

## Ticket
- **ID**: wild-7e9 (P2, claimed in this run; bd in_progress)
- **Desired outcome**: `&str`, `String` (and `&String`, normalized) become supported scalar
  types in the rust-cargo-local-1 profile's signature subset — public fns taking or
  returning text produce genuine function-type slots instead of unsupported-construct
  opaque gaps — under a new OpenSpec change proposal (genuine semantics extension per the
  wild-m7f epic ruling; never a fixture rewrite to manufacture agreement).

## Design rulings (PRE-APPROVED by lead session — implement as stated)
- **D1 — type identity is conservative**: three distinct type identities. `String` →
  scalar name `text-owned`; `&str` and `&String` → scalar name `text-borrowed`. The
  conservative subtype table already Breaks on name mismatch, so owned↔borrowed confusion
  can never yield a false Holds. Both shapes: `{"shape":"scalar","name":...}` with NO
  min/max fields (text is unbounded; mirrors the `boolean` precedent).
- **D2 — normalization**: `&String` maps to `text-borrowed` (deref coercion is standard
  Rust semantics, not a widening). `&mut str`/`&mut String` stay unsupported (mutable
  borrows are outside the v1 value-transfer model → unsupported-construct gap as today).
- **D3 — `str` bare and other text-like types** (`char`, `Cow`, `Vec<u8>`, generic args):
  remain unsupported — gap path, unchanged.
- **D4 — scope**: signature subset only (public free fn args + returns). No changes to
  demand resolution, macro support, or the subtype/accretion checker beyond what D1
  implies (name-equality already handles text scalars; verify with tests, do not edit
  the table unless a test proves a gap).

## Red/green/refactor sequence
1. **Proposal first**: author `openspec/changes/add-string-signature-support/`
   (proposal.md, design.md with D1–D4, tasks.md, spec delta under wild-extract);
   `openspec validate --strict` green BEFORE red tests (repo convention: proposal gates
   implementation; m7f.2 precedent).
2. **Red**: new tests in `tests/runtime/test_extract.py` (mirror
   `test_public_fn_with_non_scalar_return_is_opaque_gap_not_panic` shape): provider with
   `pub fn shout(x: &str) -> String`, `pub fn owned(s: String) -> usize` — assert rc=1
   currently, unsupported-construct gaps, opaque slots (RED). Also contract-shape
   assertions for the green state.
3. **Green**: extend `scalar_type` in `src/extract.rs` — `Type::Reference` handling
   (non-mut, elem `str` or path `String` → `text-borrowed`) and `"String"` path arm →
   `text-owned`. All red tests green; full suite stays green.
4. **Refactor** (separate commit only if needed): none expected; keep the match arms flat
   for the pretender complexity gate.

## Exact files
- `openspec/changes/add-string-signature-support/{proposal,design,tasks}.md`,
  `openspec/changes/add-string-signature-support/specs/wild-extract/spec.md` (delta)
- `src/extract.rs` (scalar_type only)
- `tests/runtime/test_extract.py` (new tests appended to TestExtraction)

## Completion criteria (exit 0 = done)
- `openspec validate --all --strict` → exit 0
- `python3 -m pytest tests/runtime/test_extract.py -q` → all pass, including the new
  string-type tests (proven red-first: paste the red run output in the report)
- `python3 -m pytest tests/runtime -q` → all pass
- `JUST_TEMPDIR=/tmp just ci` → exit 0 (NOT CALIBRATED advisory is benign)
- `cargo test -q` → exit 0
- atomic commits: proposal commit, then feat commit (red→green in one feat commit is
  acceptable per repo convention if the red run is pasted in the report); never
  `git add .beads`; do not touch `testaruda.toml`, `cv/`, `.wai/` lanes other than this
  ticket's state file
- do NOT push — the lead ships

## Out of scope
- wild-1gm (format_args!), wild-f4i (held-out re-run), archiving
  add-std-macro-demand-support (task 5.2), any schema/docs edits beyond the change delta
  (`schemas/` + `docs/` mirrors happen at archive time, mh5.5 precedent)

## Follow-up threshold
If scalar_type's extension ripples beyond signature subset (e.g. demand resolution or
check.rs needs text handling), STOP, commit what is green, and file the finding to bd —
do not expand the slice.
