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
