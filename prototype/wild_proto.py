#!/usr/bin/env python3
"""wild prototype: real extractors and demand extraction over real projects.

Rust:   public API of a crate (pub mod/fn/struct/enum/trait/impl/const/type, simple re-exports)
Python: module-level API of a package (defs, classes, methods, constants, from-import aliases)
Demand: what a consumer's source actually references in the provider.

Limits (deliberate, reported by the experiments): no type inference, so method calls on values
are not demand; Rust fn signatures compare by normalised text; Python return types and
behaviour are not modelled.
"""
import ast, json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wild_sim as A
from wild_sim import Slot, Contract, shape_check

# ------------------------------------------------------------------ Python signature subtyping
def py_sub(new, old):
    """True if a callable with signature `new` accepts every call that `old` accepts."""
    npos, opos = new["pos"], old["pos"]
    nnames = {n for n, _ in npos} | {n for n, _ in new["kwonly"]}
    if len(npos) < len(opos) and not new["vararg"]: return False
    for i, (n, d) in enumerate(opos):
        if i < len(npos):
            if i >= old["posonly"] and npos[i][0] != n: return False
            if d and not npos[i][1]: return False
        elif not new["vararg"]: return False
        if i >= old["posonly"] and n not in nnames and not new["kwarg"]: return False
    for n, d in old["kwonly"]:
        match = [x for x in new["kwonly"] + npos if x[0] == n]
        if not match and not new["kwarg"]: return False
        if match and d and not match[0][1]: return False
    oldnames = {n for n, _ in opos} | {n for n, _ in old["kwonly"]}
    for n, d in npos + new["kwonly"]:
        if n not in oldnames and not d: return False           # new required parameter
    if old["vararg"] and not new["vararg"]: return False
    if old["kwarg"] and not new["kwarg"]: return False
    return True

_orig_sub = A.sub
def _sub(a, b):
    if a == b: return True
    if "dyn" in (a, b) and (a.startswith(("const:", "dyn")) and b.startswith(("const:", "dyn"))): return True
    if a.startswith("pyfn:") and b.startswith("pyfn:"):
        return py_sub(json.loads(a[5:]), json.loads(b[5:]))
    return _orig_sub(a, b)
A.sub = _sub

def scoped_failures(dev, cand, demand):
    """Names in `demand` whose slot does not accrete from dev to cand, with reasons."""
    out = []
    for n in sorted(demand):
        ok, why = shape_check(dev, cand, {n})
        if not ok: out.append((n, why))
    return out

# ------------------------------------------------------------------ Python extractor
def _sig(args, skip_first=False):
    pos = [(a.arg, False) for a in args.posonlyargs + args.args]
    nd = len(args.defaults)
    for i in range(nd): pos[len(pos) - nd + i] = (pos[len(pos) - nd + i][0], True)
    posonly = len(args.posonlyargs)
    if skip_first and pos: pos = pos[1:]; posonly = max(0, posonly - 1)
    kwonly = [(a.arg, d is not None) for a, d in zip(args.kwonlyargs, args.kw_defaults)]
    return "pyfn:" + json.dumps({"pos": pos, "posonly": posonly, "kwonly": kwonly,
                                 "vararg": args.vararg is not None, "kwarg": args.kwarg is not None}, sort_keys=True)

def _defs(body, into, prefix):
    for st in body:
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)) and st.name == "__getattr__" and not prefix:
            for sub_ in ast.walk(st):                              # module-level __getattr__: names it explicitly serves
                if isinstance(sub_, ast.Compare) and isinstance(sub_.left, ast.Name) and sub_.left.id == "name":
                    for c in sub_.comparators:
                        if isinstance(c, ast.Constant) and isinstance(c.value, str): into[c.value] = Slot("out", "dyn")
                        if isinstance(c, (ast.Tuple, ast.Set, ast.List)):
                            for e in c.elts:
                                if isinstance(e, ast.Constant) and isinstance(e.value, str): into[e.value] = Slot("out", "dyn")
            continue
        if isinstance(st, (ast.FunctionDef, ast.AsyncFunctionDef)):
            decos = {ast.unparse(d) for d in st.decorator_list}
            if "property" in decos or any(d.endswith(".setter") for d in decos): into[f"{prefix}{st.name}"] = Slot("out", "property")
            else: into[f"{prefix}{st.name}"] = Slot("out", _sig(st.args, skip_first=("staticmethod" not in decos and prefix.count(".") and True)))
        elif isinstance(st, ast.ClassDef):
            into[f"{prefix}{st.name}"] = Slot("out", "class")
            inner = {}
            _defs(st.body, inner, f"{prefix}{st.name}.")
            into.update(inner)
        elif isinstance(st, (ast.Assign, ast.AnnAssign)):
            targets = st.targets if isinstance(st, ast.Assign) else [st.target]
            for t in targets:
                if isinstance(t, ast.Name) and (t.id == "__version__" or not (t.id.startswith("__") and t.id.endswith("__"))):
                    v = getattr(st, "value", None)
                    into[f"{prefix}{t.id}"] = Slot("out", "const:" + (type(v.value).__name__ if isinstance(v, ast.Constant) else "value"))
        elif isinstance(st, (ast.If, ast.Try)):
            for blk in ([st.body, st.orelse] if isinstance(st, ast.If) else [st.body, st.orelse, st.finalbody] + [h.body for h in st.handlers]):
                _defs(blk, into, prefix)

def extract_py(root_dir, pkg):
    """root_dir contains the package directory `pkg`."""
    mods, imports = {}, []
    base = os.path.join(root_dir, pkg)
    for dp, _, fs in os.walk(base):
        for f in fs:
            if not f.endswith(".py"): continue
            p = os.path.join(dp, f)
            name = os.path.relpath(p, root_dir)[:-3].replace(os.sep, ".")
            is_pkg = name.endswith(".__init__"); name = name[:-9] if is_pkg else name
            try: tree = ast.parse(open(p, encoding="utf-8", errors="replace").read())
            except SyntaxError: continue
            own = {}; _defs(tree.body, own, "")
            mods[name] = own
            for st in ast.walk(tree):
                if isinstance(st, ast.ImportFrom):
                    parts = name.split(".") if is_pkg else name.split(".")[:-1]
                    if st.level: parts = parts[: len(parts) - (st.level - 1)]
                    tgt = ".".join(parts + ([st.module] if st.module else [])) if st.level else (st.module or "")
                    for al in st.names: imports.append((name, al.asname or al.name, tgt, al.name))
    slots = {}
    for m, own in mods.items():
        slots[m] = Slot("out", "module")
        for k, s in own.items(): slots[f"{m}.{k}"] = s
    for _ in range(3):                                            # alias fixpoint (re-exports)
        for m, local, tgt, orig in imports:
            if not tgt.startswith(pkg) or orig == "*": continue
            key = f"{m}.{local}"
            if key in slots: continue
            if f"{tgt}.{orig}" in mods: slots[key] = Slot("out", "module")
            elif f"{tgt}.{orig}" in slots:
                for k, s in list(slots.items()):
                    if k == f"{tgt}.{orig}" or k.startswith(f"{tgt}.{orig}."):
                        slots.setdefault(f"{m}.{local}" + k[len(f'{tgt}.{orig}'):], s)
    return Contract(slots)

def _guard(node):
    names = set()
    for h in node.handlers:
        if h.type is None: names.add("*")
        else: names |= {n.id for n in ast.walk(h.type) if isinstance(n, ast.Name)}
    return bool(names & {"ImportError", "ModuleNotFoundError", "AttributeError", "Exception", "*"})

def demand_py(consumer_dir, croot, proot, dev, calls=None):
    """Dotted paths into `proot` that consumer package `croot` references (outside import guards)."""
    raw, unresolved = set(), set()
    for dp, _, fs in os.walk(os.path.join(consumer_dir, croot)):
        for f in fs:
            if not f.endswith(".py"): continue
            try: tree = ast.parse(open(os.path.join(dp, f), encoding="utf-8", errors="replace").read())
            except SyntaxError: continue
            amap = {}
            def imports(node, opt):
                for ch in ast.iter_child_nodes(node):
                    o = opt or (isinstance(ch, ast.Try) and _guard(ch) and False)
                    if isinstance(ch, ast.Try) and _guard(ch):
                        for b in ch.body: imports_stmt(b, True)
                        for part in (ch.orelse, ch.finalbody, *[h.body for h in ch.handlers]):
                            for b in part: imports_stmt(b, opt)
                    else: imports_stmt(ch, opt)
            def imports_stmt(st, opt):
                if isinstance(st, ast.Import):
                    for al in st.names:
                        if al.name == proot or al.name.startswith(proot + "."):
                            amap[al.asname or al.name.split(".")[0]] = al.name if al.asname else proot
                            if not opt: raw.add(al.name)
                elif isinstance(st, ast.ImportFrom) and st.level == 0 and st.module and (st.module == proot or st.module.startswith(proot + ".")):
                    for al in st.names:
                        full = st.module if al.name == "*" else f"{st.module}.{al.name}"
                        amap[al.asname or al.name] = full
                        if not opt: raw.add(full)
                elif isinstance(st, ast.Try) and _guard(st):
                    for b in st.body: imports_stmt(b, True)
                    for part in (st.orelse, st.finalbody, *[h.body for h in st.handlers]):
                        for b in part: imports_stmt(b, opt)
                else:
                    for ch in ast.iter_child_nodes(st):
                        if isinstance(ch, ast.stmt): imports_stmt(ch, opt)
            for st in tree.body: imports_stmt(st, False)
            def resolve(f):
                if isinstance(f, ast.Name): return amap.get(f.id)
                if isinstance(f, ast.Attribute):
                    cur, attrs = f, []
                    while isinstance(cur, ast.Attribute): attrs.append(cur.attr); cur = cur.value
                    if isinstance(cur, ast.Name) and cur.id in amap: return amap[cur.id] + "." + ".".join(reversed(attrs))
                return None
            def chains(node, opt):
                if calls is not None and isinstance(node, ast.Call):
                    p = resolve(node.func)
                    if p:
                        calls.setdefault(p, []).append((sum(not isinstance(a, ast.Starred) for a in node.args),
                            frozenset(k.arg for k in node.keywords if k.arg), any(isinstance(a, ast.Starred) for a in node.args),
                            any(k.arg is None for k in node.keywords)))
                if isinstance(node, ast.Try) and _guard(node):
                    for b in node.body: chains(b, True)
                    for part in (node.orelse, node.finalbody, *[h.body for h in node.handlers]):
                        for b in part: chains(b, opt)
                    return
                if isinstance(node, ast.Attribute):
                    cur, attrs = node, []
                    while isinstance(cur, ast.Attribute): attrs.append(cur.attr); cur = cur.value
                    if isinstance(cur, ast.Name) and cur.id in amap:
                        if not opt: raw.add(amap[cur.id] + "." + ".".join(reversed(attrs)))
                    else: chains(cur, opt)
                    return
                for ch in ast.iter_child_nodes(node): chains(ch, opt)
            chains(tree, False)
    demand = set()
    for p in raw:
        parts = p.split(".")
        for k in range(len(parts), 0, -1):
            if ".".join(parts[:k]) in dev.slots: demand.add(".".join(parts[:k])); break
        else: unresolved.add(p)
    return demand, unresolved

# ------------------------------------------------------------------ Rust extractor
def _rust_parser():
    import tree_sitter_rust as tsr
    from tree_sitter import Language, Parser
    lang = Language(tsr.language())
    try: return Parser(lang)
    except TypeError:
        p = Parser(); p.set_language(lang); return p

_P = None
def rparse(src):
    global _P
    if _P is None: _P = _rust_parser()
    return _P.parse(src)

def tx(n): return n.text.decode("utf8", "replace") if n is not None else ""
def norm(s): return " ".join(s.split())
def is_pub(n): return any(c.type == "visibility_modifier" and tx(c) == "pub" for c in n.children)

def rsig(n):
    mods = " ".join(tx(c) for c in n.children if c.type == "function_modifiers")
    gen = norm(tx(n.child_by_field_name("type_parameters")))
    ps = []
    prm = n.child_by_field_name("parameters")
    if prm is not None:
        for c in prm.named_children:
            if c.type == "parameter": ps.append(norm(tx(c.child_by_field_name("type"))))
            elif c.type in ("self_parameter", "variadic_parameter"): ps.append(norm(tx(c)))
    ret = norm(tx(n.child_by_field_name("return_type"))) or "()"
    where = norm(tx(next((c for c in n.children if c.type == "where_clause"), None)))
    return f"rsfn:{mods} fn{gen}({','.join(ps)})->{ret} {where}".strip()

class Crate:
    def __init__(self, root):
        self.root, self.table, self.reexports = root, {}, []
        self.load(os.path.join(root, "src", "lib.rs"), [], os.path.join(root, "src"), True)
        self.slots = {}
        self.finish()

    def put(self, mp, key, slot, public):
        self.table.setdefault(tuple(mp), {})[key] = (slot, public)

    def load(self, path, mp, dirpath, public):
        if not os.path.exists(path): return
        self.items(rparse(open(path, "rb").read()).root_node.children, mp, dirpath, public, path)

    def items(self, nodes, mp, dirpath, public, path):
        attrs = []
        for n in nodes:
            if n.type == "attribute_item": attrs.append(norm(tx(n))); continue
            a, attrs = " ".join(attrs), []
            if "cfg(test)" in a: continue
            pub = is_pub(n) and public
            name = tx(n.child_by_field_name("name"))
            q = "::".join(mp + [name]) if name else ""
            if n.type == "mod_item":
                body = n.child_by_field_name("body")
                sub = mp + [name]
                self.put(mp, name, Slot("out", "module"), pub)
                if body is not None: self.items(body.children, sub, os.path.join(dirpath, name), pub, path)
                else:
                    for cand, nd in ((os.path.join(dirpath, name + ".rs"), os.path.join(dirpath, name)),
                                     (os.path.join(dirpath, name, "mod.rs"), os.path.join(dirpath, name))):
                        if os.path.exists(cand): self.load(cand, sub, nd, pub); break
            elif n.type == "function_item": self.put(mp, name, Slot("out", rsig(n)), pub)
            elif n.type == "struct_item":
                gen = norm(tx(n.child_by_field_name("type_parameters")))
                self.put(mp, name, Slot("out", "struct" + gen), pub)
                body = n.child_by_field_name("body")
                fields, allpub = [], True
                if body is not None and body.type == "field_declaration_list":
                    for f in body.named_children:
                        if f.type != "field_declaration": continue
                        fn = tx(f.child_by_field_name("name")); ft = norm(tx(f.child_by_field_name("type")))
                        fields.append(fn); allpub &= is_pub(f)
                        if is_pub(f): self.put(mp, f"{name}.{fn}", Slot("out", "field:" + ft), pub)
                elif body is not None:
                    pend, i = False, 0
                    for f in body.children:
                        if f.type == "visibility_modifier": pend = tx(f) == "pub"
                        elif f.is_named and f.type != "attribute_item":
                            fields.append(str(i)); allpub &= pend
                            if pend: self.put(mp, f"{name}.{i}", Slot("out", "field:" + norm(tx(f))), pub)
                            i += 1; pend = False
                if fields and allpub and "non_exhaustive" not in a:
                    self.put(mp, f"{name}#fields", Slot("out", "record", frozenset(fields), True), pub)
            elif n.type == "enum_item":
                self.put(mp, name, Slot("out", "enum" + norm(tx(n.child_by_field_name("type_parameters")))), pub)
                vs = []
                body = n.child_by_field_name("body")
                for v in (body.named_children if body is not None else []):
                    if v.type != "enum_variant": continue
                    vn = tx(v.child_by_field_name("name")); vs.append(vn)
                    payload = norm(tx(v.child_by_field_name("body"))) or "unit"
                    self.put(mp, f"{name}::{vn}", Slot("out", "variant:" + payload), pub)
                self.put(mp, f"{name}#variants", Slot("out", "sum", frozenset(vs), "non_exhaustive" not in a), pub)
            elif n.type == "trait_item":
                self.put(mp, name, Slot("out", "trait" + norm(tx(n.child_by_field_name("type_parameters"))) + norm(tx(n.child_by_field_name("bounds")))), pub)
                body = n.child_by_field_name("body")
                for m in (body.named_children if body is not None else []):
                    mn = tx(m.child_by_field_name("name"))
                    if m.type == "function_signature_item": self.put(mp, f"{name}::{mn}", Slot("in", rsig(m), need="required"), pub)
                    elif m.type == "function_item": self.put(mp, f"{name}::{mn}", Slot("out", rsig(m)), pub)
                    elif m.type in ("associated_type", "const_item"): self.put(mp, f"{name}::{mn}", Slot("out", m.type), pub)
            elif n.type in ("const_item", "static_item"):
                self.put(mp, name, Slot("out", "const:" + norm(tx(n.child_by_field_name("type")))), pub)
            elif n.type == "type_item":
                self.put(mp, name, Slot("out", "type:" + norm(tx(n.child_by_field_name("type")))), pub)
            elif n.type == "macro_definition" and "macro_export" in a:
                self.put([], "macro::" + name, Slot("out", "macro"), True)
            elif n.type == "impl_item":
                ty = re.match(r"[\w:]+", norm(tx(n.child_by_field_name("type")))); ty = ty.group(0).split("::")[-1] if ty else "?"
                trait = n.child_by_field_name("trait")
                body = n.child_by_field_name("body")
                if trait is not None:
                    self.put(mp, f"{ty}#impl::{norm(tx(trait))}", Slot("out", "impl"), public)
                elif body is not None:
                    for m in body.named_children:
                        if m.type == "function_item" and is_pub(m):
                            self.put(mp, f"{ty}::{tx(m.child_by_field_name('name'))}", Slot("out", rsig(m)), public)
                        elif m.type == "const_item" and is_pub(m):
                            self.put(mp, f"{ty}::{tx(m.child_by_field_name('name'))}", Slot("out", "const:" + norm(tx(m.child_by_field_name('type')))), public)
            elif n.type == "use_declaration" and pub:
                self.reexports.append((tuple(mp), n.child_by_field_name("argument")))

    def finish(self):
        for mp, names in self.table.items():
            if mp and not self._pub_mod(mp): continue
            for key, (slot, public) in names.items():
                if public: self.slots["::".join(list(mp) + [key])] = slot
        for mp, arg in self.reexports:                          # simple re-exports
            for path, alias, glob in self._use(arg, ()):
                tgt = self._resolve(mp, path)
                if glob:
                    for k, s in list(self.slots.items()):
                        if k.startswith("::".join(tgt) + "::"): self.slots.setdefault("::".join(list(mp) + [k[len("::".join(tgt)) + 2:]]), s)
                else:
                    name = alias or path[-1]; tk = "::".join(tgt)
                    for k, s in list(self.slots.items()):
                        if k == tk or k.startswith(tk + "::") or k.startswith(tk + ".") or k.startswith(tk + "#"):
                            self.slots.setdefault("::".join(list(mp) + [name]) + k[len(tk):], s)

    def _pub_mod(self, mp):
        for i in range(1, len(mp) + 1):
            parent, name = tuple(mp[:i - 1]), mp[i - 1]
            ent = self.table.get(parent, {}).get(name)
            if ent is None or not ent[1]: return False
        return True

    def _resolve(self, mp, path):
        p = list(path)
        if p[0] == "crate": return tuple(p[1:])
        if p[0] == "self": return tuple(list(mp) + p[1:])
        if p[0] == "super": return tuple(list(mp[:-1]) + p[1:])
        return tuple(list(mp) + p)

    def _use(self, n, prefix):
        out = []
        if n is None: return out
        t = n.type
        if t in ("identifier", "scoped_identifier", "self", "crate", "super"):
            out.append((tuple(prefix) + tuple(tx(n).split("::")), None, False))
        elif t == "use_as_clause":
            for p, _, _ in self._use(n.child_by_field_name("path"), prefix):
                out.append((p, tx(n.child_by_field_name("alias")), False))
        elif t == "use_wildcard":
            inner = next((c for c in n.named_children), None)
            for p, _, _ in self._use(inner, prefix): out.append((p, None, True))
        elif t == "scoped_use_list":
            pn = n.child_by_field_name("path"); pre = tuple(prefix) + (tuple(tx(pn).split("::")) if pn is not None else ())
            for c in n.child_by_field_name("list").named_children: out += self._use(c, pre)
        elif t == "use_list":
            for c in n.named_children: out += self._use(c, prefix)
        return [(tuple(x for x in p if x != "self") or p, a, g) for p, a, g in out]

def extract_rust(crate_dir):
    return Contract(Crate(crate_dir).slots)

def iter_nodes(n):
    yield n
    for ch in n.children:
        yield from iter_nodes(ch)

def demand_rust(consumer_src_dirs, crate_alias, dev):
    """Paths under `crate_alias::` referenced by the consumer, resolved through its `use` aliases."""
    raw = set()
    for d in consumer_src_dirs:
        for dp, _, fs in os.walk(d):
            for f in fs:
                if not f.endswith(".rs"): continue
                tree = rparse(open(os.path.join(dp, f), "rb").read()).root_node
                helper = Crate.__new__(Crate)
                amap = {}
                def walk_use(n):
                    for ch in n.children:
                        if ch.type == "use_declaration":
                            for path, alias, glob in helper._use(ch.child_by_field_name("argument"), ()):
                                if path and path[0] == crate_alias:
                                    full = path[1:]
                                    if glob: raw.add("::".join(full) + "::*")
                                    elif full:
                                        raw.add("::".join(full)); amap[alias or full[-1]] = full
                        else: walk_use(ch)
                walk_use(tree)
                def walk_paths(n):
                    if n.type in ("scoped_identifier", "scoped_type_identifier"):
                        parts = tx(n).split("::")
                        if parts[0] == crate_alias: raw.add("::".join(parts[1:]))
                        elif parts[0] in amap: raw.add("::".join(list(amap[parts[0]]) + parts[1:]))
                        return
                    for ch in n.children: walk_paths(ch)
                walk_paths(tree)
                # struct literals / patterns demand the field set; enum patterns demand the variant set
                def full(parts):
                    if parts[0] == crate_alias: return parts[1:]
                    if parts[0] in amap: return list(amap[parts[0]]) + parts[1:]
                    return None
                def walk_shapes(n, in_pat):
                    if n.type in ("struct_expression", "struct_pattern"):
                        nm = n.child_by_field_name("name") or n.child_by_field_name("type")
                        if nm is not None:
                            fp = full(tx(nm).split("::"))
                            if fp: raw.add("::".join(fp) + "#fields")
                    if n.type == "match_arm" or n.type == "let_condition":
                        in_pat = True
                    if in_pat and n.type in ("scoped_identifier", "scoped_type_identifier"):
                        parts = tx(n).split("::")
                        fp = full(parts)
                        if fp and len(fp) >= 2: raw.add("::".join(fp[:-1]) + "#variants")
                    for ch in n.children:
                        walk_shapes(ch, in_pat and ch.type != "block" and ch.field_name_for_child(0) is None if False else in_pat)
                for arm in [x for x in iter_nodes(tree) if x.type == "match_arm"]:
                    pat = arm.child_by_field_name("pattern")
                    if pat is not None: walk_shapes(pat, True)
                for x in iter_nodes(tree):
                    if x.type in ("struct_expression", "struct_pattern"): walk_shapes(x, False)
    demand, unresolved = set(), set()
    for p in raw:
        if p.endswith("::*"):
            if p[:-3] in dev.slots: demand.add(p[:-3])
            continue
        parts = p.split("::")
        for k in range(len(parts), 0, -1):
            cand = "::".join(parts[:k])
            if cand in dev.slots: demand.add(cand); break
        else: unresolved.add(p)
    return demand, unresolved


def sig_accepts(sig, shape):
    """Does the signature (pyfn json) accept a call of this shape?"""
    npos, kws, star, dstar = shape
    pos, kwonly = sig["pos"], sig["kwonly"]
    if npos > len(pos) and not sig["vararg"]: return False
    names = {n for n, _ in pos[sig["posonly"]:]} | {n for n, _ in kwonly}
    for k in kws:
        if k not in names and not sig["kwarg"]: return False
        if k in [n for n, _ in pos[:npos]]: return False
    if not star and not dstar:
        for i, (n, d) in enumerate(pos):
            if not d and i >= npos and n not in kws: return False
        for n, d in kwonly:
            if not d and n not in kws: return False
    return True

def scoped_failures_calls(dev, cand, demand, calls):
    """Like scoped_failures, but a demanded function is judged by the calls the consumer actually makes."""
    out = []
    for n in sorted(demand):
        d, c = dev.slots.get(n), cand.slots.get(n)
        shapes = calls.get(n)
        if shapes and d is not None and c is not None and d.ty.startswith("pyfn:") and c.ty.startswith("pyfn:"):
            sig = json.loads(c.ty[5:])
            bad = [sh for sh in shapes if not sig_accepts(sig, sh)]
            if bad: out.append((n, f"call shape {bad[0][:2]} not accepted"))
            continue
        ok, why = shape_check(dev, cand, {n})
        if not ok: out.append((n, why))
    return out
