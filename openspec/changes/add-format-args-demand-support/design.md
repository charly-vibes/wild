# Design: format_args! demand support with format-capture disclosure

## Context

`ARGUMENT_CONFINED_STD_MACROS` (src/extract.rs:35) admits a closed list of
std expression macros whose expansion provably cannot reference
consumer-visible functions outside their syntactic arguments.
`format_args!` was excluded from the originating change to keep its approved
semantics; RO5U M1 and bd wild-1gm track it as this follow-up. While
authoring this change, a family-wide hole surfaced: implicit format-string
captures are invisible to the token-tree walker, so a whitelisted macro can
silently accept a consumer that captures a provider item by name.

## Goals / Non-Goals

- Goals: `format_args!` joins the whitelist under the same criterion and the
  same parse-and-descend rule; implicit format captures that name provider
  items are disclosed as `incomplete-demand` instead of silently accepted;
  conservative refusal everywhere else; deterministic, formatting-invariant
  behavior; red-first conformance fixtures.
- Non-Goals: general format-string semantics (alignment/width/fill specs are
  not analyzed); capture-name cross-check against anything other than
  provider item names known to the extractor; item-position macros
  (unchanged two-gap refusal); `write!`/`writeln!` (trait dispatch,
  still excluded); held-out machinery changes; envelope changes.

## Decisions

### Decision 1: Extend `rust-cargo-local-1` in place (no new profile id)

- **Decision:** keep `PROFILE = "rust-cargo-local-1"`; widen the supported
  demand set inside it.
- **Rationale:** identical to add-std-macro-demand-support decision 1 —
  `experiments/heldout/checkers.json` embeds the profile id in the wild
  checker's command template, so the re-run must reuse the machinery
  unchanged; the extractor artifact digest in provenance binds behavior, and
  this is a prototype pre-release.

### Decision 2: `format_args` joins the whitelist — the criterion holds

- **Decision:** add `"format_args"` to `ARGUMENT_CONFINED_STD_MACROS`.
- **Criterion argument:** the expansion of `format_args!` is
  `core::fmt::Arguments::new_v1(pieces, args)` — a closed std definition
  that introduces no call sites against consumer-visible functions. Its
  demand surface is exactly the syntactic argument expressions, the same
  proof shape as `format!`.
- **Routed consumers are already covered:** the canonical use
  `writer.write_fmt(format_args!(...))` is an ordinary method call on a
  known binding (`writer`); the expression walker visits it independently of
  the macro arm. The macro's result is a value that borrows its arguments;
  borrow/temporary semantics are not demand semantics, and the profile
  tracks calls and paths, not borrows.
- **Evidence:** compile/run probe (`rustc --edition 2021`) confirmed both
  the positional form (`out.write_fmt(format_args!("v={} plus {}", x, x + 1))`)
  and the routed form compile and execute as described.

### Decision 3: Parse token trees as a comma-separated expression list, then descend — named-argument values included

- **Decision:** for a whitelisted head, parse `node.mac.tokens` with
  `syn::parse2::<Punctuated<syn::Expr, Token![,]>>>` and run the existing
  walker over each parsed argument expression. Demands inside arguments are
  recorded exactly like direct calls (`record_demand` + `callee_spans`).
- **Named-argument values are argument expressions (corrected by probe):**
  `x = expr` parses as `syn::Expr::Assign`, so the named-argument form
  (`format_args!("{x} then {x}", x = provider::add_one(1))`) parses
  successfully and the descent records the demand inside the named value
  like a direct call — the expansion consumes named values as ordinary
  argument expressions, so refusing them would invent incompleteness. The
  RO5U-passed claim that `name = expr` is not an `Expr` was wrong; the
  parse handles it.
- **Fallback:** if the parse fails (e.g. a syntax shape the comma-separated
  grammar cannot represent, like `println!(a; b)`), emit the existing
  `incomplete-demand` gap — the refusal path is identical to the shipped
  behavior. Never guess.

### Decision 4: Implicit format captures naming provider items are disclosed (family-wide)

- **Decision:** for a whitelisted invocation, parse the format string
  literals for implicit capture identifiers (`{name}` and `{name:spec}` —
  the capture is the leading ident inside the brace; the scan skips `{{`/`}}`
  escape pairs and digit-only positional placeholders like `{0}`, which
  reference arguments, not variables) and check each against the provider
  item names AND the consumer-side aliases the extractor already records.
  A match emits the existing `incomplete-demand` gap. This applies to every
  whitelisted macro, not just `format_args!` — the hole exists in the
  shipped whitelist today.
- **Phase:** alias-named captures are disclosed in the walk (the per-member
  pre-pass `alias_map` is walk state; a capture ident whose alias target's
  head is a declared dependency is an unconditional provider-item
  reference). Leaf-name matches are checked at demand-resolution time,
  against the recorded slot meanings — the same provider-item name set
  `check_demand_resolution` consults — so the check is defined even for
  consumer members extracted before the provider inventory walk completes.
- **Evidence for the hole (corrected by probe after RO5U; the RO5U-passed
  text wrongly claimed fn items implement `Debug`):** since Rust 2021,
  format strings capture identifiers from scope. Provider value items
  compile as captures — `use provider::MAX;` +
  `take_args(format_args!("max={MAX}"))` compiles (consts/statics implement
  `Display`/`Debug`), and so does the aliased form (`use provider::MAX as
  LIMIT;` + `format_args!("{LIMIT}")`) — while the token trees contain only
  a string literal, so the walker records no demand and no gap: a scoped
  claim passes while the consumer secretly reads a provider value item.
  Fn items do NOT compile as captures (no `Display`/`Debug`/`Pointer` impl —
  probed and compiler-refused), and fn-pointer flow via path expressions is
  already disclosed by `visit_expr_path` — so the hole is precisely value
  items (consts/statics), direct or aliased. Note the same capture is
  already legal for plain locals; the check below closes only the
  provider-item boundary.
- **Evidence for the hole:** since Rust 2021, `println!("{greet:?}")` with
  `use dept::greet` compiles (fn items implement `Debug`) and the token
  trees contain only a string literal — the walker records no demand and no
  gap, so a scoped claim passes while the consumer secretly references the
  provider function. Note the plain `Display` form (`println!("{greet}")`)
  does NOT compile for fn items, which is why the hole is easy to miss.
- **Why the check is cheap and safe:** format literals are single string
  expressions; capture extraction is a scan of their contents. Alias
  membership is per-member pre-pass state; provider leaf names come from
  the slot meanings at demand-resolution time.
  False-gap risk is bounded: a local variable that happens to share a name
  with a provider item is shadowing — refusing it as Unknown is honest and
  conservative (the disclose law prefers over-disclosure to silent
  acceptance).
- **What stays demand-inert:** captures of plain locals (`{x}` where `x` is
  a local) record nothing — locals are not provider demand and never were.
  Only a capture matching a provider item name is disclosed.
- **Alternatives considered:**
  - *Full format-string grammar analysis* — rejected: overkill; the only
    demand-relevant content of a format string is the capture identifiers.
  - *Leave the hole, disclose in docs only* — rejected: silent acceptance of
    a provider reference violates the disclose-every-unsupported-mechanism
    law; a documented hole is still silent at extraction time.

### Decision 5: Held-out re-run as disclosed verification, expected byte-identical

- **Decision:** re-run the comparison (re-freeze with disclosed rewrite,
  compare, report) with the prediction that all wild-arm verdicts are
  byte-identical to the wild-f4i run: the e5 cohort contains no
  `format_args!` use and no format captures of provider items.
- **Why run it at all:** the wild-extract design states broader completeness
  claims require measurement, and an unverified "zero delta" claim is the
  kind this repo does not make. Any verdict movement contradicts the cohort
  audit and is a finding to investigate — possibly a corpus or adapter bug —
  never silently accepted.

## Risks / Trade-offs

- The capture cross-check can emit gaps for shadowed locals (local named
  like a provider item or an alias of one, captured in a format string).
  Accepted: honest
  over-disclosure; rare; and the refusal path is the same Unknown the
  profile already reports for unsupported mechanisms.
- The superset delta stacks on the still-open add-std-macro-demand-support
  change. Mitigated by the archive-order constraint in the proposal and
  tasks; both deltas are full-requirement copies, so the later archive
  simply wins with the complete scenario set.

## Migration Plan

None required: no persisted local-1 artifacts, no envelope change, no
corpus/oracle rewrite. Held-out re-run follows the wild-m7f.4/f4i precedent
exactly.

## Open Questions

None — the named-argument fallback and the capture check are both
probe-verified; the archive-order constraint is mechanical.