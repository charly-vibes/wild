---
tags: [pipeline-run:tdd-ro5-2026-10-09-wild-mh5-1-extract-rust-contracts-local-1-schema-canonical-reader-extract-path, pipeline-step:quality-ledger]
---

QUALITY LEDGER: wild-mh5.1 extract Rust contracts.

Changed:
- Cargo.toml + Cargo.lock (new): wild crate; syn pinned =2.0.119 (full/visit/extra-traits) + proc-macro2 span-locations + quote + toml 0.9 + sha2 0.10, exact versions locked — deps required by this slice, pinned and explained per design review (vampiro-rust-frontend parser mirror).
- src/formats.rs (new): strict v1 JSON parser (dup-key, float, out-of-range, leading-zero, BOM, control-char, surrogate refusals), canonical writer per docs/wild-formats-v1.md, sha256 digest helpers, unit tests of the canonical examples.
- src/extract.rs (new): local-1 request validation (field whitelist, kind/version/profile, bundle confinement, raw-digest binding), immutable bundle loading, syn walk producing v1 contract slots (function shapes for supported public free fns, opaque fingerprints for other pub decls), position-independent alias pre-pass, demand records bound to provider slot ids (crate name+version+qualified path, never line numbers), explicit uncuring gaps (unsupported-construct, incomplete-demand incl. unsupplied providers), provenance with locations.
- src/main.rs (new): wild extract CLI; v1 envelope on stdout; report/contract/demand/provenance written only to the requested output dir; exit accept 0 / refuse 1 / error 2.
- schemas/wild-local-v1.schema.json + schemas/examples-local.json (new): local-1 record tables (extraction-request, extraction-report, demand, provenance), draft 2020-12.
- docs/wild-local-v1.md (new): protocol doc — records, refusals, exit mapping, slice scope.
- tests/runtime/test_extract.py (new): 12 red-first command-level tests.

Verified:
- pytest -q tests/runtime/test_extract.py: 12/12 green (multiple runs).
- cargo test -q: 2/2 green (canonical byte-for-byte examples + refusal cases).
- openspec validate --all --strict --no-interactive: 12/12.
- jsonschema Draft202012: local schema + 4 examples + real extraction records + emitted v1 contract all valid.

Review:
- RO5U pass: no criticals, converged; H1/H2/H3 + M1-M3 fixed, L2 (O(n^2) dup-key scan at record scale) tracked as accepted.

Risks:
- Profile breadth is deliberately narrow (design-acknowledged abstention on real libraries; E1 measures it).
- Item-level mod file resolution unresolved -> gap; acceptable for slice scope.
- Envelope population for extract is minimal-but-schema-valid; wild check command (mh5.2) will pin fuller envelope fields.

Next:
- Record the quality gates: JUST_TEMPDIR=/tmp just ci, ah check --changes add-local-contract-checking; then commit + bd update, wild-mh5.2 next in dept order.
