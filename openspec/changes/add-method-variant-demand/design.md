# Design: add-method-variant-demand

Context: the cdp.4 re-audit measured a 100% abstention rate over 12
consecutive testaruda release pairs, with a measured, ordered gap
composition. The lead pre-approved scope rulings D1–D7 (brief
`.wai/projects/software-updates/briefs/wild-158-widen-demand-profile.md`);
this design records how each ruling lands in code.

## Decisions

### D1 — method-call demand, bounded syntactic resolution

`visit_expr_method_call` delegates to
`method_demands::SourceWalk::handle_method_call`. The receiver resolves
ONLY in bounded shapes:

- **Path receiver**: resolved through the shared `bounded_target` rules
  (declared dependency heads, import aliases with rest, crate-qualified
  heads, module-relative multi-segment candidates). The candidate type
  target is validated against the full inventory at demand-resolution
  time, so an unknown identifier keeps the honest gap instead of an
  invented resolution.
- **Call receiver**: the callee resolves through `bounded_target`; the
  resolved fn target is looked up in `fn_return_tys` — a map recorded by a
  per-file pre-pass (`scan_fn_returns`) covering public free fns and
  public inherent impl methods whose return type is a single-segment,
  uppercase-initial path type (`-> Meter`). This is written syntax, not
  inference. The type target is the declaring module base plus the
  recorded type name, so `Meter::new().tick()` inside the declaring module
  resolves to `consumer::Meter` and demands `consumer::Meter::tick`.
- **Everything else** (method-call chains beyond one resolved hop, field
  access, macro output, literals, bare unknown identifiers): walk-time
  `incomplete-demand` gap naming the receiver text.

On resolution the demand `<crate>::<Type>::<method>` is recorded and
validated like every other demand: inventoried (public impl-method opaque
slot or typed slot) → supported demand, counterexample-capable (renaming
or removing the method breaks the demand); absent → `incomplete-demand`
gap naming the full path. The call is always descended so arguments and
nested calls record their own demands — never silently dropped.

Cross-file same-crate constructor receivers (use site in a different file
than the constructor) keep the honest gap: the pre-pass is per-file by
design, and anything wider is the D7 threshold (real type inference), not
this slice.

### D2 — enum-variant inventory + demand

`type_inventory::inventory_enum`: a public, non-cfg-gated,
non-generic enum inventories each variant as a named slot
`<crate>::<module>::<Enum>::<Variant>` with a versioned meaning (fn-slot
convention), replacing the single opaque enum item. Variant fingerprints
are formatting-invariant token digests. Cfg-gated variants keep a named
gap; generic public enums keep the legacy opaque item plus a named gap.
Variant demand paths resolve through the same bounded resolution: dep-
qualified (`provider::Mode::Slow`) via the existing dep rule, same-crate
(`Flavor::Sour`) via the module-relative candidate validated against the
inventory. Unknown variants keep the gap naming the path.

### D3 — impl-block gap discipline

`type_inventory::account_impl` replaces the blanket gap with per-construct
accounting: public inherent impl methods inventory as type-qualified
opaque slots with versioned meanings (previously unqualified, which made
duplicate method names collide and method demands unresolvable); plain-
private impl items carry no public API surface (exactly like private free
fns — the incumbent private-item treatment); restricted-visibility
(`pub(crate)`/`pub(in)`) items and trait impls keep named
`unsupported-construct` gaps. Impl bodies are now walked (previously
silently skipped), so demands and method calls inside them are recorded —
per-construct honesty, never silence.

### D4 — signature subset unchanged

`scalar_type` is untouched. The only return-type recording is the
resolution-side `fn_return_tys` map (typed fn slots record scalar returns
nowhere; the map only holds uppercase-initial path types). Non-scalar fns
keep opaque-slot + `unsupported-construct` treatment. The ticket law —
never silently relax the signature subset — holds.

### D5 — spec + docs via openspec change

MODIFIED requirements "Bounded deterministic Rust extraction" (variant
inventory + impl accounting) and "Explicit consumer demand coverage"
(bounded method-call demand + variant demand paths). The macro and
function-pointer clauses stay verbatim; the "Hidden usage blocks a scoped
claim" scenario's GIVEN swaps the returned-object method-call clause for
the bounded-shapes clause, keeping macro and function-pointer wording
verbatim. No existing scenario is removed or renamed. Schema unchanged.

### D6 — determinism and test hygiene

All widened logic is name-based (crate identity + qualified path); no
line numbers in semantic bytes. Repeated-extraction byte identity is
pinned inside the widen tests. `src/extract.rs` stays under the 1200-line
ratchet via new modules `src/extract/method_demands.rs` and
`src/extract/type_inventory.rs`.

### D7 — follow-up threshold

Shapes needing real type inference (variable receivers, cross-file
constructor chains, generic resolution) keep the honest gap; follow-ups
are filed rather than approximated.

## Test shape

Red-first `-k widen` fixtures in `tests/runtime/test_extract.py`
(`test_widen_*`): same-crate constructor-receiver method demand resolves
(with byte-identity determinism pin), absent method gaps naming the full
path, unbounded chain receiver gaps naming the receiver while keeping the
one-hop demand, enum variants inventory as named slots (opaque enum item
gone), dep-qualified + same-crate variant demands resolve, unknown variant
paths gap naming the path, and per-construct impl accounting (no blanket
gap; type-qualified pub method slot; named gaps for trait impls and
`pub(crate)` method).
