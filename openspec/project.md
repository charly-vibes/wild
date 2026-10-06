# Project Context

## Purpose

**wild** aims for machine-checked compatibility and composition of software
components, modelled as a category of contracts. Compatibility, demand, and
accretion are represented as contracts in a category, so that "can this
version of X compose with that version of Y" becomes a machine-checked
question instead of a semver guess.

**Status.** A design with a prototype, not a finished tool. There is no
`wild` command yet. The manual (`docs/wild-manual.md`) describes the
intended interface and marks what is implemented.

Relation to OpenSpec: openspec manages the engineering change workflow of
this repo. The domain design lives in `openspec/specs/` (nine specodelic
specs: `wild`, `.core`, `.tiers`, `.compose`, `.registry`, `.bridge`,
`.adopt`, `.deploy`, `.extract`) — the design corpus is dogfooded through
specodelic lint/graph. The `superseded/` directory keeps earlier
single-file drafts replaced by the nine-spec layout.

## Tech Stack

- Rust (target tool implementation; nothing implemented yet)
- Python 3.12+ (prototypes and experiments, standard library plus
  `tree-sitter`/`tree-sitter-rust` for `prototype/wild_proto.py`)
- specodelic CLI for the spec corpus (`specodelic lint specs`)

## Project Conventions

### Code Style
- Python: stdlib-first; the prototype sims must stay dependency-free.

### Architecture Patterns
- Design corpus first: normative formats are in `docs/wild-formats-v1.md` and
  `schemas/wild-v1.schema.json`; spec changes land in `openspec/specs/`, verified by
  `specodelic lint` / `specodelic graph` (no dangling references).

### Testing Strategy
- `tests/test_spec_corpus.py` — spec corpus stays lint-clean and
  reference-closed, strict OpenSpec discovery, local design references, and
  shared v1 schema/examples (gated by espectacular).
- `tests/test_prototype_smoke.py` — prototype sims run clean; round-1 outcomes are asserted against declared
  expected rejection, safe-widening, and known escape cases.

### Git Workflow
- Direct commits to `main`; small, focused commits.

## Domain Context

The design model: contracts as objects in a category, compatibility as
morphisms, tiers and accretion for version relations, tombstones for
deprecations. See `docs/wild-manual.md` (start here) and the
integration-failure case files (162 cases) for the evidence base.

## Important Constraints

- The simulations use small synthetic models with assumed parameters —
  they support the model and say nothing about real registries.
- Undeclared behavior is the known weak spot; the design reaches it only
  through laws and evidence.

## External Dependencies

- specodelic (`specodelic`/`spk`) — spec corpus lint and graph
- OpenSpec — change workflow (proposals → tasks → archive)
