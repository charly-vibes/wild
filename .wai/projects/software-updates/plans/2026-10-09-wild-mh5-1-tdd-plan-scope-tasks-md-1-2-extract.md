---
tags: [pipeline-run:tdd-ro5-2026-10-09-wild-mh5-1-extract-rust-contracts-local-1-schema-canonical-reader-extract-path, pipeline-step:plan]
---

wild-mh5.1 TDD plan (scope: tasks.md 1-2 + extraction portion of 4; check/harness belongs to mh5.2+).

DESIRED BEHAVIOR
- wild extract --request extraction.json --output facts/: pinned rust-cargo-local-1 extractor inventories supplied Rust/Cargo bundles without executing project code; emits local-1 records (v1 canonical JSON): extraction request, contract facts (modules, public free fns, unit/bool/i8-i16-i32/u8-u16-u32 signatures), demand records (direct dep-qualified calls + explicit non-glob aliases), provenance (separate report; semantic hashes format/location-invariant, raw digests/provenance location-sensitive), completeness/gaps (unsupported constructs -> incomplete-demand + unsupported-construct diagnostics, never a complete claim).
- Slot ids = hash(crate identity + qualified path). Deterministic: identical inputs -> identical semantic bytes.
- Refusals: duplicate keys, unknown fields/versions, digest mismatch, references escaping the supplied bundle, changed build inputs (features/target/toolchain/deps) vs request commitment -> input-mismatch; exit mapping accept->0, reject/unknown->1 (refuse), malformed/orchestration error->2 (refuse). Zero source writes, zero network.

OUT OF SCOPE
- wild check / obligations / law execution (mh5.2, mh5.3), harness (task 5), scenario registration (task 6/mh5.5), incremental cache.

TEST CASES (red-first tests/runtime/test_extract.py)
1. 3-run byte identity: same fixture extracted thrice -> identical canonical semantic contract bytes.
2. Relocation + reformat fixture: semantic bytes identical, raw input identities + provenance distinct.
3. Macro-generated export: reports construct + incomplete inventory, refuses complete contract (unsupported-construct + incomplete-demand diagnostics).
4. Changed feature selection vs prior report: input binding fails, fresh extraction required (input-mismatch).
5. Duplicate key / unknown field / unknown version / digest mismatch / out-of-bundle reference in local-1 records: refused with exit 2.
6. Exit mapping: supported fixture accept->0; gap-bearing extraction -> unknown exit 1 refuse envelope.
7. Demand records: direct dep-qualified call + explicit non-glob alias resolve to provider slots; unsupported usage mechanisms (macro/returned-object/function-pointer) disclosed as gaps without dropping direct demand.

NARROW: pytest -q tests/runtime/test_extract.py
FULL: JUST_TEMPDIR=/tmp just ci && openspec validate --all --strict --no-interactive; overlay meter: ah check --changes add-local-contract-checking

FILES
Cargo.toml, Cargo.lock (pinned syn 2.0.119 + proc-macro2 span-locations), src/{main,lib,formats,extract}.rs, schemas/wild-local-v1.schema.json, docs/wild-local-v1.md, tests/runtime/test_extract.py. New source files open with Purpose/Responsibilities/Rationale headers. Do not touch: .wai/projects/semantic-composition/, testaruda.toml, cv/.
