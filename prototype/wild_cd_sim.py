#!/usr/bin/env python3
"""Continuous-deployment simulations for wild. Stdlib only, seeded.

MEASURED: bench_checker() times the real (toy, Python) checker code.
MODELLED: everything else. Durations and probabilities marked ASSUMED are
parameters, not data; read results as sensitivity, not prediction.
Time unit: working minutes (a working day = 480 min).
"""
import graphlib, hashlib, heapq, math, os, random, statistics as st, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wild_sim import Contract, P, I, shape_check, slot_ok

def pct(xs, p): xs = sorted(xs); return xs[min(len(xs) - 1, int(p * len(xs)))]

# wild-5gb unikernel parameterization. All values ASSUMED, in working minutes.
PARAMS = {
    # Firecracker-class microVM boot is ~125 ms documented startup (~0.004
    # working minutes); rounded up to 0.2 min to also cover image fetch and
    # first-request warmup. Boot/roll are near-zero, so the roll window
    # collapses: batches step at boot time, not boot + drain.
    "boot_min": 0.2,
    # The gated shared staging queue is replaced by parallel image builds
    # contending on a build-farm resource pool: back pressure moves from the
    # shared staging queue to the farm (K slots, simple shared-capacity model
    # like pipeline()'s `free` variable, one heap entry per slot).
    "farm_slots": 4,       # K=4 build slots (ASSUMED)
    "build_min": 5.0,      # mean per-image build duration (lognormal, s=.6)
    "roll_min": 10.0,      # mean full roll: canary + full roll collapse into one near-instant boot roll
}

# ---------------------------------------------------------------- E: unikernel rolling deploy overlap
def overlap_unikernel(instances=20, batch=2, rps=50, affected=0.3):
    """Same rolling overlap as overlap(), but new instances boot in ~0.2 min,
    so the roll window is batches * boot_min and the overlap exposure (the
    number of requests served against a not-yet-ready instance) shrinks with
    it. Same four rows and keys as A, for direct comparison."""
    boot = PARAMS["boot_min"]
    batches = math.ceil(instances / batch)
    reqs = [instances * rps * 60 * boot for _ in range(batches)]
    newfrac = [min(1, (b + 1) * batch / instances) for b in range(batches)]
    unc = sum(r * f * affected for r, f in zip(reqs, newfrac))
    roll = batches * boot
    return {
        "accretion (provides grow)":         dict(failed=0, roll_min=roll, calendar_min=roll, extra_inst=0),
        "break, uncoordinated":              dict(failed=round(unc), roll_min=roll, calendar_min=roll, extra_inst=0),
        "break -> new lineage + adapter":    dict(failed=0, roll_min=roll, calendar_min=roll, extra_inst=instances),
        "break -> manual expand/contract":   dict(failed=0, roll_min=3 * roll, calendar_min=3 * roll + 2 * 960, extra_inst=0),
    }

# ---------------------------------------------------------------- F: deploy order, checked lockstep vs derived vs baseline
def order_unikernel(n=12, p_edge=0.25, p_floor=0.3, p_break=0.15, trials=3000, seed=3):
    """Deploy order for the unikernel arm. Same graphs and the same RNG stream
    as order() (the baseline/wild rows therefore match B exactly). The
    unikernel subfleet deploys in CHECKED lockstep: the floor check runs
    pre-merge, so each break edge's true direction (consumer c depends on
    provider p) is known and becomes an enforced ordering constraint instead
    of an unknowable coin flip between the two directions."""
    r = random.Random(seed)
    rp = random.Random(seed * 31 + 7)   # separate stream: the unikernel arm's permutation checks must not shift the shared stream (keeps baseline/wild rows identical to B)
    out = {k: dict(cons=[], lock=0, safe=[]) for k in ("baseline", "wild", "unikernel")}
    for _ in range(trials):
        edges = [(c, p) for c in range(n) for p in range(c + 1, n) if r.random() < p_edge]  # c depends on p
        cons = {k: [] for k in out}
        for c, p in edges:
            u = r.random()
            if u < p_break:                              # incompatible change on this edge
                cons["baseline"].append((p, c) if r.random() < .5 else (c, p))  # provider-first or consumer-first, unknowable without contracts
                cons["unikernel"].append((p, c))         # floor check reveals the true direction pre-merge
                # wild: moved to a new lineage, no ordering constraint
            elif u < p_break + p_floor:                  # consumer starts using a new provide
                for k in out: cons[k].append((p, c))
        for k in out:
            ts = graphlib.TopologicalSorter()
            for a, b in cons[k]: ts.add(b, a)           # a must deploy before b
            try: ts.prepare(); cyc = False
            except graphlib.CycleError: cyc = True
            out[k]["cons"].append(len(cons[k])); out[k]["lock"] += cyc
            if cyc: out[k]["safe"].append(0.0); continue
            ok = 0
            rr = rp if k == "unikernel" else r           # unikernel perms come from the separate stream (see rp above)
            for _ in range(60):
                perm = list(range(n)); rr.shuffle(perm); pos = {s: i for i, s in enumerate(perm)}
                ok += all(pos[a] < pos[b] for a, b in cons[k])
            out[k]["safe"].append(ok / 60)
    return {k: dict(constraints=round(st.mean(v["cons"]), 1), lockstep_pct=round(100 * v["lock"] / trials, 1),
                    random_order_safe_pct=round(100 * st.mean(v["safe"]), 1)) for k, v in out.items()}

# ---------------------------------------------------------------- G: pipeline with build-farm contention
def pipeline_unikernel(n=4000, shape=.15, law=.05, undecl=.08, qc=.4, lam=1.6, seed=1, floors=True):
    """The C pipeline under the unikernel parameterization. The gated shared
    staging queue is replaced by parallel image builds contending on a farm
    of PARAMS['farm_slots'] slots (back pressure at the farm, not a staging
    server); boot and roll are near-zero, so canary and full roll collapse
    into a single near-instant boot roll. floors=False zeroes the pre-merge
    rejection benefit of the data-plane floor logic (shape-typed storage
    breaks then escape to production); the law dimension is untouched, so the
    residual difference vs floors=True isolates the floors' value."""
    r = random.Random(seed)
    L = lambda m, s=.6: r.lognormvariate(math.log(m), s)
    t, jobs, ch = 0.0, [], {}
    for i in range(n):
        t += r.expovariate(lam / 60)
        u = r.random()
        typ = "shape" if u < shape else "law" if u < shape + law else "undecl" if u < shape + law + undecl else "safe"
        ch[i] = dict(arr=t, typ=typ, esc=False)
        heapq.heappush(jobs, (t + L(10), i))
    farm = [0.0] * PARAMS["farm_slots"]   # per-slot free times; jobs contend for the earliest free slot
    lead, inc, impact = [], 0, 0.0
    while jobs:
        ready, i = heapq.heappop(jobs); c = ch[i]; typ = c["typ"]
        k = min(range(len(farm)), key=farm.__getitem__)    # first free farm slot (K=4 parallel builds)
        start = max(ready, farm[k]); farm[k] = start + L(PARAMS["build_min"]); ready = farm[k]
        retry = None
        if typ == "shape":
            if floors: retry, typ = L(60), "safe"          # rejected pre-merge by data-plane floors; new lineage + adapter, nobody waits
            # floors removed: the data-plane rejection benefit is zeroed — the
            # incompatible change deploys and escapes as an incident below
        elif typ == "law" and r.random() < .5: retry, typ = L(30), "safe"   # law dimension unchanged by floors removal
        if retry is not None:
            ch[i]["typ"] = typ; heapq.heappush(jobs, (ready + retry, i)); continue
        ready += L(PARAMS["roll_min"])                     # one near-instant boot roll, no canary phase
        lead.append(ready - c["arr"])
        if typ != "safe":                                  # escaped defect, data-plane concentrated
            inc += 1
            if r.random() < qc: impact += L(15) * .05      # 5%-traffic catch, instant image rollback
            else: impact += L(60)                          # full-traffic data-plane incident
    return dict(median_h=round(st.median(lead) / 60, 1), p95_h=round(pct(lead, .95) / 60, 1),
                incidents_per_100=round(100 * inc / n, 1), impact_min_per_100=round(100 * impact / n))

def hybrid_mix(f, canary, unik):
    """D4 hybrid fleets: floor ordering does NOT collapse — the unikernel
    subfleet uses checked lockstep (floor rejections intact), the rest keeps
    derived ordering. Modelled as an f-weighted mix of the F/pipeline arms.
    order_mix mixes the F arms' order statistics the same way."""
    return {k: round((1 - f) * canary[k] + f * unik[k], 1)
            for k in ("median_h", "p95_h", "incidents_per_100", "impact_min_per_100")}

# ---------------------------------------------------------------- H: sensitivity, data-plane floors on/off x hybrid fraction
def sensitivity_unikernel(fracs=(0.0, 0.5, 1.0)):
    """Sensitivity over the hybrid-fleet axis (fleet fraction unikernelized)
    with data-plane floor logic on/off. floors_residual isolates the value of
    the data-plane floor logic: how much of the unikernel arm's impact-minutes
    advantage over canary survives once the floor rejections are zeroed."""
    canary = pipeline("canary")                       # seed 1, same stream as C's arms
    on = pipeline_unikernel(floors=True)
    off = pipeline_unikernel(floors=False)
    order_arms = order_unikernel()                    # seed 3, same stream as B/F
    rows = {}
    for f in fracs:
        o = {k: round(f * order_arms["unikernel"][k] + (1 - f) * order_arms["wild"][k], 1)  # unikernel subfleet checked lockstep, rest derived
             for k in ("constraints", "random_order_safe_pct")}
        rows[f] = {
            "floors_on":  dict(hybrid_mix(f, canary, on),  order_constraints=o["constraints"], order_safe_pct=o["random_order_safe_pct"]),
            "floors_off": dict(hybrid_mix(f, canary, off), order_constraints=o["constraints"], order_safe_pct=o["random_order_safe_pct"]),
        }
    gap_p95 = round(canary["p95_h"] - on["p95_h"], 1)
    adv_on = round(canary["impact_min_per_100"] - on["impact_min_per_100"], 1)
    adv_off = round(canary["impact_min_per_100"] - off["impact_min_per_100"], 1)
    floors_residual = round(adv_on - adv_off, 1)
    narrows = gap_p95 > 0
    most = adv_on > 0 and floors_residual >= 0.5 * adv_on
    verdict = (
        f"VERDICT: lead-time gap canary-vs-unikernel narrows (p95 {canary['p95_h']}h -> {on['p95_h']}h, "
        f"gap {gap_p95}h)" if narrows else
        f"VERDICT: lead-time gap does NOT narrow (p95 {canary['p95_h']}h -> {on['p95_h']}h)"
    ) + (
        f", and removing data-plane floor logic {'erases' if most else 'does not erase most of'} the "
        f"impact-minutes advantage ({adv_on} -> {adv_off} min/100, floors_residual {floors_residual} min/100) "
        f"-> hypothesis {'SUPPORTED' if narrows and most else 'NOT SUPPORTED'}"
    )
    return dict(rows=rows, floors_residual=floors_residual, adv_on=adv_on, adv_off=adv_off, verdict=verdict)


# ---------------------------------------------------------------- A: rolling deploy overlap
def overlap(instances=20, batch=2, batch_min=2.0, rps=50, affected=0.3):
    """Old consumers call a provider while it rolls. Requests failing in the overlap window."""
    batches = math.ceil(instances / batch)
    reqs = [instances * rps * 60 * batch_min for _ in range(batches)]
    newfrac = [min(1, (b + 1) * batch / instances) for b in range(batches)]
    unc = sum(r * f * affected for r, f in zip(reqs, newfrac))
    roll = batches * batch_min
    return {
        "accretion (provides grow)":         dict(failed=0, roll_min=roll, calendar_min=roll, extra_inst=0),
        "break, uncoordinated":              dict(failed=round(unc), roll_min=roll, calendar_min=roll, extra_inst=0),
        "break -> new lineage + adapter":    dict(failed=0, roll_min=roll, calendar_min=roll, extra_inst=instances),  # old lineage stays until demand is zero
        "break -> manual expand/contract":   dict(failed=0, roll_min=3 * roll, calendar_min=3 * roll + 2 * 960, extra_inst=0),  # ASSUMED: 2 working days per consumer step
    }

# ---------------------------------------------------------------- B: deploy order constraints
def order(n=12, p_edge=0.25, p_floor=0.3, p_break=0.15, trials=3000, seed=3):
    r = random.Random(seed)
    out = {"baseline": dict(cons=[], lock=0, safe=[]), "wild": dict(cons=[], lock=0, safe=[])}
    for _ in range(trials):
        edges = [(c, p) for c in range(n) for p in range(c + 1, n) if r.random() < p_edge]  # c depends on p
        cons = {"baseline": [], "wild": []}
        for c, p in edges:
            u = r.random()
            if u < p_break:                              # incompatible change on this edge
                cons["baseline"].append((p, c) if r.random() < .5 else (c, p))  # provider-first or consumer-first, unknowable without contracts
                # wild: moved to a new lineage, no ordering constraint
            elif u < p_break + p_floor:                  # consumer starts using a new provide
                cons["baseline"].append((p, c)); cons["wild"].append((p, c))
        for k in out:
            ts = graphlib.TopologicalSorter()
            for a, b in cons[k]: ts.add(b, a)           # a must deploy before b
            try: ts.prepare(); cyc = False
            except graphlib.CycleError: cyc = True
            out[k]["cons"].append(len(cons[k])); out[k]["lock"] += cyc
            if cyc: out[k]["safe"].append(0.0); continue
            ok = 0
            for _ in range(60):
                perm = list(range(n)); r.shuffle(perm); pos = {s: i for i, s in enumerate(perm)}
                ok += all(pos[a] < pos[b] for a, b in cons[k])
            out[k]["safe"].append(ok / 60)
    return {k: dict(constraints=round(st.mean(v["cons"]), 1), lockstep_pct=round(100 * v["lock"] / trials, 1),
                    random_order_safe_pct=round(100 * st.mean(v["safe"]), 1)) for k, v in out.items()}

# ---------------------------------------------------------------- C: pipeline lead time
def pipeline(kind, n=4000, shape=.15, law=.05, undecl=.08, qc=.4, lam=1.6, seed=1):
    """kind: gated (shared staging), canary (independent CD + semver ranges), wild (tiered)."""
    r = random.Random(seed)
    L = lambda m, s=.6: r.lognormvariate(math.log(m), s)
    t, jobs, ch = 0.0, [], {}
    for i in range(n):
        t += r.expovariate(lam / 60)
        u = r.random()
        typ = "shape" if u < shape else "law" if u < shape + law else "undecl" if u < shape + law + undecl else "safe"
        ch[i] = dict(arr=t, typ=typ, esc=False)
        heapq.heappush(jobs, (t + L(10), i))
    free, lead, inc, impact = 0.0, [], 0, 0.0
    while jobs:
        ready, i = heapq.heappop(jobs); c = ch[i]; typ = c["typ"]
        if kind == "gated":
            start = max(ready, free); free = start + L(25); ready = free   # one shared staging server
        elif kind == "wild":
            ready += L(5) if typ != "safe" else 0.2                        # tiers 0-2: pure, per-service, no shared queue
        retry = None
        if typ == "shape":
            if kind == "wild": retry, typ = L(60), "safe"               # rejected pre-merge; new lineage + adapter, nobody waits
            elif r.random() < .6: retry, typ = L(960), "safe"               # declared major: coordinate with dependents, ASSUMED 2 days
            elif kind == "gated" and r.random() < .7: retry, typ = L(120), "safe"
        elif typ == "law":
            if kind == "wild" or r.random() < (.65 if kind == "gated" else .5): retry, typ = L(30), "safe"
        elif typ == "undecl" and kind == "gated" and r.random() < .2: retry, typ = L(120), "safe"
        if retry is not None:
            ch[i]["typ"] = typ; heapq.heappush(jobs, (ready + retry, i)); continue
        deploy = L(20) if kind == "gated" else L(15) + L(15)               # full roll vs canary + roll
        lead.append(ready + deploy - c["arr"])
        if typ != "safe":                                                   # escaped defect
            inc += 1
            if kind != "gated" and r.random() < qc: impact += L(15) * .05   # canary catches it at ~5% traffic
            else: impact += L(90 if kind == "gated" else 60)                # full-traffic incident
    return dict(median_h=round(st.median(lead) / 60, 1), p95_h=round(pct(lead, .95) / 60, 1),
                incidents_per_100=round(100 * inc / n, 1), impact_min_per_100=round(100 * impact / n))

# ---------------------------------------------------------------- D: measured checker cost
def bench_checker(sizes=(1_000, 10_000, 100_000)):
    rows = []
    for n in sizes:
        old = Contract({f"s{i}": P("int32") if i % 2 else I("int32") for i in range(n)})
        new = Contract(dict(old.slots)); new.slots["s0"] = I("int64")     # one input widened: an accretion
        t0 = time.perf_counter(); ok = shape_check(old, new)[0]; full = time.perf_counter() - t0
        # two-level Merkle: 64-slot buckets, hashes computed once at publish and stored
        def tree(c):
            ks = sorted(c.slots); bs = [ks[i:i + 64] for i in range(0, len(ks), 64)]
            hs = [hashlib.sha256("".join(f"{k}{c.slots[k]}" for k in b).encode()).hexdigest() for b in bs]
            return bs, hs, hashlib.sha256("".join(hs).encode()).hexdigest()
        (bo, ho, ro), (bn, hn, rn) = tree(old), tree(new)
        t0 = time.perf_counter()
        changed = [k for b, a, z in zip(bo, ho, hn) if a != z for k in b] if ro != rn else []
        okm = all(slot_ok(old.slots[k], new.slots[k])[0] for k in changed)
        merkle = time.perf_counter() - t0
        cache = {(ro, rn): okm}
        t0 = time.perf_counter(); cache[(ro, rn)]; hit = time.perf_counter() - t0
        rows.append(dict(slots=n, full_ms=round(full * 1e3, 2), merkle_ms=round(merkle * 1e3, 3),
                         cache_hit_ms=round(hit * 1e3, 4), same_verdict=(ok == okm)))
    return rows

def show(title, obj):
    print(f"\n== {title}")
    if isinstance(obj, dict):
        for k, v in obj.items(): print(f"  {k:<34} {v}")
    else:
        for v in obj: print(" ", v)

if __name__ == "__main__":
    show("A. rolling deploy overlap (20 instances, batch 2, 30% of calls hit the changed slot)", overlap())
    show("B. deploy-order constraints (12 services, 3000 random graphs)", order())
    show("C. pipeline lead time, working hours (12.8 changes/day, 20 services)",
         {k: pipeline(k) for k in ("gated", "canary", "wild")})
    sens = {}
    for sh in (.05, .15, .30):
        for q in (.2, .4, .7):
            sens[f"shape={sh:.2f} canary_catch={q:.1f}"] = {k: pipeline(k, shape=sh, qc=q) for k in ("canary", "wild")}
    print("\n== C2. sensitivity (canary vs wild): median_h / p95_h / incidents per 100 / impact min per 100")
    for k, v in sens.items():
        f = lambda m: f"{m['median_h']}/{m['p95_h']}/{m['incidents_per_100']}/{m['impact_min_per_100']}"
        print(f"  {k:<32} canary {f(v['canary']):<22} wild {f(v['wild'])}")
    show("D. MEASURED checker cost (toy Python implementation)", bench_checker())
    show("E. unikernel rolling overlap (boot ~0.2 min, roll window collapses)", overlap_unikernel())
    show("F. deploy order: unikernel checked lockstep vs derived vs baseline", order_unikernel())
    show("G. pipeline lead time, unikernel build-farm contention (K=4 slots)",
         {**{k: pipeline(k) for k in ("gated", "canary", "wild")}, "unikernel": pipeline_unikernel()})
    h = sensitivity_unikernel()
    print("\n== H. sensitivity, unikernel: data-plane floor logic on/off x hybrid fraction (fleet fraction unikernelized)")
    print("     columns: median_h / p95_h / incidents per 100 / impact min per 100 / order constraints / random-order safe pct")
    for f, row in h["rows"].items():
        for arm in ("floors_on", "floors_off"):
            r_ = row[arm]
            print(f"  f={f:<4} {arm:<11} {r_['median_h']}/{r_['p95_h']}/{r_['incidents_per_100']}/"
                  f"{r_['impact_min_per_100']}/{r_['order_constraints']}/{r_['order_safe_pct']}")
    print(f"  floors_residual = {h['floors_residual']} impact-min/100 "
          f"(advantage {h['adv_on']} -> {h['adv_off']} min/100 with floors removed; the isolated value of data-plane floor logic)")
    print(f"  {h['verdict']}")
