# Change: Add argument-confined std macro demand support to the local extractor

## Why

The `wild-1xk` held-out comparison (`experiments/heldout/report.md`) shows the
wild arm at coverage 0/4 with unknown-rate 1.0: every held-out consumer
invokes `println!`, and `visit_expr_macro` in `src/extract.rs` emits an
`incomplete-demand` gap for every expression macro, so the scoped claim is
refused as Unknown. That is the honest refusal the disclose-every-unsupported-
mechanism law requires — but it is over-broad for std macros whose expansion
provably cannot reference consumer-code functions outside their syntactic
arguments. Extending the extractor's supported set is genuine runtime
semantics (OpenSpec territory per `experiments/heldout/README.md` ruling 1);
it is never a fixture rewrite to manufacture agreement.

## What Changes

- `src/extract.rs`: macro invocations whose head is a whitelisted std macro
  with a closed, argument-confined expansion (`println!`, `print!`, `eprintln!`, `eprint!`,
  `format!`, `panic!`, `assert!`, `assert_eq!`, `assert_ne!`,
  `debug_assert!`, `debug_assert_eq!`, `debug_assert_ne!`, `todo!`,
  `unimplemented!`, `unreachable!`) no longer emit `incomplete-demand`.
  Their token trees are parsed as a comma-separated expression list and
  descended, so demands inside the arguments (e.g. `assert_eq!(a(), b())`)
  are recorded like direct calls. Any macro that fails that parse, or whose
  head is not whitelisted, keeps the existing `incomplete-demand` refusal.
  RED-phase amendment: the rule applies in BOTH expression position
  (`ExprMacro`) and statement position (`StmtMacro`). The incumbent never
  visits statement-position invocations at all (syn parses them as
  `Stmt::Macro`, not `Expr::Macro`) — silently accepted, arguments never
  descended, demands inside never recorded — so a new `visit_stmt_macro`
  override applies the same whitelist/descend/refuse rule there instead of
  leaving a silent-acceptance hole.
- Item-position macros (`visit_item_macro`, e.g. `macro_rules!` definitions
  and `lazy_static!`-style invocations) are unchanged: they can still
  generate declarations the profile cannot inventory and remain refused.
- `tests/runtime/test_extract.py`: red-first conformance fixtures covering
  the supported and refusal shapes.
- `experiments/heldout/`: re-run the comparison with the extended extractor
  using the existing `heldout_eval.py` freeze/seal/compare machinery
  unchanged.

**No breaking change** to the request envelope: the profile id stays
`rust-cargo-local-1` (see design.md decision 1).

## Impact

- Affected specs: `wild-extract` (MODIFIED requirement: Explicit consumer
  demand coverage)
- Affected code: `src/extract.rs` (`visit_expr_macro`), 
  `tests/runtime/test_extract.py`, `experiments/heldout/*` (re-run artifacts)
- Unaffected: `experiments/heldout_eval.py`, the held-out corpus
  (`cases.json`, `checkers.json`, `oracle.json`), the held-out adapter
  (`experiments/heldout_adapters/wild.py`), and the other nine spec
  capabilities
