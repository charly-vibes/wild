#!/usr/bin/env python3
"""Purpose: frozen research experiment for the semantic-composition case
    matrix C03-C11/C16 across the H0 flat, H1 authored-wrapper and H2
    first-class-composite representations (beads wild-9co.3), under
    protocol revision 2.

Responsibilities: define export/input mappings, explicit shared-instance
    identity, complete closure expansion and evidence commitments; resolve
    each representation arm to a canonical flat closure; check every closure
    with one shared oracle (binding completeness, singleton identity,
    relation endpoints) under the same frozen traversal bound; run the C03,
    C04, C05, C06, C07, C09a-e, C10, C11 and C16 fixtures as negative and
    positive variants against that same oracle; and emit one JSON report
    with per-arm canonical digests, verdicts and unknowns.

Rationale: this is an experiment record, not a runtime claim. H0/H1/H2 are
    representation arms compared only on whether they preserve the same
    canonical closure and the same verdict under the shared oracle; H2
    entry does not depend on H1 showing a benefit. Singleton conflicts are
    detected after expansion from the explicit mapping, so contract-hash
    equality cannot merge actual instances. No v1 runtime, unbounded
    liveness, cross-language conformance, or category-theoretic proof is
    claimed.
"""
from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import dataclass, field

# --- Frozen scope -----------------------------------------------------------

ORACLE_ID = "closure-oracle-v1"
POLICY_REV = 2                  # current evidence-authority revision
TRAVERSAL_BOUND = 32            # frozen expansion work bound (all arms)
SHARED_KEY = "storage_shared"   # the one shared singleton in the domain

LAWS = (
    {"id": "L1", "kind": "safety",
     "statement": "every open demand is bound to a live provider endpoint"},
    {"id": "L2", "kind": "identity",
     "statement": "a shared singleton key resolves to exactly one real instance"},
)


def digest(obj) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


ORACLE_LAWS_DIGEST = digest(LAWS)

# --- Closure model ----------------------------------------------------------
#
# A flat closure (piece) carries:
#   instances: {iid: {"kind", "artifact", "singleton" or None}}
#   bindings:  [[consumer_iid, input, provider_iid, output], ...]
#   demands:   {name: {"input": [consumer_iid, input],
#                      "singleton": key or None}}      (open inputs)
#   exports:   {name: {"output": [provider_iid, output]}} (public outputs)
#   relations: [[a_iid, op, b_iid], ...]                  (internal relations)


def piece(instances, bindings, demands, exports, relations=()):
    return {
        "instances": instances,
        "bindings": [list(b) for b in bindings],
        "demands": demands,
        "exports": exports,
        "relations": [list(r) for r in relations],
    }


EMPTY_PIECE = piece({}, [], {}, {})


@dataclass
class Expansion:
    closure: dict | None
    errors: list = field(default_factory=list)
    singleton_conflicts: list = field(default_factory=list)
    visited_once: bool = True
    traversed: int = 0


def resolve(node):
    """Representation dispatch; always returns (piece, errors).

    H0 flat      {"piece": <piece>}
    H1 wrapper   {"wrapper": {"internals": node, "contract": {...},
                              "exports_map": {b: i}, "demands_map": {b: i},
                              "hide_instances": [iid, ...]}}
    H2 composite {"children": {name: node}, "wiring": ..., "imports": ...,
                  "demands": ..., "exports": ..., "shared": ...}
    """
    if "piece" in node:
        return dict(node["piece"]), []
    if "wrapper" in node:
        w = node["wrapper"]
        inner, ierr = resolve(w["internals"])
        if ierr:
            return None, list(ierr)
        try:
            exports = {b: {"output": list(inner["exports"][i]["output"])}
                       for b, i in w["exports_map"].items()}
        except KeyError as missing:
            return None, [f"contract_drift:{missing}"]
        demands = {}
        for b, spec in w["demands_map"].items():
            d = dict(inner["demands"][spec["demand"]])
            if spec.get("singleton"):
                d["singleton"] = spec["singleton"]
            demands[b] = d
        hidden = set(w.get("hide_instances", []))
        out = piece({k: v for k, v in inner["instances"].items()
                     if k not in hidden},
                    inner["bindings"], demands, exports, inner["relations"])
        return out, []
    if "children" in node:
        exp = compose(node)
        return exp.closure, list(exp.errors)
    raise ValueError("unrecognized node")


def compose(spec):
    """Merge resolved child closures under export/input mappings.

    spec keys:
      parts     {name: node}                 sub-representations
      wiring    [[p, demand, p2, export]]    internal supply links
      imports   {f"{p}.{demand}": {"iid", "output"}}
                                             explicit input mappings
      demands   {boundary: [p, demand]}      boundary-demanded inputs
      exports   {boundary: [p, export]}      boundary-public outputs
      shared    {key: iid}                   explicit shared-instance identity
    """
    errors: list[str] = []
    instances: dict = {}
    singleton_owner: dict[str, str] = {}
    singleton_conflicts: list = []
    bindings: list[list] = []
    demands: dict = {}
    exports_out: dict = {}
    relations: list[list] = []
    wired: set = set()

    # 1. merge instances; concrete-id collisions are input errors (C09d)
    for name, node in (spec.get("parts") or spec.get("children") or {}).items():
        p, perr = resolve(node)
        if perr:
            return Expansion(None, errors=sorted(set(perr)))
        if p is None:
            return Expansion(None, errors=[f"empty_child:{name}"])
        for iid, inst in p["instances"].items():
            if iid in instances:
                errors.append(f"instance_collision:{iid}")
            else:
                instances[iid] = inst
        bindings.extend(p["bindings"])
        relations.extend(p["relations"])
        for dname, d in p["demands"].items():
            demands[(name, dname)] = d
        for ename, e in p["exports"].items():
            exports_out[(name, ename)] = e
        if len(instances) > TRAVERSAL_BOUND:
            return Expansion(None, errors=["traversal_bound_exceeded"])

    # 2. wiring links: part demand supplied by another part's export
    for p, d, p2, e in spec.get("wiring", []):
        wired.add((p, d))
        consumer = demands.get((p, d), {}).get("input")
        provider = exports_out.get((p2, e), {}).get("output")
        if consumer is None or provider is None:
            errors.append(f"dangling_endpoint:{p}.{d}->{p2}.{e}")
            continue
        bindings.append([consumer[0], consumer[1], provider[0], provider[1]])

    # 3. explicit import mappings (root mapping per consumer / shared table)
    for key, imp in spec.get("imports", {}).items():
        pname, dname = key.split(".", 1)
        wired.add((pname, dname))
        consumer = demands.get((pname, dname), {}).get("input")
        if consumer is None or imp["iid"] not in instances:
            errors.append(f"dangling_endpoint:{key}")
            continue
        bindings.append([consumer[0], consumer[1], imp["iid"], imp["output"]])
        skey = demands[(pname, dname)].get("singleton")
        if skey:
            owner = singleton_owner.setdefault(skey, imp["iid"])
            if owner != imp["iid"]:
                errors.append(f"conflicting_singleton:{skey}")
                if skey not in singleton_conflicts:
                    singleton_conflicts.append(skey)

    # 4. explicit shared-instance identity table
    for skey, iid in spec.get("shared", {}).items():
        if iid not in instances:
            errors.append(f"dangling_endpoint:shared:{skey}")
            continue
        owner = singleton_owner.setdefault(skey, iid)
        if owner != iid:
            errors.append(f"conflicting_singleton:{skey}")
            if skey not in singleton_conflicts:
                singleton_conflicts.append(skey)

    # 5. boundary demands and exports; everything else unbound (C04)
    boundary_demands: dict = {}
    for b, port in spec.get("demands", {}).items():
        p, d = port
        d0 = demands.get((p, d))
        if d0 is None:
            errors.append(f"dangling_endpoint:boundary:{b}")
            continue
        wired.add((p, d))
        boundary_demands[b] = d0
    for b, port in spec.get("exports", {}).items():
        p, e = port
        if (p, e) not in exports_out:
            errors.append(f"dangling_endpoint:boundary_export:{b}")
            continue
        exports_out[b] = exports_out[(p, e)]
    for key in demands:
        if key not in wired:
            errors.append(f"unbound_input:{key[0]}.{key[1]}")

    if errors:
        return Expansion(None, errors=sorted(set(errors)),
                         singleton_conflicts=singleton_conflicts)

    closure = piece(
        instances,
        sorted(bindings),
        boundary_demands,
        {b: exports_out[b] for b in spec.get("exports", {}) if b in exports_out},
        relations,
    )
    exp = Expansion(closure, singleton_conflicts=singleton_conflicts)
    exp.traversed = len(instances)
    exp.visited_once = reachability_counts_once(closure)
    return exp


def reachability_counts_once(closure):
    """Walk bindings from boundary demand inputs and public export outputs
    to a fixed point; each real instance must be visited exactly once
    (C09c fixed-point traversal)."""
    adjacency: dict[str, list[str]] = {iid: [] for iid in closure["instances"]}
    for c, _ci, p, _po in closure["bindings"]:
        if c in adjacency and p in adjacency:
            adjacency[c].append(p)
    roots = [d["input"][0] for d in closure["demands"].values()
             if d["input"][0] in adjacency]
    roots += [e["output"][0] for e in closure["exports"].values()
              if e["output"][0] in adjacency]
    seen, stack = set(), list(roots)
    while stack:
        iid = stack.pop()
        if iid in seen:
            continue
        seen.add(iid)
        stack.extend(adjacency[iid])
        if len(seen) > TRAVERSAL_BOUND:
            return False
    return len(seen) == len(closure["instances"])


# --- Canonical form (renaming equivalence, C09a) -----------------------------

def canonical_closure(c):
    """Canonical labels from (kind, artifact) signatures.

    The frozen fixtures give every instance a distinct (kind, artifact)
    signature, so signature order is injective; non-injective signatures
    abort rather than silently merge (recorded as a scope limitation).
    """
    sigs = sorted((v["kind"], v["artifact"], iid)
                  for iid, v in c["instances"].items())
    assert len({(k, a) for k, a, _ in sigs}) == len(sigs), \
        "fixture signatures are not injective"
    rename = {iid: f"i{n}" for n, (_k, _a, iid) in enumerate(sigs)}
    r = lambda x: rename.get(x, x)  # dangling endpoints keep their raw id
    inst = [{"iid": r(iid), "kind": k, "artifact": a,
             "singleton": c["instances"][iid]["singleton"]}
            for k, a, iid in sigs]
    return {
        "instances": inst,
        "bindings": sorted([r(b[0]), b[1], r(b[2]), b[3]]
                           for b in c["bindings"]),
        "demands": {name: [r(v["input"][0]), v["input"][1],
                           v.get("singleton")]
                    for name, v in sorted(c["demands"].items())},
        "exports": {name: [r(v["output"][0]), v["output"][1]]
                    for name, v in sorted(c["exports"].items())},
        "relations": sorted([r(x), op, r(y)] for x, op, y in c["relations"]),
    }


def closure_digest(c):
    return digest(canonical_closure(c))


# --- Shared oracle -----------------------------------------------------------

def check_closure(c):
    """The one oracle for every arm: binding completeness, singleton
    identity, relation endpoints. Same function, same budget, all arms."""
    reasons = []
    iids = set(c["instances"])
    for b in c["bindings"]:
        if b[0] not in iids or b[2] not in iids:
            reasons.append(f"binding_endpoint_missing:{b}")
    for name, d in c["demands"].items():
        if d["input"][0] not in iids:
            reasons.append(f"demand_endpoint_missing:{name}")
    for name, e in c["exports"].items():
        if e["output"][0] not in iids:
            reasons.append(f"export_endpoint_missing:{name}")
    owners: dict[str, set] = {}
    for iid, v in c["instances"].items():
        if v.get("singleton"):
            owners.setdefault(v["singleton"], set()).add(iid)
    for skey, ids in owners.items():
        if len(ids) > 1:
            reasons.append(f"conflicting_singleton:{skey}")
    for r in c["relations"]:
        if r[0] not in iids or r[2] not in iids:
            reasons.append(f"relation_endpoint_missing:{r}")
    return ("refused", sorted(reasons)) if reasons else ("accepted", [])


# --- Evidence commitments (C07/C10/C11/C16) ----------------------------------

ARTIFACTS = {
    "api": {"kind": "endpoint", "blob": "api-impl-v1"},
    "store": {"kind": "storage", "blob": "store-impl-v1"},
}
ARTIFACT_IDS = {name: digest(v["blob"]) for name, v in ARTIFACTS.items()}


def make_claim(c, artifact_ids=None, oracle_id=ORACLE_ID,
               laws_digest=ORACLE_LAWS_DIGEST, authority_rev=POLICY_REV):
    ids = dict(artifact_ids or ARTIFACT_IDS)
    return {"closure_digest": closure_digest(c),
            "artifact_ids": ids,
            "oracle_id": oracle_id,
            "laws_digest": laws_digest,
            "authority_rev": authority_rev}


def check_evidence(claim, current_claim):
    """Evidence reuse: all commitment fields must match the current run."""
    if claim["closure_digest"] != current_claim["closure_digest"]:
        return ("refused", "domain_mismatch")
    if claim["artifact_ids"] != current_claim["artifact_ids"]:
        return ("refused", "stale_evidence")
    if claim["oracle_id"] != current_claim["oracle_id"]:
        return ("refused", "oracle_mismatch")
    if claim["laws_digest"] != current_claim["laws_digest"]:
        return ("refused", "laws_mismatch")
    if claim["authority_rev"] != POLICY_REV:
        return ("refused", "authority_revoked")
    return ("accepted", "")


BUNDLE = {  # complete commitment bundle (C10 control)
    "laws": list(LAWS),
    "oracle_fixture": ORACLE_ID,
    "artifact_blobs": {name: v["blob"] for name, v in ARTIFACTS.items()},
}


def check_bundle(bundle):
    if bundle.get("laws") != list(LAWS):
        return ("refused", "missing_laws")
    if bundle.get("oracle_fixture") != ORACLE_ID:
        return ("refused", "missing_oracle_fixture")
    for name, art in ARTIFACTS.items():
        if bundle.get("artifact_blobs", {}).get(name) != art["blob"]:
            return ("refused", f"missing_artifact_blob:{name}")
    return ("accepted", "")


# --- Frozen logical domain ---------------------------------------------------

def api_part(iid="api", clock=False, artifact=None):
    demands = {"storage": {"input": [iid, "store_in"],
                           "singleton": SHARED_KEY}}
    if clock:
        demands["clock"] = {"input": [iid, "clock_in"], "singleton": None}
    return piece(
        {iid: {"kind": "endpoint",
               "artifact": artifact or ARTIFACT_IDS["api"],
               "singleton": None}},
        [], demands, {"result": {"output": [iid, "out"]}})


def store_part(iid="store", artifact=None):
    return piece(
        {iid: {"kind": "storage",
               "artifact": artifact or ARTIFACT_IDS["store"],
               "singleton": SHARED_KEY}},
        [], {}, {"get": {"output": [iid, "val"]}})


def metric_part():
    return piece(
        {"metric": {"kind": "observer",
                    "artifact": digest("metric-impl-v1"), "singleton": None}},
        [], {}, {"unused_metric": {"output": ["metric", "tick"]}})


def merge_base():
    """H0 flat encoding: full instance graph with one explicit root import
    mapping per consumer; the import supplies the storage binding."""
    a, s = api_part(), store_part()
    return piece(
        {**a["instances"], **s["instances"]},
        [],
        {**a["demands"], **s["demands"]},
        {**a["exports"]})


def with_relation():
    a, s = api_part(), store_part()
    return piece({**a["instances"], **s["instances"]},
                 [],
                 {**a["demands"]}, {**a["exports"]},
                 [["api", "less_equal", "store"]])


def base_spec(arm):
    """The same logical two-part assembly encoded per representation arm."""
    if arm == "H0":
        return {"parts": {"flat": {"piece": merge_base()}},
                "imports": {"flat.storage": {"iid": "store", "output": "val"}},
                "demands": {},
                "exports": {"result": ["flat", "result"]}}
    if arm == "H1":
        return {"parts": {"wrapped": {"wrapper": {
            "internals": {"piece": merge_base()},
            "contract": {"exports": ["result"], "demands": ["storage"]},
            "exports_map": {"result": "result"},
            "demands_map": {"storage": {"demand": "storage",
                                        "singleton": SHARED_KEY}}}}},
            "imports": {"wrapped.storage": {"iid": "store", "output": "val"}},
            "demands": {},
            "exports": {"result": ["wrapped", "result"]}}
    return {"parts": {"api": {"piece": api_part()},
                      "store": {"piece": store_part()}},
            "wiring": [["api", "storage", "store", "get"]],
            "demands": {},
            "exports": {"result": ["api", "result"]},
            "shared": {SHARED_KEY: "store"}}


ARMS = ("H0", "H1", "H2")
PART = {"H0": "flat", "H1": "wrapped", "H2": "api"}


def run_arm(arm):
    return compose(base_spec(arm))


def arm_records(exp):
    c = exp.closure
    return {
        "verdict": "error" if c is None else check_closure(c)[0],
        "reasons": exp.errors if c is None else check_closure(c)[1],
        "closure_digest": closure_digest(c) if c else None,
        "traversed": exp.traversed,
        "visited_once": exp.visited_once,
        "singleton_conflicts": exp.singleton_conflicts,
    }


# --- Cases -------------------------------------------------------------------

def full_spec(arm, with_result=True):
    """Base assembly plus the metric part carrying an explicitly unused
    export; the boundary contract can drop either output."""
    spec = base_spec(arm)
    if arm == "H1":
        w = spec["parts"]["wrapped"]["wrapper"]
        m, mt = merge_base(), metric_part()
        m = piece({**m["instances"], **mt["instances"]}, m["bindings"],
                  m["demands"], {**m["exports"], **mt["exports"]})
        emap = {"unused_metric": "unused_metric"}
        if with_result:
            emap["result"] = "result"
        spec["parts"]["wrapped"] = {"wrapper": {**w, "internals":
                                                {"piece": m},
                                                "exports_map": emap}}
        spec["exports"] = {"unused_metric": ["wrapped", "unused_metric"]}
        if with_result:
            spec["exports"]["result"] = ["wrapped", "result"]
        return spec
    spec["parts"]["metric"] = {"piece": metric_part()}
    spec["exports"] = {"unused_metric": ["metric", "unused_metric"]}
    if with_result:
        spec["exports"]["result"] = base_spec(arm)["exports"]["result"]
    return spec


def case_c03():
    """C03: remove a demanded export (refuse); remove an explicitly unused
    export (scoped compatibility after complete demand and dependency
    checks)."""
    consumer = piece(
        {"consumer": {"kind": "client", "artifact": digest("client-v1"),
                      "singleton": None}},
        [], {"result_in": {"input": ["consumer", "r_in"], "singleton": None}},
        {})
    out = {"demanded_removal": {}, "unused_removal": {}}
    for arm in ARMS:
        # demanded: the boundary contract drops "result" while the consumer
        # still demands it through the boundary
        trimmed = compose(full_spec(arm, with_result=False))
        outer = compose({"parts": {"core": {"piece": trimmed.closure},
                                   "consumer": {"piece": consumer}},
                         "wiring": [["consumer", "result_in", "core",
                                     "result"]]})
        out["demanded_removal"][arm] = arm_records(outer)
        # unused: drop "unused_metric" from the boundary contract even
        # though nobody demands it; the complete demand and dependency
        # checks still pass (scoped compatibility)
        kept_spec = full_spec(arm)
        kept_spec["exports"] = {b: v for b, v in kept_spec["exports"].items()
                                if b != "unused_metric"}
        if arm == "H1":
            kept_spec["parts"]["wrapped"]["wrapper"]["exports_map"] = {
                "result": "result"}
        kept = compose(kept_spec)
        kept_outer = compose({"parts": {"core": {"piece": kept.closure},
                                        "consumer": {"piece": consumer}},
                              "wiring": [["consumer", "result_in", "core",
                                          "result"]]})
        rec = arm_records(kept_outer)
        rec["demands_complete"] = all(
            v["input"][0] in kept.closure["instances"]
            for v in kept.closure["demands"].values())
        rec["unused_export_dropped"] = "unused_metric" not in kept.closure[
            "exports"]
        out["unused_removal"][arm] = rec
    return out


def case_c04():
    """C04: internal replacement adds an unbound required input while the
    public shape stays fixed; closure is refused and the wrapper must not
    hide the missing binding."""
    out = {}
    for arm in ARMS:
        if arm == "H0":
            m = merge_base()
            m["demands"]["clock"] = {"input": ["api", "clock_in"],
                                     "singleton": None}
            spec = {**base_spec(arm), "parts": {"flat": {"piece": m}}}
        elif arm == "H1":
            w = base_spec("H1")["parts"]["wrapped"]["wrapper"]
            m = merge_base()
            m["demands"]["clock"] = {"input": ["api", "clock_in"],
                                     "singleton": None}
            spec = {**base_spec(arm),
                    "parts": {"wrapped": {"wrapper": {**w,
                                                      "internals":
                                                      {"piece": m},
                                                      "demands_map": {
                                                          "storage": {
                                                              "demand":
                                                              "storage",
                                                              "singleton":
                                                              SHARED_KEY},
                                                          "clock": {
                                                              "demand":
                                                              "clock"}}}}}}
        else:
            spec = {**base_spec(arm),
                    "parts": {"api": {"piece": api_part(clock=True)},
                              "store": {"piece": store_part()}}}
        spec["wiring"] = base_spec(arm).get("wiring", [])
        out[arm] = arm_records(compose(spec))
    return out


def case_c05():
    """C05: two boundaries reference one real singleton (accept shared
    identity); control uses two distinct instances (refuse). Contract-hash
    equality cannot merge actual instances."""
    out = {"shared_identity": {}, "distinct_control": {},
           "equal_contracts_distinct_instances": {}}
    for arm in ARMS:
        rec = run_arm(arm)
        c = rec.closure
        shared = arm_records(rec)
        shared["singleton_instance_count"] = sum(
            1 for v in c["instances"].values()
            if v.get("singleton") == SHARED_KEY)
        shared["consumers_bound"] = sum(
            1 for b in c["bindings"] if b[2] == "store")
        out["shared_identity"][arm] = shared
        # control: same-shape assembly, but the mapping splits the singleton
        # into two distinct real instances
        if arm == "H0":
            m = merge_base()
            m["instances"]["api2"] = {"kind": "endpoint",
                                      "artifact": digest("api-impl-v1b"),
                                      "singleton": None}
            m["instances"]["store2"] = {"kind": "storage",
                                        "artifact": digest("store-impl-v1b"),
                                        "singleton": SHARED_KEY}
            m["demands"]["storage2"] = {"input": ["api2", "store_in"],
                                        "singleton": SHARED_KEY}
            split = {"parts": {"flat": {"piece": m}},
                     "imports": {"flat.storage": {"iid": "store",
                                                  "output": "val"},
                                 "flat.storage2": {"iid": "store2",
                                                   "output": "val"}},
                     "demands": {}, "exports": {}}
        elif arm == "H1":
            w = base_spec("H1")["parts"]["wrapped"]["wrapper"]
            split = {"parts": {
                "wrapped": {"wrapper": dict(w)},
                "wrapped2": {"wrapper": {
                    **w,
                    "internals": {"piece": rename_piece(
                        merge_base(), {"api": "api2", "store": "store2"})}}}},
                "imports": {"wrapped.storage": {"iid": "store",
                                                "output": "val"},
                            "wrapped2.storage": {"iid": "store2",
                                                 "output": "val"}},
                "demands": {}, "exports": {}}
        else:
            split = {"parts": {"api": {"piece": api_part("api")},
                               "api2": {"piece": api_part(
                                   "api2", artifact=digest("api-impl-v1b"))},
                               "store": {"piece": store_part("store")},
                               "store2": {"piece": store_part(
                                   "store2", artifact=digest(
                                       "store-impl-v1b"))}},
                     "wiring": [["api", "storage", "store", "get"],
                                ["api2", "storage", "store2", "get"]],
                     "demands": {}, "exports": {}}
        out["distinct_control"][arm] = arm_records(compose(split))
    # equal wrapper contracts, distinct instances: identity comes from the
    # explicit mapping, never from contract-hash equality
    w = base_spec("H1")["parts"]["wrapped"]["wrapper"]
    eq = compose({**base_spec("H1"),
                  "parts": {
                      "wrapped": {"wrapper": dict(w)},
                      "wrapped2": {"wrapper": {
                          **w,
                          "internals": {"piece": rename_piece(
                              merge_base(),
                              {"api": "api2", "store": "store2"})}}}},
                  "imports": {"wrapped.storage": {"iid": "store",
                                                  "output": "val"},
                              "wrapped2.storage": {"iid": "store2",
                                                   "output": "val"}},
                  "demands": {}, "exports": {}})
    contract = lambda w: digest([w["contract"], w["exports_map"],
                                 w["demands_map"]])
    out["equal_contracts_distinct_instances"]["H1"] = {
        **arm_records(eq),
        "contracts_equal": contract(w) ==
        contract(base_spec("H1")["parts"]["wrapped"]["wrapper"]),
    }
    return out


def case_c06():
    """C06: an internal less_equal relation crosses the boundary; a wrapper
    that hides an endpoint is refused, honest arms accept. H0/H2 encodings
    cannot hide endpoints, so the hiding variant is H1-only."""
    out = {"honest": {}, "endpoint_hidden": {}}
    for arm in ARMS:
        if arm == "H0":
            spec = {**base_spec(arm), "parts": {"flat":
                                                {"piece": with_relation()}}}
        elif arm == "H1":
            w = base_spec("H1")["parts"]["wrapped"]["wrapper"]
            spec = {**base_spec(arm),
                    "parts": {"wrapped": {"wrapper": {**w, "internals":
                                                      {"piece":
                                                       with_relation()}}}}}
        else:
            a = api_part()
            a["relations"] = [["api", "less_equal", "store"]]
            spec = {**base_spec(arm),
                    "parts": {"api": {"piece": a},
                              "store": {"piece": store_part()}}}
        out["honest"][arm] = arm_records(compose(spec))
        if arm == "H1":
            w = spec["parts"]["wrapped"]["wrapper"]
            hidden_node = {"wrapper": {**w, "hide_instances": ["store"]}}
            hp, herr = resolve(hidden_node)
            if herr or hp is None:
                out["endpoint_hidden"][arm] = {
                    "verdict": "error", "reasons": herr,
                    "closure_digest": None, "traversed": 0,
                    "visited_once": True, "singleton_conflicts": []}
            else:
                verdict, reasons = check_closure(hp)
                out["endpoint_hidden"][arm] = {
                    "verdict": verdict, "reasons": reasons,
                    "closure_digest": closure_digest(hp),
                    "traversed": len(hp["instances"]),
                    "visited_once": reachability_counts_once(hp),
                    "singleton_conflicts": []}
        else:
            out["endpoint_hidden"][arm] = {
                "verdict": "not_applicable",
                "reason": "H0/H2 encodings cannot hide endpoints",
                "closure_digest": None, "traversed": 0, "visited_once": True,
                "singleton_conflicts": []}
    return out


def case_c07(c):
    """C07: same contract, new bytes. A changed artifact cannot reuse old
    behavioral acceptance; unchanged complete inputs may reuse that check
    with policy reevaluated."""
    fresh_ids = {**ARTIFACT_IDS, "store": digest("store-impl-v2")}
    current = make_claim(c, artifact_ids=fresh_ids)
    return {
        "unchanged_reuse": check_evidence(make_claim(c), make_claim(c)),
        "changed_artifact_stale": check_evidence(make_claim(c), current),
        "changed_artifact_fresh_run": check_evidence(current, current),
    }


def case_c09a():
    """C09a: explicit injective instance renaming; same canonical closure,
    demands, relations and public traces in every arm."""
    rename = {"api": "a1", "store": "s1"}
    out = {}
    for arm in ARMS:
        exp = run_arm(arm)
        renamed = rename_piece(exp.closure, rename)
        out[arm] = {
            "base_digest": closure_digest(exp.closure),
            "renamed_digest": closure_digest(renamed),
            "equal": closure_digest(exp.closure) == closure_digest(renamed),
            "verdict": check_closure(exp.closure)[0],
        }
    return out


def rename_piece(c, rename):
    def r(x):
        return rename.get(x, x)
    return piece(
        {r(iid): dict(v) for iid, v in c["instances"].items()},
        [[r(b[0]), b[1], r(b[2]), b[3]] for b in c["bindings"]],
        {name: {"input": [r(v["input"][0]), v["input"][1]],
                "singleton": v.get("singleton")}
         for name, v in c["demands"].items()},
        {name: {"output": [r(v["output"][0]), v["output"][1]]}
         for name, v in c["exports"].items()},
        [[r(x), op, r(y)] for x, op, y in c["relations"]])


def case_c09b():
    """C09b: compose a valid assembly with an empty assembly on both sides;
    also evaluate empty alone."""
    out = {"left_identity": {}, "right_identity": {}, "empty_alone": {}}
    base = {arm: run_arm(arm) for arm in ARMS}
    for arm in ARMS:
        spec = base_spec(arm)
        left = compose({**spec, "parts": {**spec["parts"],
                                          "empty": {"piece": EMPTY_PIECE}}})
        out["left_identity"][arm] = {
            **arm_records(left),
            "identity_preserved": closure_digest(left.closure) ==
            closure_digest(base[arm].closure)}
        right = compose({"parts": {"empty": {"piece": EMPTY_PIECE},
                                   **spec["parts"]},
                         **{k: v for k, v in spec.items() if k != "parts"}})
        out["right_identity"][arm] = {
            **arm_records(right),
            "identity_preserved": closure_digest(right.closure) ==
            closure_digest(base[arm].closure)}
    empty = compose({"parts": {"empty": {"piece": EMPTY_PIECE}}})
    c = empty.closure
    out["empty_alone"] = {
        "structure": "pass_declared",
        "coverage_instances": len(c["instances"]),
        "coverage_bindings": len(c["bindings"]),
        "ratio": None,
        "verdict": check_closure(c)[0],
    }
    return out


def cycle_a():
    a = piece({"a_inst": {"kind": "endpoint", "artifact": digest("a-v1"),
                          "singleton": None}},
              [], {"x": {"input": ["a_inst", "x_in"], "singleton": None},
                   "trig": {"input": ["a_inst", "trig_in"],
                            "singleton": None}},
              {"y": {"output": ["a_inst", "y_out"]}})
    return a


def cycle_b():
    return piece({"b_inst": {"kind": "provider", "artifact": digest("b-v1"),
                             "singleton": None}},
                 [], {"y": {"input": ["b_inst", "y_in"], "singleton": None}},
                 {"x": {"output": ["b_inst", "x_out"]}})


def cycle_merged():
    a, b = cycle_a(), cycle_b()
    return piece({**a["instances"], **b["instances"]},
                 [["a_inst", "x_in", "b_inst", "x_out"],
                  ["b_inst", "y_in", "a_inst", "y_out"]],
                 {"trig": {"input": ["a_inst", "trig_in"],
                           "singleton": None}},
                 {})


def case_c09c():
    """C09c: finite A<->B provider cycle reachable from root A with valid
    bindings; fixed-point traversal visits each real instance once."""
    out = {}
    for arm in ARMS:
        if arm == "H0":
            node = {"piece": cycle_merged()}
        elif arm == "H1":
            node = {"wrapper": {
                "internals": {"piece": cycle_merged()},
                "contract": {"exports": [], "demands": ["trig"]},
                "exports_map": {},
                "demands_map": {"trig": {"demand": "trig"}}}}
        else:
            node = {"children": {"a": {"piece": cycle_a()},
                                 "b": {"piece": cycle_b()}},
                    "wiring": [["a", "x", "b", "x"], ["b", "y", "a", "y"]],
                    "demands": {"trig": ["a", "trig"]},
                    "exports": {}}
        exp = compose({"parts": {"root": node},
                       "demands": {"trig": ["root", "trig"]}})
        out[arm] = arm_records(exp)
    return out


def case_c09d():
    """C09d: map two distinct instances to one id (collision) or introduce
    an unresolved endpoint; the valid injective map is the control."""
    out = {"collision": {}, "unresolved_endpoint": {}, "valid_control": {}}
    for arm in ARMS:
        base = base_spec(arm)
        coll = {**base, "parts": {**base["parts"],
                                  "twin": {"piece": store_part("store")}}}
        out["collision"][arm] = arm_records(compose(coll))
        if arm == "H2":
            dang = {**base, "wiring": [],
                    "imports": {"api.storage": {"iid": "missing",
                                                "output": "val"}}}
        else:
            dang = {**base,
                    "imports": {f"{PART[arm]}.storage":
                                {"iid": "missing", "output": "val"}}}
        out["unresolved_endpoint"][arm] = arm_records(compose(dang))
        out["valid_control"][arm] = arm_records(run_arm(arm))
    return out


def case_c09e():
    """C09e: three jointly composable assemblies with fixed sharing and
    bindings; both groupings give an equal flat closure modulo renaming and
    the same verdict."""
    p1 = piece({"p1": {"kind": "endpoint", "artifact": digest("p1-v1"),
                       "singleton": None}},
               [], {"mid": {"input": ["p1", "mid_in"], "singleton": None}},
               {"out": {"output": ["p1", "out"]}})
    p2 = piece({"p2": {"kind": "relay", "artifact": digest("p2-v1"),
                       "singleton": None}},
               [], {"base": {"input": ["p2", "base_in"],
                             "singleton": SHARED_KEY}},
               {"mid": {"output": ["p2", "mid_out"]}})
    p3 = piece({"p3": {"kind": "storage", "artifact": digest("p3-v1"),
                       "singleton": SHARED_KEY}},
               [], {}, {"base": {"output": ["p3", "base_out"]}})
    imp = {"b.base": {"iid": "p3", "output": "base_out"}}
    # grouping 1: (a + b) + c -- b keeps its base demand open at the inner
    # boundary; the outer composition binds it to c
    inner = compose({"parts": {"a": {"piece": p1}, "b": {"piece": p2}},
                     "wiring": [["a", "mid", "b", "mid"]],
                     "demands": {"base": ["b", "base"]},
                     "exports": {"mid": ["b", "mid"], "out": ["a", "out"]}})
    g1 = compose({"parts": {"inner": {"piece": inner.closure},
                            "c": {"piece": p3}},
                  "wiring": [],
                  "imports": {"inner.base": {"iid": "p3",
                                             "output": "base_out"}},
                  "exports": {"out": ["inner", "out"]}})
    # grouping 2: a + (b + c) -- the right subgroup binds base internally
    right = compose({"parts": {"b": {"piece": p2}, "c": {"piece": p3}},
                     "wiring": [], "imports": imp,
                     "exports": {"mid": ["b", "mid"]}})
    g2 = compose({"parts": {"a": {"piece": p1},
                            "right": {"piece": right.closure}},
                  "wiring": [["a", "mid", "right", "mid"]],
                  "exports": {"out": ["a", "out"]}})
    rec1, rec2 = arm_records(g1), arm_records(g2)
    return {"grouping_left": rec1, "grouping_right": rec2,
            "equal_closure": rec1["closure_digest"] ==
            rec2["closure_digest"],
            "same_verdict": rec1["verdict"] == rec2["verdict"]}


def case_c10(c):
    """C10: delete a root subtree, implementation blob or oracle fixture;
    commitment mismatch is an error and missing required evidence is
    refusal, never pass."""
    return {
        "intact_bundle": check_bundle(BUNDLE),
        "missing_impl_blob": check_bundle(
            {**BUNDLE, "artifact_blobs":
             {k: v for k, v in BUNDLE["artifact_blobs"].items()
              if k != "store"}}),
        "missing_oracle_fixture": check_bundle(
            {**BUNDLE, "oracle_fixture": None}),
    }


def case_c11(c):
    """C11: keep structure fixed; revoke evidence authority. Policy is
    reevaluated; independent structure/law results are preserved; the old
    acceptance is not reusable."""
    structure = check_closure(c)[0]
    current = make_claim(c)
    old = make_claim(c, authority_rev=POLICY_REV - 1)
    return {
        "structure_verdict_preserved": structure,
        "current_authority": check_evidence(current, current),
        "old_acceptance_reuse": check_evidence(old, current),
    }


def case_c16(c):
    """C16: fewer schedules/subdomain, different oracle, or candidate edits
    accepted obligations are refused; the matching claim is accepted."""
    sub = piece(dict(list(c["instances"].items())[:1]), [], {}, {})
    current = make_claim(c)
    return {
        "matching": check_evidence(make_claim(c), current),
        "subdomain": check_evidence(make_claim(sub), current),
        "foreign_oracle": check_evidence(
            make_claim(c, oracle_id=ORACLE_ID + "-elsewhere"), current),
        "edited_laws": check_evidence(
            make_claim(c, laws_digest=digest(LAWS[:1])), current),
    }


# --- Experiment --------------------------------------------------------------

def main():
    base_exps = {arm: run_arm(arm) for arm in ARMS}
    base_digests = {arm: closure_digest(e.closure)
                    for arm, e in base_exps.items()}
    base_c = base_exps["H2"].closure

    report = {
        "scope": {
            "arms": list(ARMS),
            "protocol_revision": 2,
            "oracle_id": ORACLE_ID,
            "laws": list(LAWS),
            "laws_digest": ORACLE_LAWS_DIGEST,
            "policy_rev": POLICY_REV,
            "traversal_bound": TRAVERSAL_BOUND,
            "shared_singleton_key": SHARED_KEY,
            "claim": "finite frozen fixtures only; representation comparison "
                     "under one shared oracle; no v1 runtime, unbounded "
                     "liveness, cross-language conformance, or category "
                     "proof is claimed",
        },
        "artifact_ids": {
            "closure_oracle": digest([inspect.getsource(check_closure),
                                      inspect.getsource(compose)]),
            "canonicalizer": digest(inspect.getsource(canonical_closure)),
            "evidence_checker": digest(inspect.getsource(check_evidence)),
            "bundle_checker": digest(inspect.getsource(check_bundle)),
            "h0_flat": digest(inspect.getsource(merge_base)),
            "h1_wrapper": digest([inspect.getsource(base_spec),
                                  inspect.getsource(resolve)]),
            "h2_composite": digest(inspect.getsource(compose)),
        },
        "representation_equivalence": {
            "canonical_digests": base_digests,
            "equal_across_arms": len(set(base_digests.values())) == 1,
            "verdicts": {arm: check_closure(e.closure)[0]
                         for arm, e in base_exps.items()},
        },
        "unknowns": [
            "canonical labeling assumes injective (kind, artifact) "
            "signatures; colliding signatures abort instead of merging",
            "acceptance is bounded to the frozen fixtures; no equivalence "
            "proof over all assemblies is claimed",
            "these are structural closures, so no behavioral verdict is "
            "pooled with the wild-9co.2 six-schedule results",
            "H2 entry is evaluated independently; no H1 benefit is assumed",
        ],
        "cases": {
            "C03_used_vs_unused_output_removal": case_c03(),
            "C04_hidden_dependency": case_c04(),
            "C05_shared_singleton": case_c05(),
            "C06_cross_boundary_relation": case_c06(),
            "C07_same_contract_new_bytes": case_c07(base_c),
            "C09a_renaming_equivalence": case_c09a(),
            "C09b_empty_identity": case_c09b(),
            "C09c_cyclic_closure": case_c09c(),
            "C09d_invalid_mapping": case_c09d(),
            "C09e_grouping_associativity": case_c09e(),
            "C10_incomplete_bundle": case_c10(base_c),
            "C11_stale_authority": case_c11(base_c),
            "C16_evidence_domain_mismatch": case_c16(base_c),
        },
    }
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()