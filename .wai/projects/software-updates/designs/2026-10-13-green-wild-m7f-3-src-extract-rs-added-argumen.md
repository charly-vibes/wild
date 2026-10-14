---
tags: [pipeline-run:tdd-ro5-2026-10-13-wild-m7f-std-macro-demand-support, pipeline-step:green]
---

GREEN (wild-m7f.3): src/extract.rs — added ARGUMENT_CONFINED_STD_MACROS const (15 macros), ArgumentExprList newtype (Punctuated<Expr, Comma> via Parse impl; syn's Punctuated lacks Parse), shared handle_invocation_macro (whitelist -> parse_body -> descend each arg via visit_expr; parse failure or unlisted head -> incomplete-demand gap), visit_expr_macro delegates, NEW visit_stmt_macro override (statement-position invocations were silently skipped pre-change), and the Visit impl made lifetime-polymorphic impl<'a,'b> Visit<'b> for SourceWalk<'a> so owned parsed args can be walked (nodes no longer pinned to the file's borrow lifetime). Meters: pytest tests/runtime/test_extract.py 17/17 (5 reds -> green), full pytest tests/ 239 passed, JUST_TEMPDIR=/tmp just ci exit 0 (NOT CALIBRATED advisory benign), openspec strict 11/11, ah check 0 issues, spk lint 0 issues.
