# Purpose: Runtime tests for the widen-method-receiver-demands receiver
#   rules (bd wild-8j4): bundle-wide pre-pass, let-bound single-assignment
#   locals, inventoried field access, self/Self in public inherent impls,
#   and hop folding for chains.
# Responsibilities: Exercise the real `wild extract` binary as a
#   subprocess against constructed bundles; group the structurally
#   identical receiver-shape scenarios into parametrized cases so the
#   shared assertion structure lives in one test body, with the genuinely
#   different residuals (trait-impl self, free-fn signature gaps) as
#   separate tests. Assert observable records and exit codes, never
#   implementation internals.
# Rationale: Every unresolved receiver shape must keep the named
#   incomplete-demand gap, and every declared shape must resolve without
#   one; synthetic success or assertion mirroring would prove nothing.

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from test_extract import facts_json, request_record, run_extract, write_bundle

WIDEN_LIB = """pub struct Meter { pub v: u32 }
impl Meter {
    pub fn new() -> Meter { Meter { v: 0 } }
    pub fn tick(self) -> Meter { self }
    pub fn double(&mut self) { self.v *= 2; }
    pub fn bump(&mut self) { self.v += 1; }
}
pub struct Store { pub meter: Meter }
impl Store {
    pub fn new() -> Store { Store { meter: Meter::new() } }
}
"""

HELPERS_RS = (
    "pub struct Widget;\nimpl Widget {\n"
    "    pub fn new() -> Widget { Widget }\n"
    "    pub fn spin(&mut self) {}\n}\n"
)

STORE_RS = (
    "pub struct Meter { pub v: u32 }\nimpl Meter {\n"
    "    pub fn new() -> Meter { Meter { v: 0 } }\n"
    "    pub fn bump(&mut self) { self.v += 1; }\n}\n"
    "pub struct Store { pub meter: Meter }\nimpl Store {\n"
    "    pub fn new() -> Store { Store { meter: Meter::new() } }\n}\n"
)


def widen_files(lib: str, extra: dict[str, str] | None = None) -> dict[str, str]:
    files = {"consumer/src/lib.rs": lib}
    if extra:
        files.update(extra)
    return files


def widen_extract(
    tmp_path: Path, files: dict[str, str]
) -> tuple[int, dict, list[str], str]:
    lib = files.get("consumer/src/lib.rs", "")
    extra = {k: v for k, v in files.items() if k != "consumer/src/lib.rs"}
    bundle = write_bundle(tmp_path / "bundle", consumer_lib=lib)
    for rel, text in extra.items():
        bundle[rel] = text
        dest = tmp_path / "bundle" / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)
    proc = run_extract(request_record(tmp_path / "bundle", bundle), tmp_path / "facts")
    report = facts_json(tmp_path / "facts", "report.json")
    reasons = [d.get("reason", "") for d in report["diagnostics"]]
    demand = json.dumps(facts_json(tmp_path / "facts", "demand.json"))
    return proc.returncode, report, reasons, demand


RESOLVES_CASES = [
    (
        "let-bound-constructor-local",
        # rule 2: a let-bound local whose initializer is a resolved call
        # with a recorded return type feeds the receiver, including a
        # `let mut` binding that is never reassigned.
        WIDEN_LIB
        + "pub fn drive() -> u32 { let r = Meter::new(); let mut m = Meter::new(); r.tick(); m.bump(); 7 }\n",
        None,
        ["consumer::Meter::tick", "consumer::Meter::bump"],
    ),
    (
        "field-access-receiver",
        # rule 3: a field-access receiver resolves via the inventoried
        # public field type, directly (`s.meter.double()`) and through a
        # let-bound field initializer (`let f = s.meter; f.bump()`).
        WIDEN_LIB
        + "pub fn drive() -> u32 { let s = Store::new(); s.meter.double(); let f = s.meter; f.bump(); 7 }\n",
        None,
        ["consumer::Meter::double", "consumer::Meter::bump"],
    ),
    (
        "self-receiver-in-inherent-impl",
        # rule 4: `self` inside a public inherent impl on a named path
        # type resolves to that impl's type, creating the demand against
        # the inventoried impl-method slot.
        WIDEN_LIB
        + "impl Meter { pub fn double_then(&mut self) { self.double(); self.bump(); } }\n",
        None,
        ["consumer::Meter::double", "consumer::Meter::bump"],
    ),
    (
        "chain-with-recorded-returns",
        # rule 5: chains fold hop-by-hop through recorded return types;
        # every hop's demand is recorded with no incomplete-demand gap.
        WIDEN_LIB
        + "pub fn drive() -> u32 { Meter::new().tick().double(); Meter::new().tick().tick().bump(); 7 }\n",
        None,
        ["consumer::Meter::double", "consumer::Meter::bump", "consumer::Meter::tick"],
    ),
    (
        "cross-file-constructor",
        # rule 1: the pre-pass is bundle-wide — a constructor declared in
        # a public non-inline module file feeds let-bound receiver flow
        # even when the use site precedes the `mod` declaration in the
        # crate root (the old per-file scan missed it).
        WIDEN_LIB
        + "pub fn drive() -> u32 { let w = helpers::Widget::new(); w.spin(); 7 }\npub mod helpers;\n",
        {"consumer/src/helpers.rs": HELPERS_RS},
        ["consumer::helpers::Widget::spin", "consumer::helpers::Widget::new"],
    ),
    (
        "cross-file-field-type",
        # rule 1: public struct-field types recorded bundle-wide — a
        # struct and its field's type declared in a public non-inline
        # module file feed field-access receivers from the crate root.
        WIDEN_LIB
        + "pub fn drive() -> u32 { let s = store::Store::new(); s.meter.bump(); 7 }\npub mod store;\n",
        {"consumer/src/store.rs": STORE_RS},
        ["consumer::store::Meter::bump", "consumer::store::Store::new"],
    ),
]

GAP_CASES = [
    (
        "reassigned-local",
        # rule 2 residual: a re-assigned local is outside the
        # single-assignment rule — the post-assignment call keeps the
        # honest receiver gap.
        WIDEN_LIB
        + "pub fn drive() -> u32 { let mut r = Meter::new(); r = Meter::new(); r.tick(); 7 }\n",
        None,
        [(".tick", "receiver")],
    ),
    (
        "unknown-or-private-field",
        # rule 3 residual: unknown and non-public fields stay unresolved —
        # the receiver gap names the receiver, never a silent success.
        WIDEN_LIB.replace(
            "pub struct Store { pub meter: Meter }",
            "pub struct Store { pub meter: Meter, secret: Meter }",
        )
        + "pub fn drive() -> u32 { let s = Store::new(); s.nope.tick(); s.secret.bump(); 7 }\n",
        None,
        [(".tick", "receiver"), (".bump", "receiver")],
    ),
    (
        "tuple-index-and-literal-initializer",
        # residuals: tuple indexing and an initializer outside the
        # resolved-call shape keep the receiver gap naming the receiver.
        WIDEN_LIB
        + "pub fn drive() -> u32 { let pair = (Meter::new(), Meter::new()); let n = 5; pair.0.tick(); n.bump(); 7 }\n",
        None,
        [("pair . 0", "receiver"), ("`n`", "receiver")],
    ),
]


@pytest.mark.parametrize("case", RESOLVES_CASES, ids=[c[0] for c in RESOLVES_CASES])
def test_widen_receiver_shape_resolves(tmp_path, case):
    _case_id, lib, extra, demands = case
    rc, report, reasons, demand = widen_extract(tmp_path, widen_files(lib, extra))
    assert rc == 0, f"receiver shape must resolve, not gap: rc={rc} {reasons}"
    assert report["complete_inventory"] is True, reasons
    assert reasons == [], reasons
    for wanted in demands:
        assert wanted in demand, demand


@pytest.mark.parametrize("case", GAP_CASES, ids=[c[0] for c in GAP_CASES])
def test_widen_receiver_residual_keeps_gap(tmp_path, case):
    _case_id, lib, extra, fragments = case
    rc, report, reasons, _demand = widen_extract(tmp_path, widen_files(lib, extra))
    assert rc == 1, f"residual receiver shape must gap, not resolve: {reasons}"
    assert report["complete_inventory"] is False
    for a, b in fragments:
        assert any(a in r and b in r for r in reasons), reasons


def test_widen_self_receiver_in_trait_impl_keeps_gap(tmp_path):
    # rule 4 residual: trait impls stay outside the profile (D3) —
    # the unsupported-construct gap stays AND `self` keeps the receiver
    # gap (never approximated into a resolution).
    lib = (
        WIDEN_LIB
        + "trait Go { fn go(&mut self); }\nimpl Go for Meter { fn go(&mut self) { self.bump(); } }\n"
    )
    rc, report, reasons, _demand = widen_extract(tmp_path, widen_files(lib))
    assert rc == 1, "trait-impl self must gap"
    assert report["complete_inventory"] is False
    codes = {d["code"] for d in report["diagnostics"]}
    assert "unsupported-construct" in codes, reasons
    assert any(".bump" in r and "receiver" in r for r in reasons), reasons


def test_widen_let_bound_free_fn_and_cross_file_fn_resolves(tmp_path):
    # rule 1+2: a let-bound local initialized from a recorded-return
    # free fn resolves same-file and cross-file (the pre-pass records
    # public free fns bundle-wide, not just constructors). The free
    # fn's own non-scalar signature keeps its incumbent wild-73j
    # unsupported-construct gap — the receiver gap must be gone and
    # the demands recorded, but complete inventory stays refused by
    # that unrelated signature disclosure.
    lib = (
        WIDEN_LIB
        + "pub fn make_meter() -> Meter { Meter::new() }\n"
        + "pub fn drive() -> u32 { let a = crate::make_meter(); a.bump(); let b = helpers::make_widget(); b.spin(); 7 }\n"
        + "pub mod helpers;\n"
    )
    extra = {
        "consumer/src/helpers.rs": (
            "pub struct Widget;\nimpl Widget {\n"
            "    pub fn spin(&mut self) {}\n}\n"
            "pub fn make_widget() -> Widget { Widget }\n"
        )
    }
    _rc, report, reasons, demand = widen_extract(
        tmp_path, widen_files(lib, extra)
    )
    assert report["complete_inventory"] is False, (
        "the free fn's non-scalar signature keeps its wild-73j gap"
    )
    assert all("receiver" not in r for r in reasons), (
        f"no receiver gap may remain: {reasons}"
    )
    assert any("make_meter" in r for r in reasons), reasons
    assert "consumer::Meter::bump" in demand
    assert "consumer::helpers::Widget::spin" in demand
