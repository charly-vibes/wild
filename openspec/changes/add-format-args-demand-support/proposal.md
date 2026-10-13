# Change: Add format_args! demand support with format-capture disclosure

## Why

The `add-std-macro-demand-support` design (Decision 2) deliberately excluded
`format_args!` from the argument-confined whitelist to avoid exceeding that
proposal's approved semantics, and tracked it as a follow-up with its own
conformance fixture (review finding RO5U M1; bd wild-1gm). The seam is real:
`format_args!` is the expansion core of the whole print/format family, yet it
is the one argument-confined std macro absent from an otherwise closed,
auditable list.

Authoring this change also surfaced a genuine silent-acceptance hole in the
shipped whitelist that this change closes: implicit format-string captures
(since Rust 2021, `println!("max={MAX}")` captures the identifier named
`MAX` from scope) are walker-invisible. The token trees of a whitelisted
macro are just a string literal plus argument expressions, so a capture
that names a provider value item — a const or static, directly or through
an alias (`use provider::MAX as LIMIT;` + `format_args!("{LIMIT}")`) —
records no demand and emits no gap: a scoped claim passes while the
consumer secretly reads a provider value. Fn items cannot be captured (they
implement no formatting traits — compiler-refused in the probe), and
fn-pointer flow via path expressions is already disclosed by the walker, so
value items are precisely the hole. That violates the
disclose-every-unsupported-mechanism law
(`openspec/specs/wild-extract/spec.md`, requirement *Explicit consumer demand
coverage*) the whitelist exists to serve.

This is whitelist-coherence and honesty work, not held-out coverage work:
the e5 cohort (post-wild-7e9 re-run, wild-f4i) contains no `format_args!`
use and no format captures of provider items, so no verdict is expected to
move. The re-run in this change is verification of that prediction, not a
fixture rewrite.

## What Changes

- `src/extract.rs`: the whitelist constant `ARGUMENT_CONFINED_STD_MACROS`
  gains `format_args`. Its expansion is `core::fmt::Arguments::new_v1` — a
  closed std definition whose demand surface is its syntactic argument
  expressions — so the existing `ArgumentExprList` parse-and-descend rule
  applies unchanged. The named-argument form
  (`format_args!("{x} then {x}", x = expr)`) does not parse as a
  comma-separated expression list (a `name = expr` binding is not an
  `Expr`) and keeps the existing `incomplete-demand` fallback — verified by
  a compile/run probe; the fallback also protects the
  provider-call-inside-named-argument case.
- `src/extract.rs` (family-wide, not format_args-specific): implicit
  format-string captures are cross-checked. For a whitelisted invocation,
  capture identifiers parsed from the format string literals are checked
  against the provider item names and consumer-side aliases known to the
  extractor (alias-named captures disclosed in the walk; leaf-name matches
  checked at demand-resolution time against the recorded slot meanings);
  a capture that names a provider value item — directly or through an
  alias — emits the existing `incomplete-demand` gap instead of being
  silently accepted. Captures of plain locals stay demand-inert:
  locals are not provider demand, and the profile has never recorded demand
  for bare local references.
- `tests/runtime/test_extract.py`: red-first conformance fixtures for the
  supported and refusal shapes below.
- `experiments/heldout/`: re-run the comparison with the extended extractor
  using the existing `heldout_eval.py` freeze/seal/compare machinery
  unchanged, with a disclosed prediction of byte-identical verdicts; any
  movement is a finding to investigate, never silently accepted.

**No breaking change** to the request envelope: the profile id stays
`rust-cargo-local-1` (same rationale as add-std-macro-demand-support design
decision 1).

## Impact

- Affected specs: `wild-extract` (MODIFIED requirement: Explicit consumer
  demand coverage — superset delta carrying the
  add-std-macro-demand-support scenarios verbatim plus four new ones)
- Affected code: `src/extract.rs` (whitelist const + capture cross-check),
  `tests/runtime/test_extract.py`, `experiments/heldout/*` (re-run artifacts)
- Unaffected: the held-out machinery (`experiments/heldout_eval.py`), the
  corpus (`cases.json`, `checkers.json`, `oracle.json`), the wild adapter,
  the request envelope, and the other nine spec capabilities
- Archive ordering constraint: this change MUST be archived AFTER
  `add-std-macro-demand-support` (both modify the same requirement; the
  deltas are supersets, so later-archive-wins with the full scenario set is
  safe only in that order)