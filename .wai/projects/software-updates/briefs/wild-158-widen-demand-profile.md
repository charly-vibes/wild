# Brief: wild-158 — widen rust-cargo-local-1 demand profile (method calls + enum variants)

## Why
Delegation rationale: measured finding from the cdp.4 re-audit
(`results/adopt-audit-cdp4-1841.txt`) — all 12 consecutive testaruda release pairs
abstain (refuse/Unknown, exit 1) on `incomplete-demand` + `unsupported-construct`.
The gap composition is measured and ordered; this slice widens the two candidate
categories the ticket names. Context-heavy: each widening is a scope decision with
pre-approved rulings below — implement as stated, red-first, and file follow-ups
rather than approximating beyond them.

## Ticket
- **ID**: wild-158 (P2, claimed in this run; bd in_progress)
- **Desired outcome**:
  1. Method-call demand and enum-variant demand paths are supported where the
     rulings below define them; unresolvable shapes keep the honest gap.
  2. The re-audit's gap distribution improves (which categories cleared, reported
     honestly — abstention count MAY still be >0; do not force verdicts).
  3. Deployed spec `openspec/specs/wild-extract/spec.md` matches the new behavior
     via an openspec change archived in this slice.

## Design rulings (PRE-APPROVED by lead — implement as stated)

- **D1 — method-call demand, bounded syntactic resolution.** `visit_expr_method_call`
  no longer blanket-gaps. Resolve the receiver ONLY in bounded shapes:
  receiver is a call or path expression whose head resolves to an inventoried
  same-crate constructor/free fn with a known return type (the extractor already
  records return types for typed fn slots and opaque slots for others), or receiver
  is a plain inventoried type path. On resolution, the method call creates demand
  `<crate>::<Type>::<method>`:
  - resolves against inventory (public impl-method opaque slot or typed slot) →
    supported demand, no gap, counterexample-capable (candidate renaming/removing
    the method breaks the demand);
  - method absent from inventory → `incomplete-demand` gap naming the full path;
  - receiver outside the bounded shapes (multi-hop chains beyond one resolved hop,
    field access, macro output, unknown identifiers) → keep the honest
    `incomplete-demand` gap naming the receiver.
  NO type inference beyond the bounded shapes above — that is the follow-up
  threshold (D7).

- **D2 — enum-variant inventory + demand.** A public enum inventories its variants
  as named slots (`<Enum>::<Variant>` under the enum's qualified meaning) instead of
  a single opaque enum item. Variant demand paths (`Enum::Variant` in expression
  position) resolve as supported demand when the variant is inventoried; unknown
  variant paths keep the `incomplete-demand` gap naming the path. Variant slots
  follow the identity law (crate identity + qualified path, never line numbers).

- **D3 — impl-block gap discipline.** The blanket blocking
  "method implementations are outside the supported profile" `unsupported-construct`
  gap is replaced by honest per-construct accounting: public impl methods already
  inventory as opaque slots (existing behavior, kept); the blocking gap is emitted
  only for impl items the profile genuinely cannot represent (private items made
  reachable via `pub(in)`/`pub(crate)`, trait impls). Never silent: whatever remains
  unsupported keeps a named gap. Rationale: with D3 unruled, no pair could ever
  leave abstention and the widening would be unmeasurable.

- **D4 — signature subset unchanged.** The unit/bool/i8..u32 typed-fn signature
  subset stays exactly as-is; non-scalar fns keep opaque-slot + `unsupported-construct`
  treatment. Only demand-side resolution and variant inventory widen. (Ticket law:
  never silently relax the signature subset.)

- **D5 — spec + docs via openspec change, archived in this slice.**
  Create `openspec/changes/add-method-variant-demand/` with a MODIFIED
  "Explicit consumer demand coverage" requirement (the current text mandates that
  "a consumer containing an unresolved macro, returned-object method call, or
  function-pointer flow ... retains the incomplete-demand gap" — the method-call
  clause changes; macro and function-pointer clauses stay verbatim) and any variant
  inventory delta in the inventory requirement. Update `docs/wild-local-v1.md`
  supported-set description. Schema `schemas/wild-local-v1.schema.json` unchanged.
  Do NOT remove or rename any existing scenario — bound contract TOMLs in
  `.espectacular/wild-extract/` pin existing node ids (macro behavior is untouched
  and must stay green). Archive the change only after all gates are green so
  deployed specs match code at ship; expect one new contract binding for the new
  scenarios only if ah-check demands it (follow the established archive pattern).

- **D6 — determinism and test hygiene.** 3-run byte identity must hold for widened
  extraction; existing tests stay green; any legitimate expected-output change in an
  existing test is justified explicitly in the subagent report. Keep `src/extract.rs`
  under the 1200-line pretender ratchet — put the new resolution logic in new
  modules under `src/extract/` (mirror `mod_files.rs` / `macro_demands.rs`).

- **D7 — follow-up threshold.** If a widening category reveals it needs real type
  inference (receiver chains beyond the bounded shapes), stop that category, keep
  the honest gap, and file a follow-up bd ticket naming the limitation. Never
  approximate.

## Exact commands
- Red first: `pytest tests/runtime/test_extract.py -k widen -q` (new tests) must FAIL
  before implementation — prove red, then make green.
- Full runtime meter: `pytest tests/runtime -q` (baseline 116 passed — attribution).
- Cargo: `cargo test -q` (checker scenarios).
- Pretender + full gate: `JUST_TEMPDIR=/tmp just ci` (expect exit 0; NOT CALIBRATED
  advisory is benign; if meters disagree with source state, clear
  `target/debug/.fingerprint/wild-vibes-*` — known stale-fingerprint gotcha).
- Spec gates: `openspec validate --all --strict`; `ah check` (overlay while change
  open, baseline after archive, `--run-tests` post-archive).
- Audit re-run: `python3 experiments/wild_adopt_audit.py --crate testaruda` →
  record output as `results/adopt-audit-158-<n>.txt`; report the new gap
  distribution (categories cleared / remaining) vs `results/adopt-audit-cdp4-1841.txt`
  in the rung-1 addendum of
  `.wai/projects/software-updates/research/2026-10-14-dogfooding-wild-into-dulce-de-leche.md`.

## Commit protocol
- Commits in the wild repo are allowed during implementation (red→green→refactor,
  tidy separate); do NOT push and do NOT `bd close` — the orchestrator owns ship.
- Suggested atomic sequence: (1) red tests, (2) variant inventory + demand, (3)
  method-call resolution, (4) spec/docs/archive, (5) audit re-run results.

## Out of scope
Signature-subset relaxation, trait-method demand, generics-aware resolution, any
ddl-repo change, rung-2 design (that is wild-cdp.3, next run).
