# Design: widen-method-receiver-demands

## The trade-off this change settles

bd wild-8j4 names the fork exactly: "genuine type inference OR a
declared-trust widening … never approximation; the honest gap stays until
then." The two options answer the same question — *when a method call's
receiver is a local, a field, `self`, or a chain, who is allowed to say what
type it is, and on what evidence?*

### Option A — genuine type inference (compiler in the loop)

Harvest per-call-site receiver types from the compiler's own analysis and
feed them to the extractor as a hashed input artifact.

Mechanics, concretely:

- **A1 (rustdoc JSON)**: `cargo rustdoc -Zunstable-options --output-format
  json` gives typed signatures for every item, including each public
  inherent method's self type. This resolves *signatures*, not call sites —
  it still cannot say what type `r` is at `r.tick()` without flow analysis,
  so A1 alone does not close the local-variable case.
- **A2 (compiler diagnostics/analysis)**: `cargo check --message-format=json`
  plus nightly `-Zsave-analysis` (deprecated-but-functional) or an
  rust-analyzer analysis harvest produces the per-call-site receiver-type
  facts A1 lacks. The harvested facts file becomes an extraction input:
  digested like source, bound in provenance, determinism preserved by
  pinning the generator toolchain and digesting its output
  (`extractor_deterministic` already requires "the same supplied source
  bundle, extractor artifact digest, options, and IR version").

Trade-offs:

- **Coverage**: near-total for concrete-typed receivers — locals, fields,
  `self`, chains, and cross-file/cross-crate constructors in one stroke.
  It also hands bd wild-90d its dependency signatures for free (the dep
  rustdoc JSON is the same artifact), which is the strongest argument for A.
- **Trust surface**: a compiler artifact becomes an extraction input. The
  trust model is well-defined (facts are compiler-derived; absent fact →
  honest gap; digest mismatch → input-binding failure, same as the existing
  "changed build input requires new extraction" rule), but the trust
  boundary of the profile grows by a toolchain.
- **Cost/determinism**: `extractor_isolated` forbids network access and
  writes — a `cargo check` in the bundle must run offline against
  vendored/supplied deps, which the bundle convention must already support
  (the contract-bundle change owns build-input supply). rustdoc JSON format
  is unstable → toolchain must be pinned in provenance or determinism is
  lost between CI runs.
- **Risk**: nightly-feature churn (`-Zsave-analysis` deprecation path),
  monomorphization/generic pitfalls (facts may be absent for polymorphic
  call sites — fine, they fall back to the honest gap), and a much larger
  implementation surface than the measured problem needs first.

### Option B — declared-trust widening (this change)

Extend the declared receiver shapes with rules that are purely syntactic and
validated against the inventory at demand-resolution time. No new inputs, no
compiler, no new trust — everything is derived from the supplied bundle that
is already hashed.

The widened rules (each falsifiable, each falling back to the named gap):

1. **Bundle-wide pre-pass** (fixes cross-file chains): `scan_fn_returns`
   currently runs per file; run it over all files of the bundle before any
   demand walk. Public free fns and public inherent impl methods with
   single-segment, uppercase-initial path return types record
   `fn_target → crate-qualified type` bundle-wide. Public struct fields
   with such types record `field_name → type` per defining type
   (new, in type_inventory.rs). No inference: written syntax only.
2. **Let-bound constructor flow**: `let r = <resolved call>;` where the
   callee target has a recorded return type records the binding's type for
   the remainder of the scope block. Single assignment only: a rebinding,
   `let mut` reassignment, or initializer outside the resolved-call shape
   keeps the local unresolved.
3. **Field access**: `expr.field.method()` where `expr` resolved to a type
   whose inventoried public field `field` has a recorded type. Tuple
   indexing, private fields, and unknown fields stay unresolved.
4. **`self`/`Self` inside impl bodies**: a method call whose receiver is
   `self`/`Self` inside a public inherent impl on a named path type
   resolves to that impl's type. (Trait-impl bodies are already
   unsupported-construct gaps per D3 and record nothing.)
5. **Hop folding for chains**: a chain resolves hop-by-hop; a hop whose
   callee target has a recorded return type feeds the next hop's receiver.
   The first hop without a recorded return type keeps the gap naming the
   receiver, and the hops already resolved keep their recorded demands —
   the current one-hop behavior, generalized, never retroactively cured.

Validation is unchanged: the produced `<crate>::<Type>::<method>` demand
cross-checks against the full inventory in
`src/extract/demand_resolution.rs::check_demand_resolution`; an absent
method keeps the `incomplete-demand` gap naming the full path. Widening
moves work from the *receiver* gap into resolution, where absence is a
named, honest failure — never a silent success.

Trade-offs:

- **Coverage**: clears the measured dominant shapes — locals bound from
  constructors/recorded-return fns, `self`, field access, cross-file
  constructor chains, bounded chains. Does not touch trait objects,
  generics, macro outputs, closures, or re-bound locals; those keep the
  gap by name (a smaller, typed-by-shape residual).
- **Trust surface**: zero growth. The widening rules are declared in the
  profile spec (scenarios pin them); the only facts used are written in
  the supplied bundle.
- **Cost**: small — a pre-pass change, a field-type table, two receiver
  match arms, a fold loop. Contract-testable red-first, matching the
  wild-158 task pattern.
- **Risk**: rule creep — each new syntactic shape must be a declared rule
  with a scenario, or it is approximation. This design caps the set at the
  five rules above; anything outside is a follow-up ticket, not a heuristic.

## Recommendation

**Option B now; Option A as a designated follow-up, not a rival.**

- The measured abstention (12/12 pairs, 100.0% unknown rate,
  `results/adopt-audit-158-1.txt`) is dominated by shapes B clears with no
  new trust and a small, testable surface. The honest-gap rule survives
  intact: every widened resolution either lands on an inventoried slot or
  names its gap.
- A's coverage advantage is real but its prerequisites (bundle-supplied
  offline build inputs, pinned toolchain in provenance, digest-bound
  compiler artifacts) are exactly the trust machinery bd wild-90d must
  settle first. Designing A inside this change would either preempt that
  scope decision or bake a parallel trust model. The right seam is a
  follow-up change — "typed-receiver facts as extraction inputs" — that
  reuses wild-90d's declared-signature trust model for compiler-derived
  facts.
- Until A lands, the honest gap stays for the residual shapes. That is the
  ticket's own standard: "never approximation; the honest gap stays until
  then."

## Predicted effect on the abstention rate

- Status quo: 100% abstention (12/12 pairs), `incomplete-demand` +
  `unsupported-construct` on all 13 inventoried versions.
- Option B: predicted to clear the largest single share of the ~300 named
  0.5.5 method-call gaps (locals, `self`, field access, cross-file chains
  — the shapes the ticket enumerates). Quantitatively unverifiable until
  re-run; the audit harness re-run before/after is a required task, and the
  residual named-gap list it prints is the acceptance evidence. The
  residual after B is predicted to be dominated by the external-crate
  demands bd wild-90d owns (41 distinct external/unmodeled demand targets
  visible on the 0.5.5 audit line: `std.io.Error.new`, `libc.kill`,
  `shell_words.split`, `Duration.from_millis`, `Command.new`, `Stdio.piped`,
  …) plus the unsupported-signature inventory slots (trait impls).
- Option A (deferred): near-total for concrete-typed receivers; combined
  with wild-90d's declared signatures, the testaruda 0.5.5 abstention
  collapses to genuinely unknown items. Not predicted here as a gate —
  it is a different change with its own trust model to approve.

## Capability placement and house rules

- All deltas live in **wild-extract**: the receiver rules are demand-profile
  rules, same home as "Bounded method-call resolution" and "Unbounded
  method-call receivers stay disclosed". No other capability changes —
  `check_demand_resolution` semantics (absent target → gap) are untouched,
  so wild-adopt/wild-evaluate verdict semantics are unaffected.
- House style honored: never-fabricated (a missing fact is a named gap,
  exactly like `missing-base-contract` in add-declared-bump-derivation);
  gaps never cure silently (D1's "The call is always descended afterwards"
  is preserved by the fold rule); the honest gap stays until evidence
  arrives.
- `extractor_deterministic` holds: the pre-pass sees only bundle files,
  ordered deterministically as today; same bundle → same bytes.

## Non-goals

- Type inference, `cargo`/`rustdoc`/rust-analyzer invocation inside
  extraction (Option A follow-up).
- `self`/`Self`/`super`-qualified **multi-segment demand paths** (free-path
  demands like `self::helper::build()`): they need module-scope knowledge
  the bounded shapes do not carry; noted in bd wild-8j4 as related incumbent
  silence, but it is a path-resolution question, not a receiver question —
  separate change.
- Trait-method resolution, trait objects, generic receivers: trait impls
  are unsupported-construct gaps per D3; receiver widening does not
  reclassify them.
- Cross-crate constructors: out of this change by definition (nothing in
  the bundle declares them); they are bd wild-90d's demand targets.
- Gating or verdict semantics: demand coverage behavior (refuse scoped
  acceptance on any gap) is unchanged; this change only moves demands from
  "gapped by shape" into "resolved or named-gap".
