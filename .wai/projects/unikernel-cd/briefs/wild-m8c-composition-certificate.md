# Brief: wild-m8c — composition-certificate prototype (whole-graph check + Merkle)

## Why
Delegation rationale: wild-m8c is a bounded, fully-specified prototype slice (one new
stdlib-only seeded Python script + smoke test + results file), mechanically executable from
the design rulings below. The lead orchestrator stays free to verify and ship; the epic
wild-wsz has one further child (wild-3yy) to orchestrate after this one. No Rust, no
openspec, no schema changes — pure prototype/ + results/ + one smoke test, mirroring the
wild-5gb run shape.

## Ticket
- **ID**: wild-m8c (P2, claimed in this run; bd in_progress)
- **Desired outcome**: the toy checker emits a tamper-evident *whole-graph composition
  certificate* (per-edge verdicts + Merkle roots) with an independent verifier, and the
  end-to-end compose+check cost is measured over a realistic synthetic fleet DAG — the
  artifact addresses gap 1 (composition-level gate) in the unikernel-cd research artifact.

## Design rulings (PRE-APPROVED by lead session — implement as stated)
- **D1 — additive, not destructive**: new file `prototype/wild_compose.py`, stdlib only,
  seeded and deterministic. Existing prototype scripts (`wild_sim.py`, `wild_cd_sim.py`,
  `wild_proto.py`, `wild_cat_sim.py`) are NOT touched; their outputs stay byte-stable.
  Importing from `wild_sim` (Slot/Contract/shape_check) and `wild_proto` is allowed and
  encouraged (in-memory Contract construction, no disk fixtures needed). Do NOT import
  `wild_cat_sim` (its module body runs minutes-long studies).
- **D2 — synthetic fleet DAG**: build the fleet in memory from a module-level `PARAMS`
  dict with ASSUMED comments (style of `wild_cd_sim.PARAMS`): layered DAG — `layers=4`,
  services per layer `[6, 12, 18, 24]` (total 60, ASSUMED), each service connects to
  `fan_out=3` (ASSUMED) providers in the layer below; one seeded root service per top
  entry. Each service is a `Contract` whose slots are simple `Slot` records; each edge
  records the consumer's demand (a frozenset of slot names actually used — derive
  deterministically from the seed, e.g. every consumer demands a seeded subset of its
  providers' provides).
- **D3 — certificate shape**: the composition certificate is a single JSON-serializable
  dict: `{version: 1, kind: "composition", seed, components: {service: contract_digest},
  edges: [{consumer, provider, demand, verdict, key}], merkle_root, verdict}` where each
  edge `verdict` is the per-edge scoped-check outcome (`accept` / `reject: <why>` /
  `unknown: <why>`) computed with `shape_check`/scoped logic over that edge's demand only;
  `contract_digest = sha256(canonical JSON of the contract's slots)`. Merkle construction
  (document it in a comment, matching the two-level shape of `wild_cd_sim.bench_checker`):
  leaves = sha256 over the canonical JSON of each edge record and each component digest
  entry; `merkle_root = sha256("".join(sorted(leaf_hexes)))`. `verdict` is `accept` only
  when every edge verdict accepts, else the refusal kind.
- **D4 — independent verifier**: `verify(cert, contracts)` re-derives everything from the
  presented contracts: recomputes component digests, re-runs each per-edge check, rebuilds
  the root, and compares. Any mismatch is a labeled refusal — `"incomplete"` (edge set or
  component set differs), `"tampered:<field>"` (a digest/verdict/root mismatch),
  `"edge:<key> <why>"` (a re-checked edge no longer accepts). Proof-carrying style,
  mirroring `wild_cat_sim.verify` — the verifier must not trust the certificate's own
  verdict fields for its decision.
- **D5 — tamper evidence**: the output must include a tamper section where at least two
  mutations of a clean certificate are verified and refused with DISTINCT labels:
  (a) flip one component digest byte, (b) flip one edge verdict accept→reject. Print the
  labels.
- **D6 — measurement**: a `MEASURED` bench section (style of bench D in `wild_cd_sim.py`):
  end-to-end compose+check wall cost at total fleet sizes ~10 / 60 / 200 services (scale
  the layer table, ASSUMED), reporting compose_ms and verify_ms separately; plus an
  incremental scenario — bump one mid-layer service's revision (change one slot) and show
  the cached-recheck cost: only edges incident to that service are re-checked (count them)
  and the Merkle diff identifies the changed leaves; print a `recheck_ms` and
  `rechecked_edges` line.
- **D7 — results + smoke, red-first**: save the full run output to
  `results/composition-cert-2026-10-14.txt`. Extend `tests/test_prototype_smoke.py` with
  one new test: load `wild_compose.py` by explicit path (same pattern as
  `load_wild_cd_sim`), assert PARAMS is present, assert determinism (build+certify twice,
  identical dicts), assert `verify` accepts the clean cert and refuses both tampered
  variants. Prove it red first (ImportError / missing module before the change), paste the
  red output in the report.

## Red/green/refactor sequence
1. **Red**: add the smoke test; run `python3 -m pytest tests/test_prototype_smoke.py -q`
   — new test fails (RED). Paste the red output in the report.
2. **Green**: implement D1–D6 in `prototype/wild_compose.py`; the new test passes;
   existing smoke tests stay green; `python3 prototype/wild_compose.py` exits 0 printing
   the DAG summary, certificate summary, tamper section, and MEASURED bench.
3. **Refactor**: none expected; keep the flat function style (no classes beyond the
   dataclasses you import).

## Exact files
- `prototype/wild_compose.py` (new)
- `tests/test_prototype_smoke.py` (one new test appended)
- `results/composition-cert-2026-10-14.txt` (new)
- `.wai/projects/unikernel-cd/runs/wild-m8c.report.md` (implementor report)

## Completion criteria (exit 0 = done)
- `python3 -m pytest tests/test_prototype_smoke.py -q` → all pass including the new test
  (proven red-first: paste the red run output in the report)
- `python3 prototype/wild_compose.py` → exit 0; certificate summary, two distinct tamper
  refusal labels, MEASURED compose/verify/recheck numbers, `rechecked_edges` line printed
- `python3 prototype/wild_sim.py` and `python3 prototype/wild_cd_sim.py` still exit 0
  (byte-stable outputs not required to be re-proven, just exit 0)
- `cp` the run output to `results/composition-cert-2026-10-14.txt`
- atomic commits: test commit (red), feat commit (green), results commit; never
  `git add .beads`; do not touch anything outside the exact files above
- do NOT push — the lead ships

## Out of scope
- wild-3yy (functor pilot) — separate run; any real extraction from disk projects (the
  fleet is synthetic in-memory); signing/registry/attestation (gap 2); openspec/spec
  changes; `wild_cat_sim.py` edits; README edits.

## Follow-up threshold
If the per-edge verdict logic needs machinery beyond `wild_sim.shape_check`/`wild_proto`
scoped checks (e.g. real type inference, disk-based extraction, or a Merkle tree library
dependency), STOP, commit what is green, and file the finding to bd — do not expand the
slice. A stdlib `hashlib`-based Merkle is the intended shape.

## Spawn model
- Implementor session name: `subagent:wild-m8c`
- Model: session default — same family as lead; acceptable for a mechanical,
  fully-ruling-specified slice
- Context ceiling: ≤ 60% of the model window, computed at spawn
- Wall-clock budget: `timeout 3600` around the spawn; background + log + poll, never
  blind-blocking
- Log: `.wai/projects/unikernel-cd/runs/wild-m8c.spawn.log`
- Report: `.wai/projects/unikernel-cd/runs/wild-m8c.report.md`
- Verifier evidence contract (wai-px4g): the verify step's review artifact must cite the
  artifacts it read and include fresh test-run output (actual command + result pasted)
  before recording CONFIRM — otherwise REVIEW_REQUIRED
