## 1. Red — conformance fixtures (bd wild-m7f.3, red phase)
- [ ] 1.1 Add failing tests to `tests/runtime/test_extract.py` per the design test shape: (a) `println!` alongside a direct provider call yields no `incomplete-demand` from the std macro and the provider call still resolves; (b) `assert_eq!(a(), b())` records demands for a and b like direct calls; (c) a nested macro inside a whitelisted macro's arguments retains `incomplete-demand`; (d) a non-whitelisted expression macro (e.g. `vec![]`) retains `incomplete-demand`; (e) a whitelisted head whose tokens do not parse as a comma-separated expression list (e.g. `println!(a; b)`) retains `incomplete-demand`
- [ ] 1.2 Confirm the new tests fail for the right reason (gaps emitted by today's `visit_expr_macro`) and the existing determinism/invariance gates still pass

## 2. Green — extractor semantics (bd wild-m7f.3, green phase)
- [ ] 2.1 Implement the closed whitelist (const slice) and the comma-separated expression-list parse + descent in `visit_expr_macro`, with the parse-failure fallback to the existing `incomplete-demand` gap
- [ ] 2.2 All suites green: `pytest tests/runtime/test_extract.py`, then the full gate (`just ci` or the project's standard run)

## 3. Held-out re-run (bd wild-m7f.4)
- [ ] 3.1 Re-run the held-out comparison with `experiments/heldout_eval.py` split/dev-select/seal/compare/report machinery unchanged, against the committed corpus and oracle — beginning with an explicit `heldout_eval.py freeze` re-freeze (required: `cmd_compare` refuses on freeze drift with the new wild binary digest) that rewrites the committed `freeze/freeze.json`; disclose the rewrite
- [ ] 3.2 Record the coverage/unknown-rate deltas for the wild arm in `experiments/heldout/README.md` and the refreshed `report.md`/`compare.json`; disclose that the extension (not a fixture rewrite) moved the numbers

## 4. Tidy (bd wild-m7f.5, refactor while green)
- [ ] 4.1 In a separate commit, refactor the macro-support code for clarity (whitelist table, helper decomposition) with all tests still green

## 5. Validation and archive
- [ ] 5.1 `openspec validate add-std-macro-demand-support --strict`; `spk lint openspec`; `ah check`
- [ ] 5.2 On archive: mirror the modified requirement into the dual-format `openspec/specs/wild-extract/spec.md` Requirements section and confirm `linter.requirement_drift` stays satisfied
