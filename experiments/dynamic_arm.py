#!/usr/bin/env python3
# wild-pe1 — dynamic-language arm: metaprogramming-heavy extraction coverage census.
#
# PRE-REGISTRATION (committed before any extraction ran; fixture list frozen at
# commit time; no post-hoc fixture swaps). RED capture: before this file existed,
# experiments/dynamic_arm.py and experiments/dynamic_arm_results.txt did not
# exist (fixture matrix absent, exit-1 semantics) — captured in
# /tmp/wild-pe1-scratch/red_capture.txt at 2026-11-11T17:01:42Z.
#
# Question (Mistral evaluation experiment #5): does honesty-refusal degrade to
# impracticality on metaprogramming-heavy dynamic code, or does
# Unknown-with-diagnostics stay useful? An INCONCLUSIVE outcome is a valid
# pre-registered result (scope-narrowing signal).
#
# Measured arm: Python, via the prototype path used by census.py
# (`sys.path.insert(prototype); import wild_proto; wild_proto.extract_py(root, pkg)`)
# — the ast-based Python surface extractor; extract-only, no demand consumer.
# JS arm: NO JS extractor exists in the prototype (grep over prototype/*.py at
# pre-registration: no javascript/js/tree_sitter_javascript tokens) — that IS
# the finding; every JS fixture is recorded unsupported-extractor, per-fixture
# N/A, and NO extractor was built or modified (measurement only).
#
# FROZEN FIXTURE LIST (14 fixtures; 10 Python measurable + 4 JS
# unsupported-extractor). Each Python fixture is a small self-contained package
# whose KNOWN conventional public surface is documented in its module docstring
# (written into the fixture source itself, not adjusted after extraction).
# Origins: "real-pattern" = excerpt modeled directly on the on-disk CPython
# 3.15 stdlib source read at authoring time (file+line cited); "constructed" =
# built for this census, each citing the real-world idiom it models. Justify
# each (pre-registered):
#   1.  py-dispatch-singledispatch  real-pattern (CPython 3.15
#       functools.py:896 singledispatch + register usage, trimmed
#       self-contained) — decorator-based dynamic dispatch. Tests whether the
#       extractor sees through a dispatching decorator when the def statement
#       is statically present (control fixture).
#   2.  py-wraps-globals-factory    constructed (models Flask/route-table
#       endpoint registration via globals() injection) — functools.wraps chain
#       + namespace injection of documented API names.
#   3.  py-getattr-explicit         constructed (models PEP 562 lazy module
#       attribute loading as used by numpy/scipy lazy submodules) — module
#       __getattr__ serving an EXPLICIT name tuple.
#   4.  py-getattr-dynamic          constructed (models lazy loaders with
#       computed names, e.g. scipy submodule proxies) — module __getattr__
#       with NO literal name list (computed from a table).
#   5.  py-metaclass-type           constructed (models Django/SQLAlchemy
#       model builders, namedtuple-style factories) — classes built by a
#       type() call and by a metaclass __new__ that injects methods.
#   6.  py-monkeypatch              constructed (models import-time adapter
#       patching as in requests adapter mounting) — one module replaces
#       another module's function at import with a different signature.
#   7.  py-exec-built               constructed (models pydantic v1 compiled
#       validators / codegen'd APIs) — functions exec()-built into the module
#       namespace at import time.
#   8.  py-descriptor               constructed (models SQLAlchemy Column /
#       werkzeug cached_property style descriptors) — data-descriptor-backed
#       class attributes (__get__/__set__/__set_name__).
#   9.  py-class-decorator-replace  constructed (models class transforms that
#       swap the class object, e.g. functools.total_ordering / attrs) — class
#       decorator returns a type()-built subclass injecting methods.
#   10. py-registry-assembly        constructed (models plugin registries
#       assembling classes from mixins, e.g. logging handler selection) —
#       classes assembled from mixin bases chosen at runtime via dict dispatch.
#   11. js-proxy-traps              constructed (models lowdb-style proxy
#       chains) — JS Proxy get/set/has traps exposing members. No JS
#       extractor in the prototype → unsupported-extractor, N/A.
#   12. js-cjs-dynamic-require      constructed (models CommonJS lazy adapter
#       loading) — require(modules[name]) computed at runtime. Unsupported.
#   13. js-exports-monkeypatch      constructed (models express middleware
#       export patching at require time). Unsupported.
#   14. js-defineproperty-accessors constructed (models Vue 2 reactive
#       getter/setter sprawl via Object.defineProperty). Unsupported.
#
# FROZEN RUBRIC (diagnostic usefulness, per unknown slot; 0=none,
# 1=names the mechanism, 2=names mechanism + locus):
#   KNOWN slot: inventoried with a statically checkable shape — one of
#     {module, class, property}, "const:<concrete-type>" (any const: other
#     than const:value), or "pyfn:{...}". These are shapes the checker can
#     compare across versions.
#   UNKNOWN slots and their grade + reason code (mechanically derived from the
#     contract alone, plus the fixture's pre-declared runtime_replaced list):
#     absent    (name not in contract.slots at all)         → grade 0,
#       reason unsupported-construct:<construct-tag> — silent omission, no
#       diagnostic at all.
#     const:value (name inventoried but binding uninterpreted) → grade 1,
#       reason dynamic-binding-uninterpreted — locus (exact member name)
#       present, mechanism unnamed.
#     dyn       (served dynamically; emitted ONLY by the explicit module
#       __getattr__ served-name path in _defs) → grade 2, reason
#       dynamic-service-declared — locus + mechanism both named; but dyn is
#       not a statically checkable shape (signature unknown), so it counts
#       as Unknown, with the best diagnostic.
#     stale     (name in fixture.runtime_replaced, i.e. the fixture pre-declares
#       that import-time patching/decoration REPLACES the object, yet the
#       contract inventories it with a static shape — the inventory asserts
#       the pre-patch shape as fact) → grade 0, reason monkeypatch-blind —
#       no diagnostic; worse than absent because the inventory is wrong, not
#       merely incomplete. Fixture declares runtime_replaced in code with a
#       comment pointing at the patching line; decided at fixture authorship,
#       not after extraction.
#   incomplete-demand: NOT APPLICABLE in this arm — no demand consumer is run
#     (extract-only measurement), pre-registered here so the omission is on
#     the record, not silent.
#   Refusal behaviour: wild_proto.extract_py has no refusal/complete_inventory
#     machinery — it never refuses, it silently omits. The contract's shape
#     vocabulary is the only diagnostic surface; that is what this rubric
#     grades.
#
# FROZEN RATES (every headline line names numerator and denominator):
#   fixture unknown rate  = unknown slots / |known surface| (denominator =
#     surface length documented in the fixture docstring).
#   fixture grade         = min over its unknown-slot grades; "full" if the
#     fixture has zero unknown slots (full static coverage).
#   python-arm aggregate unknown rate = Σ unknown / Σ |known surface| over the
#     10 Python fixtures. JS fixtures never enter Python aggregates.
#   grade distribution: number of fixtures whose worst unknown is g0/g1/g2,
#     plus full-coverage fixtures.
#
# FROZEN DECISION RULE (fixed before extraction; applies to the Python arm):
#   impractical   if aggregate unknown rate >= 0.5 OR >= half of the Python
#                 fixtures carry at least one grade-0 unknown (gaps are common
#                 AND undiagnosed — the silent-gap case).
#   useful        if aggregate unknown rate <= 0.2 AND no Python fixture has a
#                 grade-0 unknown (gaps rare and, where present, diagnosed).
#   inconclusive  otherwise.
#   The JS arm's unsupported-extractor status is recorded as separate
#   scope-narrowing evidence; it does not enter the Python-arm rule.
#
# HARD CONSTRAINTS honoured: measurement only (extract_py is imported, never
#   modified; no extractor built for JS); scratch under WILD_PE1_SCRATCH
#   (default /tmp/wild-pe1-scratch) with df -k checks before each fixture
#   write/extract; on Errno 122 (EDQUOT) → clean scratch → retry once →
#   honest BLOCKED (exit 2 with df output); nothing outside
#   experiments/dynamic_arm.py, experiments/dynamic_arm_results.txt,
#   experiments/RESULTS.md is written in-repo; never scratch into the repo.
import hashlib
import json
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRATCH = os.environ.get("WILD_PE1_SCRATCH", "/tmp/wild-pe1-scratch")
DF_FLOOR_KB = 2_000_000  # ~2 GiB free under /tmp required to proceed

# --------------------------------------------------------------------------- fixtures
# Each fixture: id, arm, origin, construct (reason-code tag), justification,
# files {relpath: source}, surface (module-qualified known-surface names),
# runtime_replaced (names replaced/extended at runtime by the mechanism).
FIXTURES = [
    dict(
        id="py-dispatch-singledispatch", arm="python",
        origin="real-pattern (CPython 3.15 functools.py:896 singledispatch, trimmed)",
        construct="decorator-dispatch",
        justification="control: dispatching decorator with statically present def statements",
        files={"fx/__init__.py": "", "fx/dispatch.py": '''"""KNOWN PUBLIC SURFACE (conventional API): area, to_json.
Registered overload implementations (the module-private _ defs) are not
part of the surface. Modeled on CPython 3.15 functools.py singledispatch.
"""
from functools import singledispatch


class Circle:
    def __init__(self, r):
        self.r = r


class Square:
    def __init__(self, s):
        self.s = s


@singledispatch
def area(shape):
    raise NotImplementedError(f"area of {type(shape).__name__}")


@area.register
def _(shape: Circle) -> float:
    return 3.14159 * shape.r ** 2


@singledispatch
def to_json(value):
    raise NotImplementedError(f"to_json of {type(value).__name__}")


@to_json.register
def _(value: Square) -> str:
    return f"{{'square': {value.s}}}"
'''},
        surface=["fx.dispatch.area", "fx.dispatch.to_json"],
        runtime_replaced=[],
    ),
    dict(
        id="py-wraps-globals-factory", arm="python",
        origin="constructed (models Flask route-table endpoint registration)",
        construct="namespace-injection",
        justification="functools.wraps chain installs documented API names via globals()",
        files={"fx/__init__.py": "", "fx/endpoints.py": '''"""KNOWN PUBLIC SURFACE (conventional API): handle, api_ping, api_stats,
api_status. api_ping/api_stats/api_status are installed at import time by
endpoint() into the module namespace (documented: users import them
directly as fx.endpoints.api_ping etc.).
"""
import functools


def endpoint(name):
    def deco(fn):
        @functools.wraps(fn)
        def impl(*args, **kwargs):
            return fn(*args, **kwargs)
        globals()[name] = impl                      # <- installs the surface name
        return impl
    return deco


def handle(req):
    return {"ok": True, "req": req}


@endpoint("api_ping")
def _make_ping():
    return {"pong": True}


@endpoint("api_stats")
def _make_stats(limit=10):
    return {"limit": limit}


@endpoint("api_status")
def _make_status():
    return {"status": "up"}
'''},
        surface=["fx.endpoints.handle", "fx.endpoints.api_ping", "fx.endpoints.api_stats",
                 "fx.endpoints.api_status"],
        runtime_replaced=[],
    ),
    dict(
        id="py-getattr-explicit", arm="python",
        origin="constructed (models PEP 562 lazy module attrs, numpy/scipy lazy loading)",
        construct="getattr-explicit",
        justification="module __getattr__ serves an EXPLICIT name tuple (extractor has a dedicated path)",
        files={"fx/__init__.py": "", "fx/lazy.py": '''"""KNOWN PUBLIC SURFACE (conventional API): load, dump, inspect, version.
load/dump/inspect are served lazily via module __getattr__ (PEP 562) from
the _impl namespace; documented as importable (from fx.lazy import load).
"""
_impl = {
    "load": lambda path: {"path": path, "loaded": True},
    "dump": lambda obj: str(obj),
    "inspect": lambda: {"mode": "lazy"},
}


def version():
    return "1.0.0"


def __getattr__(name):
    if name in ("load", "dump", "inspect"):
        return _impl[name]
    raise AttributeError(f"module has no attribute {name!r}")
'''},
        surface=["fx.lazy.load", "fx.lazy.dump", "fx.lazy.inspect", "fx.lazy.version"],
        runtime_replaced=[],
    ),
    dict(
        id="py-getattr-dynamic", arm="python",
        origin="constructed (models computed-name lazy loaders, scipy submodule proxies)",
        construct="getattr-dynamic",
        justification="module __getattr__ with NO literal name list (names computed from a table)",
        files={"fx/__init__.py": "", "fx/lazier.py": '''"""KNOWN PUBLIC SURFACE (conventional API): encode, decode, compress, ping.
encode/decode/compress are served by module __getattr__ computed from a
prefix table at import time (no literal name list appears in source).
"""
_TABLE = {"enc": "encode", "dec": "decode", "cmp": "compress"}
_ROOT = __name__


def ping():
    return "pong"


def __getattr__(name):
    for prefix, full in _TABLE.items():
        if name == full:
            import importlib
            mod = importlib.import_module("." + prefix, _ROOT)
            return getattr(mod, full)
    raise AttributeError(f"no attribute {name!r}")
'''},
        surface=["fx.lazier.encode", "fx.lazier.decode", "fx.lazier.compress", "fx.lazier.ping"],
        runtime_replaced=[],
    ),
    dict(
        id="py-metaclass-type", arm="python",
        origin="constructed (models Django/SQLAlchemy model builders, namedtuple factories)",
        construct="metaclass-type-call",
        justification="type()-built class + metaclass __new__ injecting a method",
        files={"fx/__init__.py": "", "fx/models.py": '''"""KNOWN PUBLIC SURFACE (conventional API): Base, Comment, Audit,
Audit.validate. Comment is built by a type() call; Audit is built under
the Meta metaclass, which injects the validate method into every class
it builds (documented: Audit().validate() works after import).
"""
class Meta(type):
    def __new__(mcls, name, bases, ns):
        ns["validate"] = lambda self: True
        return super().__new__(mcls, name, bases, ns)


class Base:
    persisted = False


Comment = type("Comment", (Base,), {"table": "comments"})


class Audit(metaclass=Meta):
    table = "audit"
'''},
        surface=["fx.models.Base", "fx.models.Comment", "fx.models.Audit", "fx.models.Audit.validate"],
        runtime_replaced=[],
    ),
    dict(
        id="py-monkeypatch", arm="python",
        origin="constructed (models import-time adapter patching, requests adapter mounting)",
        construct="monkeypatch",
        justification="patcher.py replaces provider.fetch at import with a different signature",
        files={"fx/__init__.py": "", "fx/provider.py": '''"""KNOWN PUBLIC SURFACE of the package (conventional API): fetch, render.
NOTE (runtime fact, pre-declared for adjudication): fx.patcher replaces
provider.fetch AT IMPORT TIME with a retrying wrapper whose signature is
(x, *, retries=3) — the conventional runtime API is the REPLACED one
(runtime_replaced=[fetch]).
"""
def fetch(x):
    return {"data": x}


def render(obj):
    return str(obj)
''', "fx/patcher.py": '''"""Import side-effect: replaces fx.provider.fetch (see runtime_replaced)."""
from . import provider

_orig_fetch = provider.fetch


def _fetch_with_retries(x, *, retries=3):
    for _ in range(retries):
        try:
            return _orig_fetch(x)
        except Exception:
            continue
    raise RuntimeError("retries exhausted")


provider.fetch = _fetch_with_retries        # <- the documented runtime replacement
'''},
        surface=["fx.provider.fetch", "fx.provider.render"],
        runtime_replaced=["fx.provider.fetch"],
    ),
    dict(
        id="py-exec-built", arm="python",
        origin="constructed (models pydantic v1 compiled validators / codegen'd APIs)",
        construct="exec-built",
        justification="functions exec()-built into the module namespace at import time",
        files={"fx/__init__.py": "", "fx/validators.py": '''"""KNOWN PUBLIC SURFACE (conventional API): run, check_age, check_email.
check_age and check_email are compiled by build_validators() via exec()
into this module's namespace at import time (documented: users call
fx.validators.check_age(3) directly).
"""
VALIDATOR_SRC = {
    "check_age": "def check_age(n):\\n    return n >= 0 and n < 150",
    "check_email": "def check_email(s):\\n    return '@' in s",
}


def build_validators():
    g = {}
    for name, src in VALIDATOR_SRC.items():
        exec(src, g)
    for name in VALIDATOR_SRC:
        globals()[name] = g[name]


build_validators()


def run(name, *args):
    return globals()[name](*args)
'''},
        surface=["fx.validators.run", "fx.validators.check_age", "fx.validators.check_email"],
        runtime_replaced=[],
    ),
    dict(
        id="py-descriptor", arm="python",
        origin="constructed (models SQLAlchemy Column / werkzeug cached_property descriptors)",
        construct="descriptor-protocol",
        justification="data-descriptor-backed class attributes (__get__/__set__/__set_name__)",
        files={"fx/__init__.py": "", "fx/interval.py": '''"""KNOWN PUBLIC SURFACE (conventional API): Interval, Interval.value,
Interval.unit, Interval.normalize. value/unit are data-descriptor-backed
class attributes (instances read/write them through __get__/__set__).
"""
class Bounded:
    """Data descriptor over an internal storage attribute."""

    def __set_name__(self, owner, name):
        self._store = "_" + name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self._store)

    def __set__(self, obj, value):
        if value < 0:
            raise ValueError("must be >= 0")
        setattr(obj, self._store, value)


class Interval:
    value = Bounded()
    unit = Bounded()

    def normalize(self):
        return {"value": self.value, "unit": self.unit}
'''},
        surface=["fx.interval.Interval", "fx.interval.Interval.value", "fx.interval.Interval.unit",
                 "fx.interval.Interval.normalize"],
        runtime_replaced=[],
    ),
    dict(
        id="py-class-decorator-replace", arm="python",
        origin="constructed (models class-object-swapping transforms, functools.total_ordering/attrs)",
        construct="class-decorator-replace",
        justification="class decorator returns a type()-built subclass injecting checksum",
        files={"fx/__init__.py": "", "fx/session.py": '''"""KNOWN PUBLIC SURFACE (conventional API): Session, Session.checksum.
sealed() REPLACES the decorated class with a frozen subclass built via
type() that also injects the checksum method (runtime fact: users call
Session.checksum after import; runtime_replaced=[Session]).
"""
def sealed(cls):
    ns = {"checksum": lambda self: hash((cls.__name__, sorted(vars(self))))}
    return type(cls.__name__, (cls,), ns)


@sealed
class Session:
    def __init__(self, user):
        self.user = user
'''},
        surface=["fx.session.Session", "fx.session.Session.checksum"],
        runtime_replaced=["fx.session.Session"],
    ),
    dict(
        id="py-registry-assembly", arm="python",
        origin="constructed (models plugin registries assembling classes from mixins)",
        construct="registry-assembly",
        justification="classes assembled from mixin bases chosen at runtime via dict dispatch",
        files={"fx/__init__.py": "", "fx/sinks.py": '''"""KNOWN PUBLIC SURFACE (conventional API): Sink, JsonSink, XmlSink.
JsonSink/XmlSink are assembled at import time by assemble() from the
mixins below (documented: users import and instantiate them directly).
"""
class FlushMixin:
    def flush(self):
        return True


class JsonMixin:
    def encode(self, obj):
        return {"json": str(obj)}


class XmlMixin:
    def encode(self, obj):
        return {"xml": str(obj)}


class Sink:
    closed = False


def assemble(kind):
    mixins = {"json": (JsonMixin,), "xml": (XmlMixin,)}
    return type(kind.capitalize() + "Sink", (Sink, *mixins[kind]), {})


JsonSink = assemble("json")
XmlSink = assemble("xml")
'''},
        surface=["fx.sinks.Sink", "fx.sinks.JsonSink", "fx.sinks.XmlSink"],
        runtime_replaced=[],
    ),
    dict(
        id="js-proxy-traps", arm="js",
        origin="constructed (models lowdb-style proxy chains)",
        construct="proxy-traps",
        justification="Proxy get/set/has traps expose members invisible to static tooling",
        files={"proxy.js": '''// KNOWN PUBLIC SURFACE (conventional API): store.get, store.set, store.has.
// All three are served by Proxy traps over a plain target (no static def).
const target = {};
const store = new Proxy(target, {
  get(t, key) { return key in t ? t[key] : undefined; },
  set(t, key, v) { t[key] = v; return true; },
  has(t, key) { return key in t; },
});
module.exports = { store };
'''},
        surface=[], runtime_replaced=[],
    ),
    dict(
        id="js-cjs-dynamic-require", arm="js",
        origin="constructed (models CommonJS lazy adapter loading)",
        construct="dynamic-require",
        justification="require(modules[name]) computed at runtime — import graph not static",
        files={"loader.js": '''// KNOWN PUBLIC SURFACE (conventional API): load("json"|"xml"|"yaml").
// The adapter modules are resolved by require() with a runtime-computed key.
const modules = { json: "./adapters/json", xml: "./adapters/xml", yaml: "./adapters/yaml" };
function load(kind) {
  const p = modules[kind];
  if (!p) throw new Error("unknown kind: " + kind);
  return require(p);
}
module.exports = { load };
'''},
        surface=[], runtime_replaced=[],
    ),
    dict(
        id="js-exports-monkeypatch", arm="js",
        origin="constructed (models express middleware export patching at require time)",
        construct="exports-monkeypatch",
        justification="require side-effect reassigns another module's exports member",
        files={"vendor.js": '''// KNOWN PUBLIC SURFACE (conventional API): vendor.fetch, vendor.render.
function fetch(url) { return { url, ok: true }; }
function render(obj) { return String(obj); }
module.exports = { fetch, render };
''', "patch.js": '''// Import side-effect: replaces vendor.fetch (documented runtime API).
const vendor = require("./vendor");
const orig = vendor.fetch;
vendor.fetch = function (url, opts) { return orig(url); };
'''},
        surface=[], runtime_replaced=[],
    ),
    dict(
        id="js-defineproperty-accessors", arm="js",
        origin="constructed (models Vue 2 reactive getter/setter sprawl)",
        construct="defineproperty-accessors",
        justification="Object.defineProperty getter/setter pairs fabricate the public surface",
        files={"reactive.js": '''// KNOWN PUBLIC SURFACE (conventional API): state.count, state.name.
// Both are fabricated at import time via Object.defineProperty accessors.
const state = {};
let _count = 0;
Object.defineProperty(state, "count", {
  get() { return _count; },
  set(v) { _count = v; },
});
module.exports = { state };
'''},
        surface=[], runtime_replaced=[],
    ),
]

KNOWN_STATIC = {"module", "class", "property"}


def sha12(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


def df_free_kb():
    out = subprocess.run(["df", "-k", "/tmp"], capture_output=True, text=True).stdout
    return int(out.strip().splitlines()[-1].split()[3])


def check_df(stage):
    kb = df_free_kb()
    if kb < DF_FLOOR_KB:
        raise OSError(122, "df floor hit at %s: %d KiB free" % (stage, kb))
    return kb


def write_fixtures():
    """Materialise every fixture package into the scratch tree."""
    roots = []
    for fx in FIXTURES:
        root = os.path.join(SCRATCH, "fixtures", fx["id"])
        if os.path.exists(root):
            shutil.rmtree(root)
        for rel, src in fx["files"].items():
            p = os.path.join(root, rel)
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write(src)
        roots.append((fx, root))
    return roots


def classify(fx, contract):
    """Mechanical per-name classification per the frozen rubric. Returns rows."""
    slots = contract.slots
    rows = []
    for name in fx["surface"]:
        slot = slots.get(name)
        ty = slot.ty if slot is not None else None
        if slot is not None and name in fx["runtime_replaced"]:
            rows.append((name, "stale:%s" % ty, 0, "monkeypatch-blind"))
        elif slot is None:
            rows.append((name, "absent", 0, "unsupported-construct:%s" % fx["construct"]))
        elif ty == "const:value":
            rows.append((name, ty, 1, "dynamic-binding-uninterpreted"))
        elif ty == "dyn":
            rows.append((name, ty, 2, "dynamic-service-declared"))
        elif ty in KNOWN_STATIC or ty.startswith("pyfn:") or (ty.startswith("const:") and ty != "const:value"):
            rows.append((name, ty, None, "known"))  # None grade = known slot
        else:
            rows.append((name, "unrecognized-shape:%s" % ty, 1, "dynamic-binding-uninterpreted"))
    return rows


def main():
    os.makedirs(SCRATCH, exist_ok=True)
    header = []
    header.append("# wild-pe1 dynamic-language arm — results (generated by experiments/dynamic_arm.py)")
    header.append("# PRE-REGISTERED: fixture list (14: 10 python measurable + 4 js unsupported-extractor),")
    header.append("#   rubric (0=none, 1=mechanism, 2=mechanism+locus), rates and decision rule were frozen")
    header.append("#   in dynamic_arm.py BEFORE any extraction ran (see its header); no post-hoc fixture swaps.")
    header.append("# RED capture: no fixture matrix existed before this file (/tmp/wild-pe1-scratch/red_capture.txt).")
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    header.append("# date: %s | scratch: %s" % (now, SCRATCH))
    header.append("# python: %s" % sys.version.split()[0])
    header.append("# extractor identity (measurement only, unmodified): prototype/wild_proto.py sha256:%s,"
                  " prototype/wild_sim.py sha256:%s" % (sha12(os.path.join(REPO, "prototype", "wild_proto.py")),
                                                        sha12(os.path.join(REPO, "prototype", "wild_sim.py"))))
    try:
        pre = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        header.append("# provenance: HEAD (pre-registration commit) = %s" % pre)
    except Exception as e:  # never fabricate provenance
        header.append("# provenance: git HEAD unavailable (%s)" % e)
    header.append("# invocation: wild_proto.extract_py(root, 'fx') — the prototype Python surface path used by")
    header.append("#   experiments/census.py (sys.path.insert(prototype); import wild_proto). Extract-only:")
    header.append("#   no demand consumer is run in this arm, so reason code incomplete-demand is N/A (pre-registered).")
    header.append("# JS arm: no JS extractor exists in prototype/ (grep evidence at pre-registration) — every JS")
    header.append("#   fixture is recorded unsupported-extractor with N/A rates; no extractor was built (finding).")
    header.append("# fixture count: %d (python measurable: %d, js unsupported-extractor: %d)" % (
        len(FIXTURES), sum(1 for f in FIXTURES if f["arm"] == "python"),
        sum(1 for f in FIXTURES if f["arm"] == "js")))

    sys.path.insert(0, os.path.join(REPO, "prototype"))
    import wild_proto as P  # noqa: imported, never modified (measurement only)

    attempts = 0
    while True:
        try:
            check_df("fixture-write")
            roots = write_fixtures()
            per_fx, agg_unknown, agg_denom, grade_hist = [], 0, 0, {"g0": 0, "g1": 0, "g2": 0, "full": 0}
            for fx, root in roots:
                if fx["arm"] != "python":
                    continue
                check_df("extract-" + fx["id"])
                contract = P.extract_py(root, "fx")
                rows = classify(fx, contract)
                unknown = [r for r in rows if r[2] is not None]
                denom, num = len(fx["surface"]), len(unknown)
                rate = num / denom if denom else 0.0
                fgrade = min(r[2] for r in unknown) if unknown else "full"
                key = ("g%d" % fgrade) if unknown else "full"
                grade_hist[key] += 1
                agg_unknown += num
                agg_denom += denom
                per_fx.append((fx, contract, rows, denom, num, rate, fgrade))
            break
        except OSError as e:
            if e.errno == 122 and attempts == 0:
                attempts += 1
                for d in ("fixtures",):
                    p = os.path.join(SCRATCH, d)
                    if os.path.exists(p):
                        shutil.rmtree(p)  # clean scratch, retry once — then honest BLOCKED
                print("EDQUOT/df-floor at /tmp: cleaned %s, retrying once" % SCRATCH, file=sys.stderr)
                continue
            print("BLOCKED after cleanup+retry: %s (errno=%s)" % (e, e.errno), file=sys.stderr)
            print("df -k /tmp:\n%s" % subprocess.run(["df", "-k", "/tmp"], capture_output=True, text=True).stdout,
                  file=sys.stderr)
            sys.exit(2)

    # ---- render results -----------------------------------------------------
    L = list(header)
    L.append("")
    L.append("## Python arm (measured; per-fixture; unknown rate = numerator unknown / denominator |known surface|)")
    L.append("")
    L.append("fixture | origin | construct | denominator | numerator | unknown rate | slots inventoried | unknown slots (shape -> grade, code) | fixture grade")
    L.append("--- | --- | --- | --- | --- | --- | --- | --- | ---")
    for fx, contract, rows, denom, num, rate, fgrade in per_fx:
        uslots = ", ".join("%s [%s -> g%d, %s]" % (n.rsplit(".", 1)[-1], sh, g, c)
                           for n, sh, g, c in rows if g is not None) or "-"
        L.append("%s | %s | %s | %d | %d | %d/%d = %.2f | %d | %s | %s" % (
            fx["id"], fx["origin"].split(" (")[0], fx["construct"], denom, num, num, denom, rate,
            len(contract.slots), uslots, fgrade))
    L.append("")
    agg_rate = (agg_unknown / agg_denom) if agg_denom else 0.0
    n_py = len(per_fx)
    half = (n_py + 1) // 2
    g0_fx = grade_hist["g0"]
    L.append("## Python-arm aggregate")
    L.append("")
    L.append("- aggregate unknown rate = %d / %d = %.2f (numerator: unknown slots summed over the %d python fixtures;"
             " denominator: summed |known surface|)" % (agg_unknown, agg_denom, agg_rate, n_py))
    L.append("- fixture grade distribution: g0 (worst unknown undiagnosed): %d, g1 (mechanism only): %d,"
             " g2 (mechanism+locus): %d, full static coverage: %d (of %d python fixtures)" % (
                 grade_hist["g0"], grade_hist["g1"], grade_hist["g2"], grade_hist["full"], n_py))
    L.append("- refusal behaviour: wild_proto.extract_py never refuses (no complete_inventory machinery) —")
    L.append("  silent omission is the only failure mode on this arm; incomplete-demand is N/A (no demand consumer).")
    L.append("")
    L.append("## JS arm (finding, not measured)")
    L.append("")
    for fx in FIXTURES:
        if fx["arm"] == "js":
            L.append("- %s (%s): unsupported-extractor — no JS extractor exists in the prototype;"
                     " unknown rate N/A (numerator 0 measurable / denominator 0 measurable — not extractable,"
                     " not engineered around per ticket constraint)." % (fx["id"], fx["construct"]))
    L.append("")
    # frozen decision rule (verbatim from the pre-registration)
    if agg_rate >= 0.5 or g0_fx >= half:
        verdict = "impractical"
    elif agg_rate <= 0.2 and g0_fx == 0:
        verdict = "useful"
    else:
        verdict = "inconclusive"
    ev = ("python-arm aggregate unknown rate %d/%d = %.0f%% with %d/%d fixtures carrying a grade-0 (silent,"
          " undiagnosed) unknown; %d/%d grade-2; JS arm adds scope-narrowing evidence: no JS extractor exists"
          " (4/4 fixtures unsupported-extractor), so the dynamic-language arm cannot cover JS at all"
          % (agg_unknown, agg_denom, agg_rate * 100, g0_fx, n_py,
             grade_hist["g2"], n_py, len([f for f in FIXTURES if f["arm"] == "js"])))
    L.append("## Verdict")
    L.append("")
    L.append("VERDICT: %s — evidence: %s." % (verdict.upper() if verdict != "inconclusive" else "INCONCLUSIVE", ev))
    L.append("")
    L.append("(decision rule, pre-registered: impractical iff aggregate rate >= 0.5 or >= half of python fixtures"
             " carry a grade-0 unknown; useful iff rate <= 0.2 and zero grade-0 fixtures; else inconclusive.)")

    out = os.path.join(REPO, "experiments", "dynamic_arm_results.txt")
    with open(out, "w") as f:
        f.write("\n".join(L) + "\n")
    print("wrote %s (%d fixtures, %d python-measurable, aggregate %d/%d = %.2f, verdict %s)" % (
        out, len(FIXTURES), n_py, agg_unknown, agg_denom, agg_rate, verdict))
    return 0


if __name__ == "__main__":
    sys.exit(main())
