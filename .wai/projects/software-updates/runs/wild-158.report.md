# wild-158 implementation report — widen rust-cargo-local-1 demand profile

Implementor subagent run, 2026-10-14. Brief:
`.wai/projects/software-updates/briefs/wild-158-widen-demand-profile.md`
(rulings D1–D7 implemented as stated; red-first TDD; no push, no `bd close`).

## Commits (sha + subject)

| sha | subject |
| --- | --- |
| `7cd5f18` | test(wild-158): red-first widen tests — bounded method demand, enum variants, per-construct impl accounting |
| `c07053f` | feat(wild-158): enum-variant inventory + bounded same-crate demand resolution (D2) |
| `7d73f98` | feat(wild-158): bounded method-call demand resolution (D1) + per-construct impl accounting (D3) |
| `04890f8` | docs(wild-158): openspec change add-method-variant-demand + supported-set docs |
| `1d75fbc` | tidy(wild-158): Self-qualified paths stay outside the bounded demand profile |
| `2be48d7` | results(wild-158): adopt audit re-run after demand-profile widening |
| `67df463` | docs(wild-158): archive add-method-variant-demand + contract bindings for new scenarios |

Red→green protocol: commit 1 proved all 6 `-k widen` tests failing
(6 failed / 33 deselected); commits 2–3 made them green in separate
D2 / D1+D3 slices; commit 5 is a tidy-after-green refactor.

## Test results (actual outputs)

- Red proof (pre-implementation):
  `pytest tests/runtime/test_extract.py -k widen -q` → **6 failed, 33 deselected**.
- Post-implementation: same command → **6 passed**.
- Full runtime meter: `pytest tests/runtime -q` → **122 passed** (baseline
  116 + 6 new; no pre-existing test modified).
- Cargo: `cargo test -q` → **12 passed; 0 failed**.
- Pretender + full gate: `JUST_TEMPDIR=/tmp just ci` → **exit 0** (run twice:
  before archive and after archive + contract bindings; 0 pretender
  violations, extract.rs 1133 lines — under the 1200 ratchet; testaruda
  gate ingested 269 + 2 results; no NOT CALIBRATED advisory appeared in the
  final run).
- Spec gates: `openspec validate --all --strict` → **11 passed, 0 failed**
  with the change overlay, **10 passed, 0 failed** post-archive;
  `spk lint openspec` → 0 findings, 0 advisory warnings;
  `ah check` → 0 issues with overlay, then 7 `no-toml` structural findings
  post-archive (expected — new scenarios), then **0 issues** after adding
  the 7 contract TOMLs (see D5 deviation note below).

## Audit re-run numbers

`python3 experiments/wild_adopt_audit.py --crate testaruda --out results/adopt-audit-158-1.txt` → exit 0.
Recorded as `results/adopt-audit-158-1.txt` (12 consecutive pairs, 13 versions).

| metric | cdp4 baseline (`adopt-audit-cdp4-1841.txt`) | after wild-158 (`adopt-audit-158-1.txt`) |
| --- | --- | --- |
| pairs audited | 12 | 12 |
| abstained (refuse/Unknown, exit 1) | 12 (100%) | **12 (100%)** — unchanged, expected and allowed |
| consistent / disagreement | 0 / 0 | 0 / 0 |
| determinism (byte identity) | pass | pass |
| 0.5.5 diagnostics | 81 incomplete-demand + 26 unsupported-construct | 414 incomplete-demand + 24 unsupported-construct |
| 0.1.0 diagnostics | (codes only recorded in baseline log) | 211 incomplete-demand + 17 unsupported-construct |

**Categories cleared** (vs `adopt-audit-cdp4-1841.txt`):
- Enum-variant demand gaps (`AdapterError::Io`, `AdapterIO::spawn_in`) now
  resolve as supported demand against named variant slots
  (`testaruda::adapter::AdapterError::Io` etc. inventoried).
- The blanket "method implementations are outside the supported profile"
  `unsupported-construct` gap: **0 occurrences** in all 12 versions
  (previously 19 in 0.5.5 alone), replaced by named per-construct gaps
  (trait impls `Default`/`Drop`/`ProvenanceSemiring`, associated consts
  `AdapterCommand::*`, non-scalar signature fns).
- Impl-method slots are now type-qualified
  (`testaruda::adapter::AdapterIO::spawn_in`), removing the prior duplicate
  colliding slot names (`testaruda::adapter::new` ×2 style).
- Bounded-receiver method calls resolve (demand
  `<crate>::<Type>::<method>` validated against inventory).

**Honest volume increase**: incomplete-demand counts grew (0.5.5: 81 → 414).
This is disclosure expansion, not regression: per-construct accounting now
walks impl bodies that were previously silently skipped, and same-crate
optimistic recording names previously-invisible std/prelude references
(`std::io::Error::new`, `Vec::new`, `json!`, `miette!`). Residual blockers,
in order: (1) method calls on non-bounded receivers (locals, literals, std
objects — needs type inference), (2) std/third-party references outside the
bundle, (3) trait impls (named gaps, D3), (4) non-scalar signature fns
(unchanged, D4).

Addendum recorded in the rung-1 section ("Rung 1 addendum 2") of
`.wai/projects/software-updates/research/2026-10-14-dogfooding-wild-into-dulce-de-leche.md`.

## Ruling compliance and interpretation notes

- **D1** implemented as stated: bounded shapes only (path receivers via
  `bounded_target`; call receivers via recorded syntactic return types;
  everything else gaps naming the receiver). Two interpretation notes:
  - *Type-path receivers*: an expression-path receiver resolves through the
    bounded demand rules and is **validated against the inventory at
    demand-resolution time** rather than at walk time (the full inventory
    does not exist during the walk); an unknown identifier therefore keeps
    the honest gap via validation, satisfying "unknown identifiers → gap".
  - *Same-crate module-relative candidates*: multi-segment local paths
    resolve module-relative (correct Rust scope rule) and are validated
    against the inventory; this is what makes same-crate `Enum::Variant`
    and `Type::method` calls resolve (D2 + D1 demand surfaces).
- **D2** as stated; variant slots replace the opaque enum item, identity
  law held (crate identity + qualified path, versioned meanings).
- **D3** as stated. One interpretation: bare-private impl items carry no
  public API surface and are skipped without a gap — identical to the
  incumbent treatment of private free fns and private modules; the ruling's
  "private items made reachable via `pub(in)`/`pub(crate)`" is read as
  restricted-visibility items, which keep named gaps.
- **D4** held: `scalar_type` untouched; non-scalar fns keep opaque + gap
  (visible in the audit: `parse_command_string`, `spawn_adapter`, … remain
  named gaps).
- **D5** done via openspec change `add-method-variant-demand`, archived as
  `openspec/changes/archive/2026-10-14-add-method-variant-demand` with the
  two MODIFIED requirements; macro and function-pointer clauses verbatim;
  no existing scenario removed or renamed;
  `docs/wild-local-v1.md` gained the "Extraction supported set (wild-158)"
  section; schema unchanged. *Deviation from the brief's expectation of
  "one new contract binding"*: ah check demanded bindings for **all 7**
  new scenarios (one `no-toml` finding each), so 7 contract TOMLs were
  added following the established `.espectacular/wild-extract/` pattern —
  the brief's "follow the established archive pattern" clause governs.
- **D6** held: 3-run byte identity pinned inside the widen tests and by the
  audit determinism gate; extract.rs at 1133 lines (new logic in
  `src/extract/method_demands.rs` and `src/extract/type_inventory.rs`).
  One justified expected-output change in an existing-test-facing surface:
  none — no existing test changed; contract bytes for impl-method slots
  changed shape (type-qualified names), which no prior test pinned.
- **D7** followed: no type inference beyond the bounded shapes; follow-ups
  filed (below).

## Follow-ups filed (bd)

- **wild-8j4** (P3): Method-call demand on non-bounded receivers needs real
  type inference (also records the incumbent `self`/`Self`/`super`-silent
  treatment).
- **wild-90d** (P3): rust-cargo-local-1 std/external-crate awareness for
  demand resolution (dominant residual abstention cause).

## Blockers

None. The slice is complete and all gates are green; `bd wild-158` remains
in_progress and nothing was pushed, per the orchestrator-owned ship.
