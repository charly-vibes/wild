#!/usr/bin/env python3
"""Round 2: does composition across components hold up, autonomously and verifiably?

1. LAWS      exhaustive small-scope check that accretion is a category (reflexive, transitive)
2. THEOREM   assemblies stay well-formed when a component is replaced by an accretion of itself
3. RESOLVE   semver-range (pip-style) resolution vs lineage resolution, against hand-built truth
4. CERTIFY   proof-carrying resolution: an independent verifier re-checks a certificate; tamper tests

Everything is seeded. Ground truth is produced by the generators, not by the checker.
"""
import hashlib, itertools, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wild_sim import Contract, Slot, shape_check, sub

acc = lambda a, b: shape_check(a, b)[0]

# ------------------------------------------------------------------ 1. category laws
def laws():
    live = [Slot(pol, ty, var, cl, need)
            for pol in ("in", "out") for ty in ("int32", "int64", "str")
            for need in (("required", "optional") if pol == "in" else ("required",))
            for var in (frozenset(), frozenset("a"), frozenset("ab"))
            for cl in ((True, False) if var else (True,))]
    cs = [Contract({"x": s}) for s in live] + [Contract({})] + \
         [Contract({}, retired={"x": s}) for s in live if s.pol == "in"]
    n = len(cs); m = [[acc(a, b) for b in cs] for a in cs]
    refl = sum(not m[i][i] for i in range(n))
    trans = sum(1 for i in range(n) for j in range(n) if m[i][j]
                for k in range(n) if m[j][k] and not m[i][k])
    # restriction to a demand set is monotone: accretes(a, b) => accretes(a|D, b|D)
    restr = sum(1 for i in range(n) for j in range(n) if m[i][j]
                for D in (set(), {"x"}) if not shape_check(cs[i], cs[j], D)[0])
    return dict(states=n, triples=n ** 3, reflexivity_failures=refl,
                transitivity_violations=trans, restriction_violations=restr,
                note="per-name check; the relation is a conjunction over names, so it extends to many slots")

# ------------------------------------------------------------------ 2. substitutability theorem
NAMES = "abcd"
def rslot(r):
    u = r.random()
    ty = r.choice(["int32", "int64", "str"])
    var = r.choice([frozenset(), frozenset("a"), frozenset("ab")])
    cl = r.random() < .7
    if u < .45: return Slot("out", ty, var, cl)
    if u < .65: return Slot("in", ty, var, cl, "required")
    if u < .75: return Slot("in", ty, var, cl, "optional")
    return None

def wire_ok(o, i):
    """Can provider slot `o` feed consumer slot `i`? An open or unrestricted provider sum may emit
    values the consumer has not seen, so only a tolerant (open) consumer may be bound to it.
    (First run accepted closed consumers here and showed 21/10,171 'unsound' accretions; all 21
    involved open sums, i.e. the wiring rule, not the checker, was too lenient.)"""
    if not sub(o.ty, i.ty): return False
    if i.variants:
        if o.variants and o.closed: return o.variants <= i.variants or not i.closed
        return not i.closed
    return True

def well_formed(comps):
    for k, c in enumerate(comps):
        for n, s in c.slots.items():
            if s.pol == "in" and s.need == "required":
                if not any(j != k and comps[j].slots.get(n) and comps[j].slots[n].pol == "out"
                           and wire_ok(comps[j].slots[n], s) for j in range(len(comps))):
                    return False
    return True

def mutate(r, c):
    n = r.choice(NAMES); new = rslot(r)
    slots = dict(c.slots); ret = dict(c.retired); old = slots.get(n)
    if new is None:
        slots.pop(n, None)
        if old is not None and old.pol == "in": ret[n] = old       # a drop leaves a tombstone
    else:
        slots[n] = new; ret.pop(n, None)
    return Contract(slots, retired=ret)

def theorem(trials=30000, seed=11):
    r = random.Random(seed); st = dict(assemblies=0, global_ok=0, global_unsound=0, global_reject=0,
                                      rescued=0, scoped_unsound=0)
    while st["assemblies"] < trials:
        comps = [Contract({n: s for n in NAMES if (s := rslot(r))}) for _ in range(4)]
        if not well_formed(comps): continue
        st["assemblies"] += 1
        k = r.randrange(4); x = comps[k]; y = mutate(r, x)
        ok_after = well_formed(comps[:k] + [y] + comps[k + 1:])
        used = {n for j, c in enumerate(comps) if j != k for n, s in c.slots.items() if s.pol == "in"}
        scope = used | {n for n, s in list(x.slots.items()) + list(y.slots.items()) if s.pol == "in"} | set(x.retired) | set(y.retired)
        g, sc = acc(x, y), shape_check(x, y, scope)[0]
        if g:
            st["global_ok"] += 1; st["global_unsound"] += (not ok_after)
        else:
            st["global_reject"] += 1; st["rescued"] += (sc and ok_after)
        st["scoped_unsound"] += (sc and not ok_after)
    st["rescued_pct_of_rejections"] = round(100 * st["rescued"] / max(1, st["global_reject"]), 1)
    return st

# ------------------------------------------------------------------ 3. ecosystems
def chash(c):
    d = {"s": {n: [s.pol, s.ty, sorted(s.variants), s.closed, s.need] for n, s in sorted(c.slots.items())},
         "r": sorted(c.retired)}
    return hashlib.sha256(json.dumps(d).encode()).hexdigest()[:12]

def make_eco(r, P=30, V=8, pb=.33, mis=.5, deps=2, roots=4):
    pk = []
    for p in range(P):
        vs = [dict(c=Contract({f"s{i}": Slot("out", "int32") for i in range(3)}), brk=set(), add=set(), lab="minor", deps=[])]
        for v in range(1, V):
            prev = vs[-1]["c"]; slots = dict(prev.slots); brk, add = set(), set(); lab = "minor"
            if r.random() < pb:                                       # a break is always a real change
                n = r.choice(sorted(slots))
                if slots[n].ty == "int32" and (r.random() < .5 or len(slots) == 1):
                    slots[n] = Slot("out", "str"); brk.add(n)
                elif len(slots) > 1:
                    slots.pop(n); brk.add(n)
                if brk and r.random() > mis: lab = "major"
            elif r.random() < .6:
                n = f"n{v}"; slots[n] = Slot("out", "int32"); add.add(n)   # names are never reused
            vs.append(dict(c=Contract(slots), brk=brk, add=add, lab=lab, deps=[]))
        pk.append(vs)
    def edge(q):
        dv = min(V - 1, int(V * (1 - r.random() ** 2)))             # developers mostly build against recent versions
        names = sorted(pk[q][dv]["c"].slots)
        return (q, dv, tuple(r.sample(names, min(len(names), r.randint(1, 2)))))
    for p in range(1, P):
        for v in range(V):
            pk[p][v]["deps"] = [edge(q) for q in r.sample(range(p), min(p, deps))]
    root = [edge(q) for q in r.sample(range(P), roots)]
    return pk, root

def major(pk, q, v): return sum(pk[q][i]["lab"] == "major" for i in range(1, v + 1))
def lineage(pk, q, v):
    s = v
    while s > 0 and acc(pk[q][s - 1]["c"], pk[q][s]["c"]): s -= 1
    return s

def broken(pk, q, dv, cv, demand):
    if cv >= dv: return any(pk[q][i]["brk"] & set(demand) for i in range(dv + 1, cv + 1))
    return any(pk[q][i]["add"] & set(demand) for i in range(cv + 1, dv + 1))

def semver_resolve(pk, root, cap=20000):
    nodes = [0]
    def rec(assign, cons):
        nodes[0] += 1
        if nodes[0] > cap: return None
        todo = [q for q in cons if q not in assign]
        if not todo: return assign
        q = todo[0]
        for v in range(len(pk[q]) - 1, -1, -1):
            if all(major(pk, q, v) == major(pk, q, dv) and v >= dv for dv, _ in cons[q]):
                c2 = {k: list(x) for k, x in cons.items()}
                for (q2, dv2, dem) in pk[q][v]["deps"]: c2.setdefault(q2, []).append((dv2, dem))
                a2 = {**assign, q: v}                                  # re-check ranges on already-assigned packages
                if any(major(pk, k, a2[k]) != major(pk, k, d0) or a2[k] < d0 for k in a2 for d0, _ in c2.get(k, [])):
                    continue
                got = rec(a2, c2)
                if got is not None: return got
        return None
    cons = {}
    for (q, dv, dem) in root: cons.setdefault(q, []).append((dv, dem))
    return rec({}, cons), nodes[0]

def semver_edges(pk, root, assign):
    es = [(q, dv, dem, assign[q]) for (q, dv, dem) in root]
    for p, v in assign.items(): es += [(q, dv, dem, assign[q]) for (q, dv, dem) in pk[p][v]["deps"] if q in assign]
    return es

def semver_dup(pk, root):
    """npm-style: every consumer gets the newest release its caret range allows; duplicates allowed."""
    work, chosen, es = list(root), set(), []
    while work:
        q, dv, dem = work.pop()
        v = max(i for i in range(len(pk[q])) if major(pk, q, i) == major(pk, q, dv) and i >= dv)
        es.append((q, dv, dem, v))
        if (q, v) not in chosen: chosen.add((q, v)); work += list(pk[q][v]["deps"])
    return es, chosen

def wild_resolve(pk, root):
    """Newest revision per (package, lineage); consumers processed before providers. No search."""
    P = len(pk); need = {}; sel = {}; edges = []
    def want(q, dv, dem, who):
        need.setdefault((q, lineage(pk, q, dv)), []).append((dv, dem, who))
    for (q, dv, dem) in root: want(q, dv, dem, "root")
    for p in range(P - 1, -1, -1):
        for (q_, l), lst in [(k, v) for k, v in need.items() if k[0] == p]:
            sel[(p, l)] = max(v for v in range(len(pk[p])) if lineage(pk, p, v) == l)
            for v in {sel[(p, l)]}:
                for (q, dv, dem) in pk[p][v]["deps"]: want(q, dv, dem, (p, v))
    for (q, l), lst in need.items():
        for dv, dem, who in lst: edges.append((q, dv, dem, sel[(q, l)], who, l))
    return sel, need, edges

def dedupe(pk, sel, need):
    copies = 0
    for q in {k[0] for k in sel}:
        ls = sorted(l for (qq, l) in sel if qq == q); keep = []
        for l in ls:                                                  # try to merge older lineages into newer
            tgt = next((m for m in reversed(ls) if m > l and all(
                shape_check(pk[q][dv]["c"], pk[q][sel[(q, m)]]["c"], dem)[0] for dv, dem, _ in need[(q, l)])), None)
            if tgt is None: keep.append(l)
        copies += len(keep)
    return copies

def resolve_study(mis, n=200, seed=5, pb=.33):
    r = random.Random(seed); S = dict(conflict=0, false_ok=0, nodes=0, edges=0, brk_edges=0)
    A = dict(broken_edges=0, copies=0, copies_deduped=0, pkgs=0, checker_vs_truth_mismatch=0)
    D = dict(broken=0, edges=0, copies=0, pkgs=0, projects_with_break=0)
    for _ in range(n):
        pk, root = make_eco(r, mis=mis, pb=pb)
        for q in range(len(pk)):                                      # checker must agree with generator truth
            for v in range(1, len(pk[q])):
                A["checker_vs_truth_mismatch"] += (acc(pk[q][v - 1]["c"], pk[q][v]["c"]) == bool(pk[q][v]["brk"]))
        sol, nodes = semver_resolve(pk, root); S["nodes"] += nodes
        if sol is None: S["conflict"] += 1
        else:
            es = semver_edges(pk, root, sol); b = sum(broken(pk, q, dv, cv, dem) for q, dv, dem, cv in es)
            S["false_ok"] += (b > 0); S["brk_edges"] += b; S["edges"] += len(es)
        es2, ch2 = semver_dup(pk, root); b2 = sum(broken(pk, q, dv, cv, dem) for q, dv, dem, cv in es2)
        D["broken"] += b2; D["edges"] += len(es2); D["copies"] += len(ch2); D["projects_with_break"] += (b2 > 0)
        D["pkgs"] += len({q for q, _ in ch2})
        sel, need, edges = wild_resolve(pk, root)
        A["broken_edges"] += sum(broken(pk, q, dv, cv, dem) for q, dv, dem, cv, _, _ in edges)
        A["pkgs"] += len({k[0] for k in sel}); A["copies"] += len(sel); A["copies_deduped"] += dedupe(pk, sel, need)
    return dict(semver=dict(no_solution_pct=round(100 * S["conflict"] / n, 1),
                            solved_but_broken_pct=round(100 * S["false_ok"] / n, 1),
                            broken_edge_pct=round(100 * S["brk_edges"] / max(1, S["edges"]), 1),
                            avg_search_nodes=round(S["nodes"] / n, 1)),
                semver_duplicates_allowed=dict(solved_but_broken_pct=round(100 * D["projects_with_break"] / n, 1),
                            broken_edge_pct=round(100 * D["broken"] / max(1, D["edges"]), 1),
                            copies_per_pkg=round(D["copies"] / D["pkgs"], 2)),
                wild=dict(no_solution_pct=0.0, broken_edges=A["broken_edges"],
                             copies_per_pkg=round(A["copies"] / A["pkgs"], 2),
                             copies_per_pkg_after_scoped_merge=round(A["copies_deduped"] / A["pkgs"], 2),
                             checker_vs_generator_disagreements=A["checker_vs_truth_mismatch"], of_transitions=n * 7 * 30))

# ------------------------------------------------------------------ 4. certificates
def certify(pk, sel, edges):
    reg = {chash(pk[q][v]["c"]): pk[q][v]["c"] for q in range(len(pk)) for v in range(len(pk[q]))}
    cert = [dict(dev=chash(pk[q][dv]["c"]), prov=chash(pk[q][cv]["c"]), demand=list(dem), key=(q, dv, tuple(dem), str(who)))
            for q, dv, dem, cv, who, _ in edges]
    return reg, cert

def verify(reg, cert, expected):
    if {c["key"] for c in cert} != expected: return "incomplete"
    for b in cert:
        d, p = reg.get(b["dev"]), reg.get(b["prov"])
        if d is None or p is None or chash(d) != b["dev"] or chash(p) != b["prov"]: return "bad_hash"
        if not shape_check(d, p, set(b["demand"]))[0]: return "incompatible"
    return "ok"

def cert_study(n=150, seed=9):
    r = random.Random(seed); out = dict(valid_accepted=0, n=0, bindings=0, verify_ms=0.0,
        swap_total=0, swap_false_accept=0, swap_rejected=0, swap_ok_still=0,
        corrupt_total=0, corrupt_rejected=0, drop_total=0, drop_rejected=0)
    for _ in range(n):
        pk, root = make_eco(r, mis=.5)
        sel, need, edges = wild_resolve(pk, root); reg, cert = certify(pk, sel, edges)
        expected = {c["key"] for c in cert}; out["n"] += 1; out["bindings"] += len(cert)
        t = time.perf_counter(); out["valid_accepted"] += verify(reg, cert, expected) == "ok"
        out["verify_ms"] += (time.perf_counter() - t) * 1e3
        if not cert: continue
        for _ in range(5):
            i = r.randrange(len(cert)); q, dv, dem, _, _ = edges[i][0], edges[i][1], edges[i][2], edges[i][3], 0
            alt = r.randrange(len(pk[q])); c2 = [dict(b) for b in cert]; c2[i]["prov"] = chash(pk[q][alt]["c"])
            res = verify(reg, c2, expected); truth_ok = not broken(pk, q, dv, alt, dem)
            out["swap_total"] += 1
            if res == "ok" and not truth_ok: out["swap_false_accept"] += 1
            out["swap_rejected"] += res != "ok"; out["swap_ok_still"] += (res == "ok")
            c3 = [dict(b) for b in cert]; h = c3[i]["prov"]; c3[i]["prov"] = h[:-1] + ("0" if h[-1] != "0" else "1")
            out["corrupt_total"] += 1; out["corrupt_rejected"] += verify(reg, c3, expected) != "ok"
            c4 = [b for j, b in enumerate(cert) if j != i]
            out["drop_total"] += 1; out["drop_rejected"] += verify(reg, c4, expected) != "ok"
    out["avg_bindings"] = round(out["bindings"] / out["n"], 1); out["avg_verify_ms"] = round(out["verify_ms"] / out["n"], 3)
    del out["verify_ms"]
    return out

def show(t, o):
    print(f"\n== {t}")
    for k, v in (o.items() if isinstance(o, dict) else enumerate(o)): print(f"  {k:<30} {v}")

if __name__ == "__main__":
    show("1. category laws (exhaustive, small scope)", laws())
    show("2. substitutability theorem (30,000 random assemblies)", theorem())
    for m in (0.0, 0.25, 0.5, 0.75):
        show(f"3. resolution, share of breaking releases mislabelled as non-major = {m}", resolve_study(m))
    for pbv in (0.05, 0.10):
        show(f"3b. lower break rate: {pbv} of releases break, 30% of those mislabelled", resolve_study(.3, pb=pbv))
    show("4. certificates and tamper tests", cert_study())
