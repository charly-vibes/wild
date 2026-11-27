# accretes-is-transitive — evidence

## Identification

Baseline candidate 1 of bd wild-wz9; refined from the suite-level
`properties/wild.md` (commit c22c150) entry, re-verified at 4e26885.

- `accretes` conjoins the rule set: `src/v1.rs:804-825` (`remaining_outputs`,
  `retained_inputs`, `tombstone_history`, `new_inputs_forbidden`,
  `unchanged_input_defaults`, `unchanged_records`, `new_relations_forbidden`).
- Removal branch: `retained_inputs`, `src/v1.rs:885-899` — a removed input
  must leave a tombstone with the same meaning, checked as
  `subtype(&slot_type(tombstone), &slot_type(old_slot))` (`:898`).
- Reactivation branch: `tombstone_history`, `src/v1.rs:927-969` — a
  reactivated slot must be non-required `in` with the same meaning, checked
  as `subtype(&slot_type(old_tombstone), &slot_type(slot))` (`:966`).
- Retained inputs: `src/v1.rs:919` — `subtype(&slot_type(old_slot),
  &slot_type(new_slot))` (inputs widen).

## What goes wrong

The two tombstone checks use opposing subtype orientations. Removal accepts a
**narrowed** tombstone (tombstone domain ⊆ old input domain); reactivation
only requires the new slot's domain to **contain the tombstone**. A chain can
therefore shrink below its origin:

Constructed witness (integer intervals; all three contracts valid under
`validate_contract`):

1. Contract `a`: input slot `x` with type `integer[min=0,max=10]`, required.
2. `a → b`: remove `x`, leave tombstone `x` with type `integer[min=0,max=5]`.
   `retained_inputs`: `subtype([0,5], [0,10])` = Holds (narrowed tombstone
   accepted) → `accretes(a,b)` = Holds.
3. `b → c`: reactivate `x` as an optional input with type
   `integer[min=0,max=5]`. `tombstone_history`:
   `subtype([0,5], [0,5])` = Holds → `accretes(b,c)` = Holds.
4. `a → c`: `retained_inputs` now compares the original slot against the
   reactivated slot: `subtype([0,10], [0,5])` = Breaks →
   `accretes(a,c)` = Breaks.

Transitivity fails. Note the intermediate contracts are individually
consistent — the defect is the composed triple.

## Existing instrumentation vs. missing

- Fixed-example tests exist (`tests/v1_checker.rs:194-225`: identical
  contract accretes, removed output breaks, new required input breaks) but no
  generated triples and no transitivity check.
- The Python prototype checks transitivity exhaustively on a small-scope
  lattice (`prototype/wild_cat_sim.py:14-34`, `laws()`), and its `slot_ok`
  checks the tombstone in the **opposite** direction:
  `sub(old.ty, tomb.ty)` (`prototype/wild_sim.py:80` via `slot_ok(o, t)` at
  `wild_sim.py:77-82`) — the prototype requires a *widened* tombstone and
  reports zero transitivity violations on its 76-state lattice. The Rust
  model diverges from the prototype exactly here.

## Tombstone semantics: should the Rust model match the prototype's widened tombstone?

Both candidate repairs kill the witness:

- **Doc-equality (recommended).** `docs/wild-formats-v1.md` §Contract IR
  already says tombstones "must retain their last accepted meaning and
  **type**". Requiring canonical type equality on removal
  (`type_identical(tombstone, old_slot)`) matches the document, is strictly
  simpler than any subtype check, and restores transitivity: reactivation
  then needs `subtype(old, slot) ⊇ old`, so the composed `a → c` comparison
  holds.
- **Prototype's widened tombstone.** Checking `subtype(old_slot, tombstone)`
  (tombstone domain ⊇ old domain) also restores transitivity: reactivation
  gives `slot ⊇ tombstone ⊇ old`. This is what `prototype/wild_sim.py`
  implements ("fixed after exhaustive law testing", `wild_sim.py:32-34`), but
  it *diverges from the format document's retain-their-type wording*, so
  adopting it requires a doc change too.

Recommendation recorded in `evaluation/synthesis.md`: adopt doc-equality; do
not keep the narrowed acceptance. Either repair is a production change and
out of scope for this research ticket (implementer: bd wild-dr2).

## Generator sketch (valid contracts)

- Seed: `example_contract()` from `tests/v1_checker.rs:28` or a generated
  contract; validate with `validate_contract` before use and drop invalid
  seeds (generator must be validity-preserving, not filter-heavy).
- Edit language (each edit re-sorts affected set arrays by key, per
  `src/v1.rs:150-156`): add optional input; remove input (leaving a
  tombstone with chosen type — narrowed, equal, or widened); widen input
  interval; required → optional; add/remove output facet-consistently;
  reactivate a tombstone; add law/relations preserving ids.
- Constraints honored by construction: slot names unique across slots and
  tombstones (`src/v1.rs:140-148`); tombstones polarity `in`, non-required
  (`:242-249`); law ids unique; relations sorted by id; ids match
  `id_syntax` (`src/v1.rs:219`); defaults `{present:false}` / `{present:true,value}`
  inhabiting the declared type.
- Shrink: Hegel internal shrinking applies; keep edit sequences short
  (≤ 4 edits per contract) so minimal counterexamples stay human-readable.

## Predicted red/green

**RED** as stated (witness above). Two green variants worth writing alongside:
(a) transitivity restricted to chains with no tombstone transitions;
(b) transitivity under the doc-equality removal rule, as a red test pinning
the intended semantics once wild-dr2 lands.

**Open Questions:**

- Is the narrowed-tombstone removal acceptance intentional? `(needs human input)`
  - Examined: `src/v1.rs:885-969` both branches, `docs/wild-formats-v1.md`
    §Contract IR, `tests/v1_checker.rs`, `prototype/wild_sim.py:32-82`.
  - Found: the two branches test different subtype orientations; the doc's
    "retain their last accepted type" wording is not enforced by any test;
    the prototype checks the opposite (widened) direction.
  - Not found: any commit, spec note, or test pinning the narrowed direction
    as intentional.
  - Conclusion: tagged `(needs human input)` — owner confirms intent;
    recommendation is doc-equality (see `evaluation/synthesis.md`).
