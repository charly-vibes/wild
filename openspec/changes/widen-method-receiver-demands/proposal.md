# Change: Widen method-receiver demands — declared receiver shapes beyond one hop

## Why

The wild-158 widening (beads wild-158, design ruling D1) gave method calls two
bounded receiver shapes — a path expression resolving through
`bounded_target`, and a constructor/free-fn call with a recorded syntactic
return type — and left everything else as the honest `incomplete-demand` gap
(`src/extract/method_demands.rs`, `ReceiverOutcome::Unresolved`). The adopt
audit measured what that boundary costs
(`results/adopt-audit-158-1.txt`): **12/12 consecutive-release pairs
abstained (unknown-abstention rate 100.0%)**, with `incomplete-demand` and
`unsupported-construct` diagnostics on every inventoried testaruda version
0.1.0–0.5.5, and testaruda 0.5.5 carries **~300 named incomplete-demand gaps**
— method calls like `.to_string`/`.exists`/`.join` on local variables, on
`self`, on field-access receivers, and on cross-file constructor chains
(bd wild-8j4). The same file's own audit line records unresolved same-crate
method demands (e.g. `testaruda::demand::testaruda::adapter::AdapterRegistry::new`,
`...::AdapterCommand::discover`) alongside the external ones owned by
bd wild-90d.

The concrete boundary is in the code: the return-type pre-pass
(`scan_fn_returns`) scans **one file at a time**, so its own comment records
the limit — "cross-file and cross-crate constructors keep the honest gap
(D7 threshold — file a follow-up, never approximate)" — and the receiver
shapes stop at locals-in-unrelated-shapes, field access, and `self`.
This change is that follow-up: it widens the *declared* receiver shapes so
the honest gap shrinks by rule, never by approximation. bd wild-8j4 says it
plainly: "never approximation; the honest gap stays until then."

## What Changes

- **Declared receiver shapes widened** (wild-extract, `rust-cargo-local-1`):
  four additional shapes join the bounded set, each a declared rule
  validated against the inventory at demand-resolution time — (1) a
  let-bound single-assignment local whose initializer is a resolved call
  with a recorded return type; (2) a field-access receiver whose field type
  is inventoried from a public struct-field declaration; (3) a
  `self`/`Self` receiver inside an inherent impl body of that type;
  (4) method chains whose every hop resolves by these rules and whose
  callee targets have recorded return types.
- **Bundle-wide pre-pass**: the syntactic return-type and field-type
  pre-pass becomes cross-file over the supplied bundle (replacing the
  per-file `scan_fn_returns` scan), so cross-file constructor chains resolve.
  No new inputs, no new trust — the same supplied bundle, hashed as today
  (`extractor_deterministic` unchanged).
- **Residual disclosure re-scoped**: "Unbounded method-call receivers stay
  disclosed" now names the genuinely unresolvable residual — trait-object
  and generic receivers, macro-produced receivers, closures and re-bound
  locals, a chain hop without a recorded return type, unknown identifiers.
  Gaps keep naming the receiver and refusing scoped acceptance.
- **What will NOT change**: no type-inference engine, no `cargo`/`rustdoc`
  invocation, no compiler-in-the-loop extraction (design.md weighs that as
  Option A and defers it); `bounded_target` path rules unchanged;
  `self`/`Self`/`super`-qualified **multi-segment demand paths** (non-receiver
  free-path demands) stay outside the demand profile — that needs module
  scope knowledge the profile does not carry and is a separate decision;
  trait impls and restricted-visibility items keep their named gaps
  (type_inventory.rs D3 unchanged); gaps never cure silently.

## Impact

- Specs: `openspec/specs/wild-extract/spec.md` — MODIFIED "Bounded
  method-call resolution" (declared receiver rules, scenarios for each new
  shape) and MODIFIED "Unbounded method-call receivers stay disclosed"
  (residual shapes).
- Code: `src/extract/method_demands.rs` (receiver resolution rules,
  bundle-wide pre-pass), `src/extract/type_inventory.rs` (public
  struct-field type recording). No core/IR change; demand entries keep
  their current shape.
- Measured gate: re-run the adopt-audit harness that produced
  `results/adopt-audit-158-1.txt` — per the ticket's follow-up threshold,
  the deliverable is the before/after gap rate and the residual named-gap
  list on testaruda 0.5.5, not a green checkmark.
