# Implementor report — wild-m8c (composition-certificate prototype)

- **Ticket**: wild-m8c (P2, in_progress under epic wild-wsz)
- **Brief**: `.wai/projects/unikernel-cd/briefs/wild-m8c-composition-certificate.md`
- **Session**: `subagent:wild-m8c` · date 2026-10-14 · cwd `/var/home/sasha/para/areas/dev/gh/charly/wild`
- **Design rulings D1–D7**: implemented as pre-approved; not renegotiated.

## Sequence followed (red → green → results)

### 1. RED (test first)

Appended `test_wild_compose_certificate_deterministic_and_verified` (+ `load_wild_compose`
loader, same pattern as `load_wild_cd_sim`) to `tests/test_prototype_smoke.py` **before**
any implementation existed.

Command:

```
python3 -m pytest tests/test_prototype_smoke.py -q
```

Red output (pasted verbatim):

```
tests/test_prototype_smoke.py:103: 
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
tests/test_prototype_smoke.py:94: in load_wild_compose
    spec.loader.exec_module(module)
<frozen importlib._bootstrap_external>:755: in exec_module
    ???
<frozen importlib._bootstrap_external>:892: in get_code
    ???
_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 

self = <_frozen_importlib_external.SourceFileLoader object at 0x7f4631ff4ef0>
path = '/var/home/sasha/para/areas/dev/gh/charly/wild/prototype/wild_compose.py'

>   ???
E   FileNotFoundError: [Errno 2] No such file or directory: '/var/home/sasha/para/areas/dev/gh/charly/wild/prototype/wild_compose.py'

<frozen importlib._bootstrap_external>:950: FileNotFoundError
=========================== short test summary info ============================
FAILED tests/test_prototype_smoke.py::test_wild_compose_certificate_deterministic_and_verified
1 failed, 4 passed in 63.02s (0:01:03)
```

Committed as `c4d0086` — `test(wild-m8c): red smoke test for composition-certificate prototype (wild_compose)`.

### 2. GREEN (D1–D6 in `prototype/wild_compose.py`)

New file, stdlib only (`hashlib`, `json`, `random`, `time`), seeded `PARAMS["seed"]=20261014`,
imports `Contract`/`P`/`shape_check` from `wild_sim` only (D1: `wild_cat_sim` NOT imported).
No existing prototype file touched.

- **D2**: `build_fleet()` — layers=4, per-layer `[6,12,18,24]` (60 services, ASSUMED),
  `fan_out=3` (ASSUMED), one seeded root layer; each service a `Contract` of simple `Slot`
  records with globally-unique provides (`L{layer}S{i}.out{k}`); each edge records the
  consumer's demand = seeded subset of the provider's provides; the consumer's contract
  carries a *pin* (build-time view) of each demanded slot, which is exactly the
  `shape_check(consumer, provider, demand)` accretion relation used by `wild_cat_sim.verify`.
- **D3**: `certify()` emits `{version: 1, kind: "composition", seed, components, edges,
  merkle_root, verdict}`; `contract_digest = sha256(canonical JSON of slots)`;
  per-edge verdict = `accept` / `reject: <why>` / `unknown: <why>` scoped to the edge's
  demand; Merkle documented at `merkle_root()`: leaves = sha256 of canonical JSON of each
  edge record / component digest entry, `root = sha256("".join(sorted(leaf_hexes)))`
  (two-level shape of `wild_cd_sim.bench_checker`).
- **D4**: `verify(cert, contracts)` re-derives component digests, re-runs every per-edge
  check, rebuilds the root; labeled refusals `incomplete` / `tampered:<field>` /
  `edge:<key> <why>`; never trusts the certificate's own verdict fields.
- **D5**: `tamper_component_digest` (byte flip) → `tampered:components`;
  `tamper_edge_verdict` (accept→reject) → `tampered:edges` — distinct labels, printed.
- **D6**: `bench()` — compose_ms / verify_ms at ~10 / 60 / 200 services (layer tables in
  `PARAMS["bench_layers"]`, ASSUMED); incremental scenario bumps one mid-layer service
  (`L1S00`, out int64→int32 accretion) and shows the cached recheck: only incident edges
  re-checked, Merkle diff identifies changed leaves, `recheck_ms` + `rechecked_edges` printed.

Two mid-green syntax/logic fixes (walrus-in-comprehension, frozenset subscript, reject-demo
pin direction, fan-out cap for the 10-service table) — all within the slice, no scope growth.

Command + green run output (exit 0):

```
$ python3 prototype/wild_compose.py ; echo exit=$?
fleet: 60 services, 162 edges (layers=4, per_layer=[6,12,18,24], fan_out=3, seed=20261014)
certificate: version=1 kind=composition components=60 edges=162
  merkle_root=75e7aab7a6f234c4...  verdict=accept
verify(clean) = ok

== edge-verdict vocabulary (reject / unknown arms on real contracts)
  reject                   reject: L0S01.out1: output type str->int32
  unknown                  unknown: no.such.slot in no contract

== tamper evidence (independent verifier, D5)
  (a) component-digest byte flip -> tampered:components
  (b) edge verdict accept->reject -> tampered:edges

== MEASURED compose+verify cost (toy Python implementation)
  10 svc / 20 edges        compose_ms=0.53 verify_ms=0.31 verdict=accept
  60 svc / 162 edges       compose_ms=4.43 verify_ms=2.8 verdict=accept
  200 svc / 540 edges      compose_ms=17.14 verify_ms=9.48 verdict=accept
  incremental: bump L1S00 -> recheck_ms=2.88 rechecked_edges=7/162 (changed_leaves=1/222)
exit=0
```

Committed as `45b56c7` — `feat(wild-m8c): composition-certificate prototype — whole-graph check + Merkle (green)`.

### 3. Refactor

None needed (per brief: flat function style kept; no classes beyond imported dataclasses).

## Completion criteria — evidence

| Criterion | Command | Result |
|---|---|---|
| Smoke suite green incl. new test, red-first proven | `python3 -m pytest tests/test_prototype_smoke.py -q` | `5 passed in 63.32s (0:01:03)` (red run above) |
| Script exit 0 with summary / tamper / MEASURED / rechecked_edges | `python3 prototype/wild_compose.py` | exit 0 (output above; `rechecked_edges=7/162` printed) |
| Sibling prototypes still exit 0 | `python3 prototype/wild_sim.py` / `python3 prototype/wild_cd_sim.py` | both exit 0 (outputs redirected to /dev/null) |
| Results file | `python3 prototype/wild_compose.py > results/composition-cert-2026-10-14.txt` | exit 0, file created |
| Atomic commits, no `.beads`, no push | `git log` | 3 commits: red test / green feat / results+report; nothing pushed |
| Scope discipline | — | no file outside the brief's exact list touched; no follow-up finding needed |

## Notes for the verifier (wai-px4g)

- Artifacts read: brief, `prototype/wild_sim.py`, `prototype/wild_cd_sim.py` (bench D /
  PARAMS style), `prototype/wild_cat_sim.py` (`verify`/`certify`/`chash` semantics — read
  only, never imported), `tests/test_prototype_smoke.py`, `git log`.
- Fresh test-run output is pasted above (pytest green line + full script run); re-run both
  commands before recording CONFIRM.
- Determinism: `cert1 == cert2` and `contracts1 == contracts2` asserted by the smoke test;
  the only timing values (compose/verify/recheck ms) live in the MEASURED section and
  naturally vary run-to-run — everything else is seed-stable.

## Follow-up threshold

Not triggered: per-edge verdict logic needed only `wild_sim.shape_check` + a stdlib
`hashlib` Merkle; no type inference, no disk extraction, no dependencies. Nothing filed.

## Out of scope (untouched)

wild-3yy; real disk extraction; signing/registry/attestation; openspec/spec changes;
`wild_cat_sim.py`; README. No push performed (lead ships).
