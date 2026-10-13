# Design: argument-confined std macro demand support

## Context

`rust-cargo-local-1` deliberately refuses every expression macro:
`visit_expr_macro` emits a `complete_killer` `incomplete-demand` gap and does
not descend, so any demand inside the macro's arguments is unrecorded and the
claim is refused with Unknown structural assurance. The `wild-1xk` held-out
run measured the consequence: coverage 0/4, unknown-rate 1.0, because the e5
consumers call `println!`.

The change must widen the supported demand profile without weakening the
disclose-every-unsupported-mechanism law
(`openspec/specs/wild-extract/spec.md`, requirement *Explicit consumer demand
coverage*). The `rust-cargo-local-1` design also states: "Extending this
profile requires new conformance fixtures before broader completeness
claims" — the red-first fixtures in this change are those conformance
fixtures, and the held-out re-run is the broader completeness measurement.

## Goals / Non-Goals

- Goals: a closed, auditable whitelist of std expression macros whose
  expansion provably cannot reference consumer functions outside their
  syntactic arguments; demand recording inside those arguments; conservative
  refusal everywhere else; deterministic, formatting-invariant behavior.
- Non-Goals: general macro support, `macro_rules!` definition expansion,
  item-position macro invocation support, proc-macro or attribute macro
  analysis, trait-dispatching macros (`write!`, `writeln!`, logging crates),
  changes to the request envelope or the held-out machinery.

## Decisions

### Decision 1: Extend `rust-cargo-local-1` in place (no new profile id)

- **Decision:** keep `PROFILE = "rust-cargo-local-1"` and widen the supported
  demand set inside it.
- **Alternatives considered:**
  - *Bump to `rust-cargo-local-2`*: rejected. `experiments/heldout/checkers.json`
    embeds the profile id in the wild checker's command template, and the
    held-out re-run (wild-m7f.4) must reuse `experiments/heldout_eval.py`
    freeze/seal/compare unchanged against the committed corpus and oracle. A
    new profile id would force a corpus rebuild, breaking that constraint.
  - Also: no persisted local-1 extraction artifacts exist that must remain
    reproducible under the old semantics — the extractor artifact digest in
    provenance binds behavior, and this is a prototype pre-release.
- **Rationale:** the profile id names the request envelope contract; the
  extractor digest names the behavior. The report's completeness and gap
  fields still disclose exactly what was and was not supported for every run.

### Decision 2: Closed whitelist of expansion-safe std macros

- **Decision:** only expression macros whose head is in a fixed constant
  list are exempt from `incomplete-demand`. The criterion for membership is
  that the macro's std expansion is a closed definition that evaluates only
  its syntactic arguments and cannot reference consumer-visible functions
  outside them. The list is the std print/format/assert/panic/diverge
  family:
  `println!`, `print!`, `eprintln!`, `eprint!`, `format!`, `panic!`,
  `assert!`, `assert_eq!`, `assert_ne!`, `debug_assert!`,
  `debug_assert_eq!`, `debug_assert_ne!`, `todo!`, `unimplemented!`,
  `unreachable!`.
- **Rationale:** each expansion is a closed std definition that evaluates
  its syntactic arguments and introduces no additional call sites against
  consumer-visible functions. The whitelist is data (a const slice), so a
  reader can audit the exact supported set without tracing control flow.
- **Excluded deliberately:**
  - `write!`/`writeln!` — expansion dispatches `write_fmt`, a trait method
    call on the target expression; the profile refuses returned-object
    method calls, so pretending these are transparent would invent
    completeness.
  - `vec!`, `matches!`, `cfg!`, `concat!`, `include!`, and every non-std
    macro — expansion shape is not provably argument-confined (or requires
    file inclusion / cfg evaluation), so the honest refusal stays.
  - Item-position macros (`visit_item_macro`) — they may generate
    declarations the inventory cannot see; the existing two-gap refusal is
    unchanged.

### Decision 3: Parse token trees as a comma-separated expression list, then descend

- **Decision:** for a whitelisted head, parse `node.mac.tokens` with
  `syn::parse2::<Punctuated<syn::Expr, Token![,]>>>` and run the existing
  walker over each parsed argument expression. Demands inside arguments are
  recorded exactly like direct calls (`record_demand` + `callee_spans`).
- **Fallback:** if the parse fails (e.g. a syntax shape the comma-separated
  grammar cannot represent), emit the existing `incomplete-demand` gap —
  the refusal path is identical to today's behavior. Never guess.
- **Why this is sound:** the format macros' expansion consumes their
  arguments as ordinary expressions, so descending into the parsed argument
  list sees every consumer identifier that participates in demand.
  - Over-approximation note: `todo!`, `unimplemented!`, and `unreachable!`
    never evaluate their arguments, so a call inside them is recorded as
    demand although it can never execute. This is intentionally
    conservative — the profile records syntactic demand, exactly as it
    already does for direct calls in dead branches — and can only produce a
    false block, never a missed breakage.
  - Inline format captures (`println!("{x.field}")`) cannot hide a call:
    per RFC 2795 inline captured fragments admit only identifiers, field
    access, and indexing — method calls and function calls are compile
    errors there. So descending the argument list is sufficient; the string
    literal itself is never scanned as demand.
- **Determinism:** token parsing is span-independent; the walker's semantic
  bytes derive from qualified names, not locations, so formatting and
  checkout-path invariance (the existing
  `test_repeated_extraction_formatting_invariance`-style gate) holds.

### Decision 4: Unknown macro heads keep the current refusal

- **Decision:** `visit_expr_macro` for a non-whitelisted head emits the
  same `incomplete-demand` gap as today. No new diagnostic codes.
- **Rationale:** the disclose-every-unsupported-mechanism law is unchanged;
  only the supported set grows. The held-out unknown-rate can only drop
  through genuine support, never through silent acceptance.

## Risks / Trade-offs

- **Whitelist drift** (a future std version changes an expansion) → the
  whitelist is a single reviewed const; the held-out and conformance
  fixtures pin behavior; report fields still carry per-run gap evidence.
- **Format-argument demands mistaken as complete demand** → no: arguments
  are visited by the same walker that already refuses returned-object
  method calls, function-pointer flows, and non-whitelisted nested macros
  inside the arguments. Nested macro inside a whitelisted macro's arguments
  (e.g. `println!("{}", foo!())`) is refused by the inner `visit_expr_macro`
  — refusal composes.
- **`assert!`/`assert_eq!` with non-expression first argument** (e.g.
  `assert!(matches!(x, P))` — `matches!` is a nested macro, refused; that
  is the honest outcome, not a regression).

## Migration Plan

1. Red: add the failing conformance fixtures (test shape below).
2. Green: implement the whitelist + descent; all suites green.
3. Re-run the held-out comparison with the unchanged machinery; record
   coverage/unknown-rate deltas in `experiments/heldout/README.md` and the
   refreshed `report.md`/`compare.json`. Note: `cmd_compare` verifies the
   committed `freeze/freeze.json` against current tool digests and refuses
   on drift, so the re-run begins with an explicit `heldout_eval.py freeze`
   step that REWRITES the committed freeze artifact (only the wild binary
   digest changes — `heldout_eval.py`, the corpus, the oracle, and the seal
   are untouched); the rewrite is disclosed in the README.
4. Tidy pass in a separate commit while green.
5. Archive: mirror the modified requirement into the dual-format
   `openspec/specs/wild-extract/spec.md` Requirements section
   (`linter.requirement_drift` must stay satisfied; no specodelic-table
   change is needed — the constraints and properties are generic and
   already cover the behavior).

## Test shape (defined before implementation, per the design law)

- **Inputs:** consumer bundles (built with the existing `write_bundle`
  helper) containing, alongside a direct dependency-qualified provider
  call:
  1. a `println!` expression macro;
  2. a whitelisted macro whose arguments reference provider functions
     (`assert_eq!(a(), b())`);
  3. a nested macro inside a whitelisted macro's arguments
     (`println!("{}", foo!())`);
  4. a non-whitelisted expression macro (`vec![...]`);
  5. a whitelisted head whose tokens do not parse as a comma-separated
     expression list (e.g. `println!(a; b)` — syn accepts the macro body as
     raw tokens and extraction never compiles the bundle).
- **Outputs:**
  1. no `incomplete-demand` from the std macro; the provider call still
     resolves to a provider slot; scoped claim not refused for the macro;
  2. demands for `a` and `b` recorded like direct calls;
  3. `incomplete-demand` retained (nested macro refuses);
  4. `incomplete-demand` retained for the non-whitelisted macro;
  5. `incomplete-demand` retained for the unparseable whitelisted head.
- **Invariants checked in the same tests:** repeated extraction of the same
  bundle yields identical contract bytes (determinism gate unchanged); the
  held-out re-run uses `experiments/heldout_eval.py` machinery unchanged.

## Open Questions

- (none)
