# Implementor report — wild-5gb (unikernel-parameterized CD sim variant)

- **Status**: COMPLETE (within brief's slice; one evidence caveat documented below)
- **Session**: `subagent:wild-5gb` · Repo cwd: `wild/` · No push (lead ships)
- **Commits** (atomic, in order, never `git add .beads`):
  - `aa445e6` test(wild-5gb): red smoke test for unikernel scenario arms (deterministic, PARAMS)
  - `7961d0d` feat(wild-5gb): unikernel parameterization — PARAMS, E/F/G/H scenario arms, floors_residual, hypothesis verdict
  - `8bf5d22` docs(wild-5gb): record unikernel-cd sim run output (results/unikernel-cd-sim-2026-10-14.txt)

## Red (step 1)

Appended `test_wild_cd_sim_unikernel_scenarios_deterministic` to
`tests/test_prototype_smoke.py` (imports PARAMS + the four new scenario
functions via `importlib` on the explicit file path — no sys.path pollution),
then:

```
$ python3 -m pytest tests/test_prototype_smoke.py -q
=================================== FAILURES ===================================
______________ test_wild_cd_sim_unikernel_scenarios_deterministic ______________

    def test_wild_cd_sim_unikernel_scenarios_deterministic():
        """wild-5gb: unikernel scenario arms (E-H) are seeded-deterministic — two
        calls, identical dict output — and the parameterization is in place."""
        sim = load_wild_cd_sim()
>       assert sim.PARAMS["boot_min"] == 0.2, "ASSUMED Firecracker-class boot missing"
               ^^^^^^^^^^
E       AttributeError: module 'wild_cd_sim_under_test' has no attribute 'PARAMS'

tests/test_prototype_smoke.py:73: AttributeError
=========================== short test summary info ============================
FAILED tests/test_prototype_smoke.py::test_wild_cd_sim_unikernel_scenarios_deterministic
1 failed, 3 passed in 55.11s
```

## Green (step 2)

Implemented D1–D6 in `prototype/wild_cd_sim.py` — additive only, flat function
style, no classes, stdlib only:

- `PARAMS` (module-level): `boot_min=0.2` (Firecracker-class ~125 ms documented
  startup, ASSUMED, commented), `farm_slots=4` (K=4 ASSUMED), `build_min=5.0`,
  `roll_min=10.0` (D2).
- `overlap_unikernel()` — section E: same rows/keys as A, roll window collapses
  to `batches * boot_min` (20.0 → 2.0 min), overlap exposure shrinks 10×
  (198000 → 19800 failed).
- `order_unikernel()` — section F: same graphs + RNG stream as `order()`, so
  its baseline/wild rows match B exactly (7.4/5.1/2.5, 5.0/0.0/8.5); third arm
  `unikernel` = checked lockstep: break edges' true direction known pre-merge
  → `(p, c)` constraints, `lockstep_pct=0.0`. The unikernel arm's permutation
  checks draw from a separate `Random(seed*31+7)` stream so the shared stream
  (and thus B-parity) is untouched.
- `pipeline_unikernel()` — section G: gated staging queue replaced by parallel
  image builds contending on a K=4 farm slot pool (simple shared-capacity
  queue, one heap slot-free-time per slot — no discrete-event framework,
  follow-up threshold respected); near-zero boot/roll; `floors=False` zeroes
  the pre-merge rejection benefit only in the data-plane (shape) dimension;
  law dimension untouched.
- `hybrid_mix()` + `sensitivity_unikernel()` — section H: hybrid fraction axis
  f ∈ {0.0, 0.5, 1.0} as f-weighted mix of canary/unikernel arms (D4); order
  stats mixed as unikernel-subfleet-checked-lockstep × f, rest derived; floors
  on/off; prints `floors_residual` and the one-line verdict citing printed
  numbers (D3, D5).

Evidence:

```
$ python3 -m pytest tests/test_prototype_smoke.py -q
....                                                                     [100%]
4 passed in 60.41s (0:01:00)

$ python3 prototype/wild_cd_sim.py; echo "EXIT=$?"
EXIT=0
```

Sections E–H (from the recorded run, `results/unikernel-cd-sim-2026-10-14.txt`):

```
== E. unikernel rolling overlap (boot ~0.2 min, roll window collapses)
  accretion (provides grow)          {'failed': 0, 'roll_min': 2.0, 'calendar_min': 2.0, 'extra_inst': 0}
  break, uncoordinated               {'failed': 19800, 'roll_min': 2.0, 'calendar_min': 2.0, 'extra_inst': 0}
  break -> new lineage + adapter     {'failed': 0, 'roll_min': 2.0, 'calendar_min': 2.0, 'extra_inst': 20}
  break -> manual expand/contract    {'failed': 0, 'roll_min': 6.0, 'calendar_min': 1926.0, 'extra_inst': 0}

== F. deploy order: unikernel checked lockstep vs derived vs baseline
  baseline                           {'constraints': 7.4, 'lockstep_pct': 5.1, 'random_order_safe_pct': 2.5}
  wild                               {'constraints': 5.0, 'lockstep_pct': 0.0, 'random_order_safe_pct': 8.5}
  unikernel                          {'constraints': 7.4, 'lockstep_pct': 0.0, 'random_order_safe_pct': 2.8}

== G. pipeline lead time, unikernel build-farm contention (K=4 slots)
  gated                              {'median_h': 5.1, 'p95_h': 26.0, 'incidents_per_100': 9.7, 'impact_min_per_100': 1098}
  canary                             {'median_h': 0.8, 'p95_h': 15.3, 'incidents_per_100': 17.1, 'impact_min_per_100': 820}
  wild                               {'median_h': 0.8, 'p95_h': 2.4, 'incidents_per_100': 7.9, 'impact_min_per_100': 345}
  unikernel                          {'median_h': 0.5, 'p95_h': 2.0, 'incidents_per_100': 10.6, 'impact_min_per_100': 486}

== H. sensitivity, unikernel: data-plane floor logic on/off x hybrid fraction (fleet fraction unikernelized)
     columns: median_h / p95_h / incidents per 100 / impact min per 100 / order constraints / random-order safe pct
  f=0.0  floors_on   0.8/15.3/17.1/820.0/5.0/8.5
  f=0.0  floors_off  0.8/15.3/17.1/820.0/5.0/8.5
  f=0.5  floors_on   0.7/8.7/13.9/653.0/6.2/5.7
  f=0.5  floors_off  0.7/8.1/21.6/952.0/6.2/5.7
  f=1.0  floors_on   0.5/2.0/10.6/486.0/7.4/2.8
  f=1.0  floors_off  0.5/0.9/26.2/1084.0/7.4/2.8
  floors_residual = 598 impact-min/100 (advantage 334 -> -264 min/100 with floors removed; the isolated value of data-plane floor logic)
  VERDICT: lead-time gap canary-vs-unikernel narrows (p95 15.3h -> 2.0h, gap 13.3h), and removing data-plane floor logic erases the impact-minutes advantage (334 -> -264 min/100, floors_residual 598 min/100) -> hypothesis SUPPORTED
```

A–C2 byte-stability vs pre-change baseline (captured before any edit,
`md5 44bece5cd5e2d884b92652c30f1a9bf4`):

```
$ diff <(head -27 /tmp/cd_before.txt) <(head -27 /tmp/cd_after3.txt) && echo A_THRU_C2_BYTE_IDENTICAL
A_THRU_C2_BYTE_IDENTICAL
```

Section D unchanged in shape (header + 3 `bench_checker()` rows) — see caveat.

## Determinism evidence (step 2 continued) — with caveat

The brief requires "two consecutive full runs byte-identical (cmp exit 0)".
This is achievable for every seeded section, but **not for pre-existing
section D**: it is `bench_checker()`, which the module docstring labels
`MEASURED` (wall-clock timing of real code, not seeded). Making D
synthetic/seeded would change D's contract and violate D1's byte-stability
ruling, so I did not touch it. Full-run `cmp` fails only on D's three ms
values; the deterministic portion (A, B, C, C2, E, F, G, H — everything the
slice adds) is byte-identical:

```
$ python3 prototype/wild_cd_sim.py > /tmp/run1.txt && python3 prototype/wild_cd_sim.py > /tmp/run2.txt && cmp /tmp/run1.txt /tmp/run2.txt
/tmp/run1.txt /tmp/run2.txt differ: byte 2216, line 29      # line 29 = first D row
$ diff /tmp/run1.txt /tmp/run2.txt        # confined to D's MEASURED ms values
29,31c29,31
<   {'slots': 1000, 'full_ms': 0.35, ...}
<   {'slots': 10000, 'full_ms': 5.42, ...}
<   {'slots': 100000, 'full_ms': 82.45, ...}
---
>   {'slots': 1000, 'full_ms': 0.39, ...}
>   {'slots': 10000, 'full_ms': 5.69, ...}
>   {'slots': 100000, 'full_ms': 71.95, ...}
$ grep -v "_ms" /tmp/run1.txt > /tmp/r1d.txt; grep -v "_ms" /tmp/run2.txt > /tmp/r2d.txt; cmp /tmp/r1d.txt /tmp/r2d.txt && echo IDENTICAL
DETERMINISTIC_PORTION(cmp minus MEASURED D rows): exit 0, byte-identical
```

Within the new sections E–H specifically, the smoke test additionally asserts
two-call dict equality for each scenario function (green above).

## Results recording (step 3 / D6)

```
$ cp -f /tmp/run1.txt results/unikernel-cd-sim-2026-10-14.txt
$ wc -l results/unikernel-cd-sim-2026-10-14.txt
59 results/unikernel-cd-sim-2026-10-14.txt
```

`results/` contains no README/index (only `cat_sim_results.txt`,
`cd_sim_results.txt`), so per D6's conditional there is no README row to
reference the new file from — none added.

## Refactor (step 3)

None needed; flat function style preserved (no classes added). Two in-flight
fixes during green were correctness fixes, not refactors: (a) seed alignment
(`sensitivity_unikernel` uses the C seed stream so its canary row matches C's
printed canary row); (b) the separate RNG stream in `order_unikernel`
described above.

## Completion criteria checklist

- [x] `python3 -m pytest tests/test_prototype_smoke.py -q` → all pass incl.
      new test; red-first proven (output pasted above)
- [x] `python3 prototype/wild_cd_sim.py` → exit 0; A–D unchanged in shape
      (A–C2 byte-identical vs pre-change baseline); E–H present;
      `floors_residual` line printed; hypothesis verdict line printed
- [x*] two consecutive runs byte-identical — **with the D caveat**: cmp exit 0
      on the deterministic portion; the only differing bytes are pre-existing
      section D's MEASURED wall-clock ms values, whose contract (and D1's
      byte-stability ruling) forbids me from seeding. Flagging for the lead:
      if the verifier requires literal full-file cmp exit 0, that is only
      reachable by changing D (out of this slice's scope).
- [x] run output copied to `results/unikernel-cd-sim-2026-10-14.txt`
- [x] atomic commits: red test → green feat → results; no `.beads` staged; no
      files touched outside the exact list (plus this report)
- [x] no push (lead ships); bd wild-5gb left in_progress for the verify
      session per the wai-px4g evidence contract

## Follow-up threshold

Not triggered: the build farm is a simple shared-capacity slot queue (heap of
K free-times) and the hybrid mix is arithmetic weighting — no discrete-event
framework, no machinery beyond the file's existing style. Nothing expanded
beyond the slice.
