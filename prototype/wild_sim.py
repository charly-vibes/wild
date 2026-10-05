#!/usr/bin/env python3
"""Toy simulation of wild's tier pipeline vs. semver auto-update.

States follow wild.md: draft -> extracted -> identified -> shape_checked
-> law_checked -> published (or rejected@<tier>); evidence is an optional
post-publish canary. Ground truth ("truth") is written by hand per scenario
and is deliberately independent of the checker.
"""
import json
from dataclasses import dataclass, field

SUB = {("int32", "int64"), ("int64", "decimal"), ("int32", "decimal")}
def sub(a, b): return a == b or (a, b) in SUB  # a usable where b expected


@dataclass(frozen=True)
class Slot:
    pol: str                      # 'out' = provides, 'in' = requires
    ty: str
    variants: frozenset = frozenset()
    closed: bool = True
    need: str = "required"
    default: object = None


@dataclass
class Contract:
    slots: dict
    laws: tuple = ()
    retired: dict = field(default_factory=dict)   # tombstones: name -> last Slot of a dropped requires


def slot_ok(old, new):
    """Is `new` a valid accretion of `old` for one slot? (fixed after exhaustive law testing)"""
    if new is None:
        return (old.pol == "in", "provide removed")        # dropping a requires is fine
    if old.pol != new.pol:
        return (False, "polarity changed")
    if old.pol == "out":
        if not sub(new.ty, old.ty): return (False, f"output type {old.ty}->{new.ty}")
        if old.variants and old.closed:                    # consumers may match exhaustively
            if not new.variants or not new.variants <= old.variants:
                return (False, "closed output sum grew or became unrestricted")
            if not new.closed: return (False, "closed output sum became open")
        if old.default != new.default: return (False, "declared default changed")
    else:
        if not sub(old.ty, new.ty): return (False, "input type narrowed")
        if not old.variants and new.variants: return (False, "input became restricted")
        if old.variants and new.variants and not new.variants >= old.variants:
            return (False, "input variants shrank")
        if old.variants and not old.closed and new.closed: return (False, "input tolerance shrank")
        if old.need == "optional" and new.need == "required": return (False, "optional input became required")
    return (True, "")


def eff(c, n):
    return c.slots.get(n) or c.retired.get(n)


def shape_check(old, new, demand=None):
    """Accretion: provides grow, requires shrink. Dropped requires leave a tombstone so a
    name can never come back with a different meaning (found by exhaustive law testing)."""
    names = set(old.slots) | set(old.retired) | set(new.slots) | set(new.retired)
    for n in sorted(names):
        if demand is not None and n not in demand: continue
        o, ns = eff(old, n), new.slots.get(n)
        if o is None:
            if ns is None and n in new.retired:      # add-then-drop of an optional input is harmless
                t = new.retired[n]
                if t.pol != "in" or t.need == "required":
                    return (False, f"{n}: tombstone without history")
            if ns is not None and ns.pol == "in" and ns.need == "required":
                return (False, f"{n}: new required input")
            continue
        if ns is None:
            if o.pol == "out": return (False, f"{n}: provide removed")
            t = new.retired.get(n)
            if t is None: return (False, f"{n}: tombstone not carried")
            ok, why = slot_ok(o, t)
            if not ok: return (False, f"{n}: tombstone {why}")
        else:
            ok, why = slot_ok(o, ns)
            if not ok: return (False, f"{n}: {why}")
    return (True, "")


LAWS = {
    "timeout_ge_30": lambda impl: impl.get("timeout_default", 99) >= 30,
    "parses_c_fmt": lambda impl: impl.get("c_fmt") == "str",
}


def publish(chain, cand, impl, evidence=None):
    trace = ["draft", "extracted", "identified"]
    for anc in chain:                                   # tier 1, against every ancestor
        ok, why = shape_check(anc, cand)
        if not ok: return trace + ["rejected@shape"], f"shape: {why}"
    trace.append("shape_checked")
    need = {l for c in chain for l in c.laws}           # tier 2, cumulative laws
    if not need <= set(cand.laws): return trace + ["rejected@laws"], "law dropped"
    for l in cand.laws:
        if not LAWS[l](impl): return trace + ["rejected@laws"], f"law {l} failed"
    trace += ["law_checked", "published"]
    if evidence is not None:                            # tier 3 canary
        old_impl, samples = evidence
        diff = [k for k in samples if old_impl.get(k) != impl.get(k)]
        if diff: return trace + ["observed", "repair_draft"], f"evidence: {diff} drifted"
        trace.append("observed")
    return trace, "published"


@dataclass
class Consumer:
    name: str
    demand: set
    depends: set = field(default_factory=set)


def run_variant(v):
    chain, cand = v["chain"], v["cand"]
    trace, why = publish(chain, cand, v["impl"], v.get("evidence"))
    delivered_tool = trace[-1] in ("published", "observed")
    delivered_semver = v["declared"] != "major"
    rows = {}
    for c in v["consumers"]:
        broke = bool(c.demand & v["changed_slots"] or c.depends & v["changed_beh"])
        def tag(delivered):
            if delivered and broke: return "BROKEN"
            return "ok" if delivered else ("protected" if broke else "held")
        t = tag(delivered_tool)
        if t == "held" and shape_check(chain[-1], cand, c.demand)[0]: t = "held(opt-in ok)"
        rows[c.name] = {"tool": t, "semver": tag(delivered_semver)}
    return {"id": v["id"], "case": v["case"], "trace": " > ".join(trace), "why": why, "consumers": rows}


def S(**k): return Slot(**k)
P = lambda ty="str", **k: Slot("out", ty, **k)
I = lambda ty="str", **k: Slot("in", ty, **k)

V = []
# S1 mislabelled break in a minor release (Maven ~30% / npm ~14% of client releases)
v1 = Contract({"parse": P(), "parse_legacy": P()})
V.append(dict(id="1", case="minor removes a slot", chain=[v1],
    cand=Contract({"parse": P()}), impl={}, declared="minor",
    changed_slots={"parse_legacy"}, changed_beh=set(),
    consumers=[Consumer("C1", {"parse"}), Consumer("C2", {"parse_legacy"})]))

# S3 behaviour change under an unchanged signature (npm: feature modification)
base = Contract({"fetch": P(default=30)}, laws=("timeout_ge_30",))
V.append(dict(id="3a", case="default is a declared slot attr", chain=[base],
    cand=Contract({"fetch": P(default=5)}, laws=("timeout_ge_30",)),
    impl={"timeout_default": 5}, declared="patch", changed_slots=set(),
    changed_beh={"timeout_default"},
    consumers=[Consumer("C", {"fetch"}, {"timeout_default"})]))
lawc = Contract({"fetch": P()}, laws=("timeout_ge_30",))
V.append(dict(id="3b", case="behaviour covered by a law", chain=[lawc],
    cand=Contract({"fetch": P()}, laws=("timeout_ge_30",)),
    impl={"timeout_default": 5}, declared="patch", changed_slots=set(),
    changed_beh={"timeout_default"},
    consumers=[Consumer("C", {"fetch"}, {"timeout_default"})]))
bare = Contract({"list": P()})
for vid, case, ev in (("3c", "undeclared ordering, no evidence", None),
                      ("3d", "undeclared ordering, canary replay", ({"order": "insertion"}, ["order"]))):
    V.append(dict(id=vid, case=case, chain=[bare], cand=Contract({"list": P()}),
        impl={"order": "hash"}, declared="patch", changed_slots=set(),
        changed_beh={"order"}, evidence=ev,
        consumers=[Consumer("C", {"list"}, {"order"})]))

# S4 change propagation A -> B -> C (npm: second most common cause)
cfmt = Contract({"fmt": P("str")})
V.append(dict(id="4a", case="C contracted, mislabelled patch", chain=[cfmt],
    cand=Contract({"fmt": P("int32")}), impl={"c_fmt": "int"}, declared="patch",
    changed_slots={"fmt"}, changed_beh=set(),
    consumers=[Consumer("B", {"fmt"})]))
bchain = Contract({"render": P()}, laws=("parses_c_fmt",))
V.append(dict(id="4b", case="C uncontracted, B has integration law", chain=[bchain],
    cand=Contract({"render": P()}, laws=("parses_c_fmt",)), impl={"c_fmt": "int"},
    declared="patch", changed_slots=set(), changed_beh={"c_fmt"},
    consumers=[Consumer("App", {"render"}, {"c_fmt"})]))
bnolaw = Contract({"render": P()})
V.append(dict(id="4c", case="C uncontracted, B has no law", chain=[bnolaw],
    cand=Contract({"render": P()}), impl={"c_fmt": "int"}, declared="patch",
    changed_slots=set(), changed_beh={"c_fmt"},
    consumers=[Consumer("App", {"render"}, {"c_fmt"})]))

# S5 data-type changes (npm: third most common cause); polarity matters
for vid, case, old, new, truth in (
    ("5a", "output int32 -> int64", P("int32"), P("int64"), {"id"}),
    ("5b", "input int32 -> int64", I("int32"), I("int64"), set()),
    ("5c", "output int64 -> string", P("int64"), P("str"), {"id"}),
    ("5d", "closed output enum grows", P(variants=frozenset("ab")),
        P(variants=frozenset("abc")), {"id"})):
    V.append(dict(id=vid, case=case, chain=[Contract({"id": old})], cand=Contract({"id": new}),
        impl={}, declared="minor", changed_slots=truth, changed_beh=set(),
        consumers=[Consumer("C", {"id"})]))

if __name__ == "__main__":
    print(json.dumps([run_variant(v) for v in V], indent=1))
