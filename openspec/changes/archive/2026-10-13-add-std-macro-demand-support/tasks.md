## 1. Red — conformance fixtures (bd wild-m7f.3, red phase)
- [x] 1.1 Add failing tests to `tests/runtime/test_extract.py` per the design test shape (RED-phase amendment: statement position via `visit_stmt_macro` is the default under test — the incumbent silently skips it): (a) statement `println!` alongside a direct provider call yields no `incomplete-demand` and the provider call still resolves; (b) statement `assert_eq!(provider::add_one(1), provider::greet(2))` with no other calls records both demands like direct calls; (c) expression `format!` with a provider call in args records the demand; (d) a nested macro inside a whitelisted macro's arguments retains `incomplete-demand`; (e) a statement-position non-whitelisted macro (`vec![1, 2];`) retains `incomplete-demand`; (f) an expression-position non-whitelisted macro (`let v = vec![1, 2];`) retains `incomplete-demand`; (g) a whitelisted head whose tokens do not parse as a comma-separated expression list (`println!(a; b);`) retains `incomplete-demand`
- [x] 1.2 Confirmed reds are for the right reason (missing statement-position visit — silent acceptance, not the old over-broad gap) and the existing determinism/invariance gates still pass. Bundles avoid non-scalar public fn returns (wild-73j panic bug, out of scope)

## 2. Green — extractor semantics (bd wild-m7f.3, green phase)
- [x] 2.1 Implemented the closed whitelist (const slice) + `ArgumentExprList` comma-separated parse + descent in the shared `handle_invocation_macro` helper, wired into `visit_expr_macro` AND the new `visit_stmt_macro` (statement-position silent-skip hole, design decision 3a), with the parse-fallback refusal. `Visit` impl made lifetime-polymorphic (`impl<'a,'b> Visit<'b> for SourceWalk<'a>`) so owned parsed args can be walked
- [x] 2.2 All suites green: pytest tests/runtime/test_extract.py 17/17, full pytest tests/ 239 passed, JUST_TEMPDIR=/tmp just ci exit 0, openspec strict 11/11, ah check 0 issues, spk lint 0 issues

## 3. Held-out re-run (bd wild-m7f.4)
- [x] 3.1 Re-run the held-out comparison with `experiments/heldout_eval.py` split/dev-select/seal/compare/report machinery unchanged, against the committed corpus and oracle — beginning with an explicit `heldout_eval.py freeze` re-freeze (required: `cmd_compare` refuses on freeze drift with the new wild binary digest) that rewrites the committed `freeze/freeze.json`; disclose the rewrite
- [x] 3.2 Record the coverage/unknown-rate deltas for the wild arm in `experiments/heldout/README.md` and the refreshed `report.md`/`compare.json`; disclose that the extension (not a fixture rewrite) moved the numbers

## 4. Tidy (bd wild-m7f.5, refactor while green)
- [x] 4.1 Tidy applied during the same green cycle (disclosed as one commit): refusal paths decomposed into `refuse_invocation` helper, early-return shape for the unlisted-head branch; whitelist already a const table; all suites stayed green. NOTE: held-out re-run (3) deliberately ordered AFTER tidy so the freeze binds the final binary digest

## 5. Validation and archive
- [x] 5.1 `openspec validate add-std-macro-demand-support --strict`; `spk lint openspec`; `ah check`
- [ ] 5.2 On archive: mirror the modified requirement into the dual-format `openspec/specs/wild-extract/spec.md` Requirements section and confirm `linter.requirement_drift` stays satisfied
