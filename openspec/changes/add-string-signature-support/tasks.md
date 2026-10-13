# Tasks: add-string-signature-support

## 1. Proposal (gates implementation)
- [x] 1.1 Author proposal.md, design.md (D1–D4), tasks.md, and the wild-extract spec delta; `openspec validate --strict` green before any red test

## 2. Red — signature-subset conformance fixtures
- [x] 2.1 Add tests to `tests/runtime/test_extract.py` (TestExtraction): (a) text-taking public fns (`&str` arg + `String` return, `String` arg, `&String` arg) extract with rc=0, complete inventory, and function-type slots carrying `text-borrowed`/`text-owned` scalars; (b) `&mut str` keeps the unsupported-construct refusal with an opaque slot
- [x] 2.2 Confirm reds are for the right reason (unsupported-construct gaps from the missing text arms, not a bundle or panic defect) and the existing suites still pass

## 3. Green — scalar_type extension
- [x] 3.1 Extend `scalar_type` in `src/extract.rs`: `Type::Reference` arm (non-mut, elem `str` or `String` → `text-borrowed`; mutable → None) and `"String"` path arm → `text-owned`; flat match arms for the pretender complexity gate
- [x] 3.2 All suites green: `pytest tests/runtime/test_extract.py`, `pytest tests/runtime`, `cargo test -q`, `JUST_TEMPDIR=/tmp just ci`

## 4. Validation
- [x] 4.1 `openspec validate --all --strict` exit 0; `spk lint openspec` clean
- [ ] 4.2 On archive: mirror the modified requirement into `openspec/specs/wild-extract/spec.md` and extend the `schemas/wild-v1.schema.json` scalar-name enum (`text-owned`, `text-borrowed`) + `docs/wild-formats-v1.md` (mh5.5 precedent)
