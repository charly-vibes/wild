#!/usr/bin/env python3
"""Whole-graph composition certificate prototype for wild (wild-m8c).

The toy checker's per-service shape_check is pairwise; this script composes a
synthetic fleet DAG in memory, runs a per-edge scoped check for every edge's
own demand, and seals the whole-graph verdict into a tamper-evident
certificate: per-edge verdicts + component digests + a Merkle root, with an
independent verifier that re-derives everything from the presented contracts
and never trusts the certificate's own verdict fields.

MEASURED: compose_ms / verify_ms / recheck_ms bench below times the real (toy,
Python) check code. Everything else is synthetic. Values marked ASSUMED are
parameters, not data.
Stdlib only, seeded, deterministic.
"""
import hashlib, json, os, random, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wild_sim import Contract, P, shape_check

# Fleet shape. All values ASSUMED, in the style of wild_cd_sim.PARAMS.
PARAMS = {
    "seed": 20261014,                # one seed drives every random choice below
    "layers": 4,                     # DAG depth
    "services_per_layer": [6, 12, 18, 24],   # 60 services total (ASSUMED)
    "fan_out": 3,                    # providers each consumer connects to in the layer below (ASSUMED)
    "slots_per_service": 5,          # provides per service (ASSUMED)
    "demand_fraction": 0.5,          # consumer demands a seeded subset of a provider's provides (ASSUMED)
    # Bench fleet tables (ASSUMED): total sizes ~10 / 60 / 200 with the same
    # 4-layer shape, layer 0 held at ~10% of the fleet.
    "bench_layers": {10: [1, 2, 3, 4], 60: [6, 12, 18, 24], 200: [20, 40, 60, 80]},
}

# ------------------------------------------------------------------ canonical serialization
def _slot_rec(s):
    return [s.pol, s.ty, sorted(s.variants), s.closed, s.need, s.default]

def slot_json(slots):
    """Canonical JSON of a slots dict: sorted keys, frozensets as sorted lists."""
    return json.dumps({n: _slot_rec(s) for n, s in sorted(slots.items())},
                      sort_keys=True, separators=(",", ":"))

def contract_digest(c):
    """D3: component digest = sha256 over the canonical JSON of the contract's slots."""
    return hashlib.sha256(slot_json(c.slots).encode()).hexdigest()

def _h(s):
    return hashlib.sha256(s.encode()).hexdigest()

def merkle_root(leaf_hexes):
    """D3 (two-level shape, mirroring wild_cd_sim.bench_checker's tree): leaves are
    sha256 over the canonical JSON of each edge record and each component digest
    entry, computed once at certify time; root = sha256 over the SORTED leaf hexes
    joined. Sorted-join keeps the root order-independent; the two levels keep the
    incremental case cheap: a changed record only changes its own leaf, so the
    recheck diffs leaves instead of re-hashing every record."""
    return _h("".join(sorted(leaf_hexes)))

def _leaf_edge(e):
    return _h(json.dumps(e, sort_keys=True, separators=(",", ":")))

def _leaf_component(svc, digest):
    return _h(json.dumps([svc, digest], separators=(",", ":")))

# ------------------------------------------------------------------ fleet construction (D2)
def build_fleet(seed=None, layers=None, per_layer=None):
    """Synthetic fleet DAG, fully in memory. Each service is a Contract whose
    provides are out slots with globally-unique names (`svc.out<k>`), so a
    consumer's contract can carry a *pin* of each demanded provider slot under
    the same name — exactly the build-time view shape_check accretes against.
    Each edge records the consumer's demand: a seeded subset of the provider's
    provides (the names it actually uses)."""
    p = PARAMS
    seed = p["seed"] if seed is None else seed
    layers = p["layers"] if layers is None else layers
    per_layer = p["services_per_layer"] if per_layer is None else per_layer
    r = random.Random(seed)
    services, edges = {}, []
    for layer in range(layers):
        for i in range(per_layer[layer]):
            svc = f"L{layer}S{i:02d}"
            slots = {f"{svc}.out{k}": P("int64" if (seed + i + k) % 3 else "int32")
                     for k in range(p["slots_per_service"])}
            if layer > 0:
                prev = [f"L{layer - 1}S{j:02d}" for j in range(per_layer[layer - 1])]
                for prov in sorted(r.sample(prev, min(p["fan_out"], len(prev)))):
                    provs = sorted(services[prov].slots)
                    dem = sorted(r.sample(provs, max(1, int(len(provs) * p["demand_fraction"]))))
                    for n in dem:                      # pin the build-time view of each demanded slot
                        slots[n] = services[prov].slots[n]
                    edges.append({"consumer": svc, "provider": prov, "demand": frozenset(dem)})
            services[svc] = Contract(slots)
    return {"services": services, "edges": edges, "seed": seed}

# ------------------------------------------------------------------ per-edge verdict (D3)
def edge_verdict(consumer, provider, demand):
    """Scoped check over this edge's demand only. `accept`, or a labeled
    `reject: <why>` / `unknown: <why>`; `why` text comes from shape_check."""
    for n in sorted(demand):
        if n not in provider.slots and n not in consumer.slots and n not in consumer.retired:
            return f"unknown: {n} in no contract"      # demand names a slot nobody declares
    ok, why = shape_check(consumer, provider, set(demand))
    return "accept" if ok else f"reject: {why}"

def certify(fleet):
    """Compose the whole-graph certificate (D3). Returns (cert, contracts)."""
    services, edges = fleet["services"], fleet["edges"]
    components = {s: contract_digest(c) for s, c in sorted(services.items())}
    cert_edges = []
    for e in sorted(edges, key=lambda e: (e["consumer"], e["provider"])):
        v = edge_verdict(services[e["consumer"]], services[e["provider"]], e["demand"])
        cert_edges.append({"consumer": e["consumer"], "provider": e["provider"],
                           "demand": sorted(e["demand"]), "verdict": v,
                           "key": f"{e['consumer']}->{e['provider']}"})
    cert = {
        "version": 1, "kind": "composition", "seed": fleet["seed"],
        "components": components, "edges": cert_edges,
        "merkle_root": None, "verdict": None,
    }
    cert["merkle_root"] = merkle_root(
        [_leaf_edge(e) for e in cert_edges] + [_leaf_component(s, d) for s, d in components.items()])
    bad = [e["verdict"] for e in cert_edges if e["verdict"] != "accept"]
    cert["verdict"] = "accept" if not bad else bad[0]   # the refusal kind, e.g. "reject: <why>"
    return cert, services

# ------------------------------------------------------------------ independent verifier (D4)
def verify(cert, contracts):
    """Proof-carrying verification: re-derive everything from the presented
    contracts; never trust the certificate's own verdict fields. Labeled
    refusals: incomplete / tampered:<field> / edge:<key> <why>."""
    if set(cert["components"]) != set(contracts): return "incomplete"
    components = {s: contract_digest(contracts[s]) for s in sorted(contracts)}
    if components != cert["components"]: return "tampered:components"
    want_edges = sorted(cert["edges"], key=lambda e: e["key"])
    if len({e["key"] for e in want_edges}) != len(want_edges): return "incomplete"
    for e in want_edges:
        c, p = contracts.get(e["consumer"]), contracts.get(e["provider"])
        if c is None or p is None: return "incomplete"
        recheck = edge_verdict(c, p, frozenset(e["demand"]))
        if recheck != "accept": return f"edge:{e['key']} {recheck}"   # genuinely no longer composes
        if e["verdict"] != recheck: return "tampered:edges"           # verdict field disagrees with re-check
    root = merkle_root(
        [_leaf_edge(e) for e in want_edges] + [_leaf_component(s, d) for s, d in components.items()])
    if root != cert["merkle_root"]: return "tampered:merkle_root"
    return "ok"

# ------------------------------------------------------------------ tamper mutations (D5)
def tamper_component_digest(cert):
    """(a) flip one byte of one component digest."""
    t = json.loads(json.dumps(cert))
    svc = sorted(t["components"])[0]
    d = t["components"][svc]
    t["components"][svc] = ("0" if d[0] != "0" else "1") + d[1:]
    return t

def tamper_edge_verdict(cert):
    """(b) flip one edge verdict accept -> reject."""
    t = json.loads(json.dumps(cert))
    for e in t["edges"]:
        if e["verdict"] == "accept":
            e["verdict"] = "reject: tampered"
            break
    return t

# ------------------------------------------------------------------ incremental recheck (D6)
def bump_revision(fleet, svc):
    """Change one slot of one mid-layer service: an ACCRETION (out int64 -> int32,
    int32 is usable where int64 is expected), so the honest recheck still
    accepts — only the digest and the Merkle leaves move."""
    services = dict(fleet["services"])
    slots = dict(services[svc].slots)
    own = [n for n in sorted(slots) if n.startswith(svc + ".") and slots[n].ty == "int64"]
    assert own, f"{svc} has no int64 provide to accrete"
    slots[own[0]] = P("int32")
    services[svc] = Contract(slots)
    return {"services": services, "edges": fleet["edges"], "seed": fleet["seed"]}

# ------------------------------------------------------------------ bench (D6)
def bench():
    """End-to-end compose+check wall cost at ~10 / 60 / 200 services, plus the
    incremental scenario: bump one mid-layer service, re-check only its incident
    edges, and diff the Merkle leaves."""
    rows = []
    cached = None                                   # (leaf list, verdicts) from the previous size
    for n, per_layer in sorted(PARAMS["bench_layers"].items()):
        t0 = time.perf_counter()
        fleet = build_fleet(per_layer=per_layer)
        cert, contracts = certify(fleet)
        compose_ms = (time.perf_counter() - t0) * 1e3
        t0 = time.perf_counter()
        res = verify(cert, contracts)
        verify_ms = (time.perf_counter() - t0) * 1e3
        assert res == "ok", res
        leaves = ([_leaf_edge(e) for e in cert["edges"]] +
                  [_leaf_component(s, d) for s, d in cert["components"].items()])
        rows.append({"services": sum(per_layer), "edges": len(cert["edges"]),
                     "compose_ms": round(compose_ms, 2), "verify_ms": round(verify_ms, 2),
                     "verdict": cert["verdict"]})
        if n == 60: cached = (fleet, cert, contracts, leaves)
    fleet, cert, contracts, leaves = cached
    mid = sorted(s for s in fleet["services"] if s.startswith("L1") or s.startswith("L2"))[0]
    t0 = time.perf_counter()
    bumped = bump_revision(fleet, mid)
    contracts2 = dict(contracts); contracts2[mid] = bumped["services"][mid]
    # Cached recheck: only the edges incident to the bumped service are re-checked;
    # every other edge verdict stays cached.
    incident = [e for e in cert["edges"] if e["consumer"] == mid or e["provider"] == mid]
    rechecked = [edge_verdict(contracts2[e["consumer"]], contracts2[e["provider"]],
                              frozenset(e["demand"])) for e in incident]
    assert all(v == "accept" for v in rechecked), rechecked
    # Merkle diff: edge leaves are keyed on (consumer, provider, demand, verdict) —
    # all unchanged for an accreting bump — so only the bumped service's
    # component-digest leaf is re-hashed; the root is rebuilt from the sorted leaves.
    new_leaves = list(leaves)
    comp_pos = {s: len(cert["edges"]) + i for i, s in enumerate(sorted(cert["components"]))}
    new_leaves[comp_pos[mid]] = _leaf_component(mid, contract_digest(contracts2[mid]))
    changed = [i for i, (a, b) in enumerate(zip(leaves, new_leaves)) if a != b]
    root2 = merkle_root(new_leaves)
    assert root2 != cert["merkle_root"], "Merkle diff failed to move the root"
    cert2 = {**cert, "components": {**cert["components"], mid: contract_digest(contracts2[mid])},
             "merkle_root": root2}
    assert verify(cert2, contracts2) == "ok"
    recheck_ms = (time.perf_counter() - t0) * 1e3
    incremental = {"service": mid, "recheck_ms": round(recheck_ms, 2),
                   "rechecked_edges": len(incident), "edges_total": len(cert["edges"]),
                   "changed_leaves": len(changed), "leaves_total": len(leaves)}
    return {"bench": rows, "incremental": incremental}

# ------------------------------------------------------------------ edge-verdict vocabulary demo
def verdict_vocab_demo(fleet):
    """Show the reject / unknown arms of the verdict vocabulary on real fleet
    contracts, without disturbing the clean certificate."""
    services = fleet["services"]
    e = fleet["edges"][0]
    broken = dict(services[e["consumer"]].slots)     # non-accreting pin: "str" can't accept int32/int64
    pin = sorted(e["demand"])[0]
    broken[pin] = P("str")
    c2 = Contract(broken)
    reject_v = edge_verdict(c2, services[e["provider"]], e["demand"])
    unknown_v = edge_verdict(services[e["consumer"]], services[e["provider"]],
                             e["demand"] | {f"no.such.slot"})
    return {"reject": reject_v, "unknown": unknown_v}

def _show(title, rows):
    print(f"\n== {title}")
    for k, v in rows.items():
        print(f"  {k:<24} {v}")

if __name__ == "__main__":
    fleet = build_fleet()
    cert, contracts = certify(fleet)
    n_edges = len(cert["edges"])
    print(f"fleet: {len(contracts)} services, {n_edges} edges "
          f"(layers={PARAMS['layers']}, per_layer={PARAMS['services_per_layer']}, "
          f"fan_out={PARAMS['fan_out']}, seed={PARAMS['seed']})")
    print(f"certificate: version={cert['version']} kind={cert['kind']} "
          f"components={len(cert['components'])} edges={n_edges}")
    print(f"  merkle_root={cert['merkle_root'][:16]}...  verdict={cert['verdict']}")
    res = verify(cert, contracts)
    print(f"verify(clean) = {res}")
    assert res == "ok"
    _show("edge-verdict vocabulary (reject / unknown arms on real contracts)", verdict_vocab_demo(fleet))
    t1 = tamper_component_digest(cert)
    t2 = tamper_edge_verdict(cert)
    print("\n== tamper evidence (independent verifier, D5)")
    print(f"  (a) component-digest byte flip -> {verify(t1, contracts)}")
    print(f"  (b) edge verdict accept->reject -> {verify(t2, contracts)}")
    assert verify(t1, contracts) != verify(t2, contracts), "tamper labels must be distinct"
    measured = bench()
    _show("MEASURED compose+verify cost (toy Python implementation)", {
        f"{r['services']} svc / {r['edges']} edges":
            f"compose_ms={r['compose_ms']} verify_ms={r['verify_ms']} verdict={r['verdict']}"
        for r in measured["bench"]})
    inc = measured["incremental"]
    print(f"  incremental: bump {inc['service']} -> recheck_ms={inc['recheck_ms']} "
          f"rechecked_edges={inc['rechecked_edges']}/{inc['edges_total']} "
          f"(changed_leaves={inc['changed_leaves']}/{inc['leaves_total']})")
