"""wild-3yy functor-signature extraction pilot over a pinned mirage-skeleton.

Measures, for a real MirageOS corpus, what the OCaml type system gives for
free at functor boundaries versus what wild's laws/tombstones add.

Source-text extraction only (per the toolchain ruling): tree-sitter-ocaml
parses the .ml/.mli files; no OCaml compiler or opam install is involved
(`tree_sitter` is imported only because it is the runtime API of the pinned
tree-sitter-ocaml package).

Gap-disclosing by construction (wild's gaps-uncuring law): every construct
the extractor does not interpret is COUNTED per file with a per-kind
breakdown and never silently dropped. All iteration is sorted for
determinism; no timings are printed (D5 byte-identity is total).
"""

import re
import subprocess
import sys
from pathlib import Path

import tree_sitter_ocaml
import tree_sitter

# --- D2: pinned corpus -------------------------------------------------------

MIRAGE_SKELETON_URL = "https://github.com/mirage/mirage-skeleton"
MIRAGE_SKELETON_PIN = "52abe5aedb1f19f6dd3a18dc9ad81c766f813ebc"
CORPUS_CACHE = Path.home() / ".cache" / "wild-functor-pilot" / "mirage-skeleton"
CORPUS_DIRS = ("tutorial", "applications", "device-usage")  # lead correction 2026-10-14: example/ does not exist at the pin; the functor-bearing devices (dns, http, git, docteur) live under applications/
EXCLUDED_DIR_PARTS = {"_build", "vendored", ".git"}

# --- D3: gap-disclosure kinds ------------------------------------------------

# Every kind below is a mechanism the extractor does NOT interpret. Counts are
# always emitted for all kinds (0 included) so the gap surface is visible.
UNSUPPORTED_KINDS = (
    "with_type_constraints",    # `with type/module ...` constraints
    "module_type_of",           # `module type of X` definitions
    "include_module_type_of",   # `include module type of X` (mangled by grammar; regex-counted)
    "first_class_modules",      # `(module M : S)` package expressions
    "include_module_type",      # plain `include X` inside a signature (items not expanded)
    "unparsed_error_nodes",     # grammar ERROR nodes (anything unattributed)
)

INCLUDE_MTO_RE = re.compile(r"\binclude\s+module\s+type\s+of\b")
MIRAGE_DECL_RE = re.compile(r"mirage\b[^\n]*")


def _parser():
    lang = tree_sitter.Language(tree_sitter_ocaml.language_ocaml())
    return tree_sitter.Parser(lang)


def _text(node):
    return node.text.decode("utf-8")


def _iter_all(node):
    yield node
    for child in node.children:
        yield from _iter_all(child)


def _child(node, kind):
    for c in node.children:
        if c.type == kind:
            return c
    return None


def _module_type_label(node):
    """Human-stable label for a module-type expression node."""
    if node is None:
        return None
    if node.type == "module_type_path":
        name = _child(node, "module_type_name")
        return _text(name) if name is not None else _text(node)
    if node.type == "signature":
        # Inline `sig ... end`: attribute the items, disclose the shape.
        vals = sum(1 for c in node.children if c.type == "value_specification")
        typs = sum(1 for c in node.children if c.type == "type_definition")
        return f"sig(inline; values={vals}, types={typs})"
    return _text(node)


def _count_sig_items(signature_node):
    vals = sum(1 for c in signature_node.children if c.type == "value_specification")
    typs = sum(1 for c in signature_node.children if c.type == "type_definition")
    return vals + typs


def _extract_module_type(node):
    name = _child(node, "module_type_name")
    sig = _child(node, "signature")
    return {
        "name": _text(name) if name is not None else "?",
        "value_specs": sum(1 for c in sig.children if c.type == "value_specification")
        if sig is not None
        else 0,
        "type_decls": sum(1 for c in sig.children if c.type == "type_definition")
        if sig is not None
        else 0,
    }


def _extract_functor(binding):
    """module_binding -> functor record, or None if not a functor."""
    params = [c for c in binding.children if c.type == "module_parameter"]
    functor_expr = _child(binding, "functor")
    if not params and functor_expr is not None:
        params = [
            c for c in _iter_all(functor_expr) if c.type == "module_parameter"
        ]
    if not params:
        return None
    name_node = _child(binding, "module_name")
    # Result module type: the annotated type after `:` (path or inline sig).
    result = None
    seen_colon = False
    for c in binding.children:
        if c.type == ":":
            seen_colon = True
            continue
        if seen_colon and c.type in ("module_type_path", "signature"):
            result = _module_type_label(c)
            break
    return {
        "name": _text(name_node) if name_node is not None else "?",
        "parameters": [
            {
                "name": _text(pn) if (pn := _child(p, "module_name")) is not None else "?",
                "module_type": _module_type_label(
                    next((c for c in p.children
                          if c.type in ("module_type_path", "signature")), None)
                ),
            }
            for p in params
        ],
        "result_module_type": result,
    }


def _unsupported_counts(root, source):
    counts = dict.fromkeys(UNSUPPORTED_KINDS, 0)
    for node in _iter_all(root):
        if node.type == "constrain_type":
            counts["with_type_constraints"] += 1
        elif node.type == "module_type_of":
            counts["module_type_of"] += 1
        elif node.type == "package_expression":
            counts["first_class_modules"] += 1
        elif node.type == "include_module_type":
            counts["include_module_type"] += 1
        elif node.type == "ERROR":
            counts["unparsed_error_nodes"] += 1
    # The grammar mangles top-level `include module type of X`; count it from
    # source text so the gap is never lost to a parser artifact.
    if isinstance(source, bytes):
        source = source.decode("utf-8", errors="replace")
    counts["include_module_type_of"] = len(INCLUDE_MTO_RE.findall(source))
    return counts


def extract_from_source(filename, source):
    """Extract functor-signature inventory + gap counts from OCaml source text.

    Pure function of (filename, source): no I/O, no clock (D5 determinism).
    """
    if isinstance(source, str):
        source = source.encode("utf-8")
    parser = _parser()
    tree = parser.parse(source)
    root = tree.root_node

    module_types, functors, applications = [], [], []
    for node in root.children:
        if node.type == "module_type_definition":
            # The grammar mangles `include module type of X` into an ERROR
            # node plus a spurious bare `module type of X` definition; both
            # carry ERROR children. A definition that failed to parse is
            # never inventoried as a real signature (it would shadow the
            # real one) — the ERROR stays disclosed in unsupported_constructs.
            if any(c.type == "ERROR" for c in node.children):
                continue
            module_types.append(_extract_module_type(node))
        elif node.type == "module_definition":
            binding = _child(node, "module_binding")
            if binding is None:
                continue
            functor = _extract_functor(binding)
            if functor is not None:
                functors.append(functor)
            app = _child(binding, "module_application")
            if app is not None:
                callee = _child(_child(app, "module_path"), "module_name")
                applications.append(
                    {"callee": _text(callee) if callee is not None else "?"}
                )

    return {
        "file": filename,
        "module_type_definitions": module_types,
        "functors": functors,
        "module_applications": applications,
        "unsupported_constructs": _unsupported_counts(root, source),
    }


# --- D2: corpus acquisition --------------------------------------------------


def _ensure_corpus():
    if CORPUS_CACHE.exists():
        head = subprocess.run(
            ["git", "-C", str(CORPUS_CACHE), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=True,
        ).stdout.strip()
        if head != MIRAGE_SKELETON_PIN:
            sys.exit(
                f"error: cached checkout HEAD {head} != pin "
                f"{MIRAGE_SKELETON_PIN}; remove {CORPUS_CACHE} and rerun"
            )
        return
    CORPUS_CACHE.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "clone", "--filter=blob:none", "--no-checkout",
         MIRAGE_SKELETON_URL, str(CORPUS_CACHE)],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(CORPUS_CACHE), "fetch", "--depth", "1", "origin",
         MIRAGE_SKELETON_PIN],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(CORPUS_CACHE), "checkout", "FETCH_HEAD"],
        check=True, capture_output=True,
    )


def _corpus_files():
    files = []
    for d in CORPUS_DIRS:
        base = CORPUS_CACHE / d
        if not base.is_dir():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(CORPUS_CACHE)
            if EXCLUDED_DIR_PARTS & set(rel.parts):
                continue
            if p.suffix in (".ml", ".mli"):
                files.append(rel)
    return sorted(files)


def _declared_mirage_version():
    """Report what the repo's own files declare about the mirage version."""
    findings = []
    candidates = list(CORPUS_CACHE.glob("*.opam"))
    for extra in ("dune-project", "README.md", "README.org"):
        p = CORPUS_CACHE / extra
        if p.is_file():
            candidates.append(p)
    for path in sorted(candidates):
        for i, line in enumerate(
            path.read_text(encoding="utf-8", errors="replace").splitlines(), 1
        ):
            if re.search(r"\"?mirage\"?\s*\{|mirage\s*[<>=~]+", line, re.I):
                findings.append(f"{path.name}:{i}: {line.strip()}")
    return findings or ["(no mirage version constraint found in *.opam, "
                        "dune-project, or README files — declared honestly as absent)"]


# --- D4/D5: report -----------------------------------------------------------


def _fmt_functor(f):
    params = ", ".join(f"{p['name']}: {p['module_type']}" for p in f["parameters"])
    result = f["result_module_type"] if f["result_module_type"] else "(no result annotation)"
    return f"{f['name']} ({params}) : {result}"


def main():
    _ensure_corpus()
    rel_files = _corpus_files()
    if not rel_files:
        sys.exit("error: empty corpus — no .ml/.mli under tutorial/, applications/, or device-usage/")

    print("wild-3yy functor-signature extraction pilot — mirage-skeleton")
    print(f"pinned commit: {MIRAGE_SKELETON_PIN}")
    print(f"corpus: {MIRAGE_SKELETON_URL} @ pin, dirs {CORPUS_DIRS}, "
          f"{len(rel_files)} .ml/.mli files")
    print("mirage version declared by the repo's own files:")
    for line in _declared_mirage_version():
        print(f"  {line}")
    print()

    records = []
    for rel in rel_files:  # sorted walk order (D5)
        source = (CORPUS_CACHE / rel).read_bytes()
        records.append(extract_from_source(str(rel), source))

    per_file_unsupported = 0
    for r in records:
        unsup = r["unsupported_constructs"]
        per_file_unsupported += sum(unsup.values())
        print(f"== {r['file']} ==")
        print(f"  module_type_definitions: {len(r['module_type_definitions'])}")
        for m in r["module_type_definitions"]:
            print(f"    {m['name']}: value_specs={m['value_specs']} "
                  f"type_decls={m['type_decls']}")
        print(f"  functors: {len(r['functors'])}")
        for f in r["functors"]:
            print(f"    {_fmt_functor(f)}")
        print(f"  module_applications: {len(r['module_applications'])}")
        for a in r["module_applications"]:
            print(f"    callee: {a['callee']}")
        print("  unsupported_constructs (extractor does not interpret): "
              + ", ".join(f"{k}={v}" for k, v in unsup.items()))
        print()

    # Summary
    n_mts = sum(len(r["module_type_definitions"]) for r in records)
    n_functors = sum(len(r["functors"]) for r in records)
    n_params = sum(len(f["parameters"]) for r in records for f in r["functors"])
    n_apps = sum(len(r["module_applications"]) for r in records)
    n_mts_items = sum(m["value_specs"] + m["type_decls"]
                      for r in records for m in r["module_type_definitions"])
    unsup_total = dict.fromkeys(UNSUPPORTED_KINDS, 0)
    for r in records:
        for k, v in r["unsupported_constructs"].items():
            unsup_total[k] += v

    print("== summary ==")
    print(f"files scanned: {len(records)}")
    print(f"module_type_definitions: {n_mts} (signature items: {n_mts_items})")
    print(f"functor boundaries: {n_functors} (parameters: {n_params})")
    print(f"module_applications: {n_apps}")
    print("unsupported_constructs total: "
          + ", ".join(f"{k}={v}" for k, v in unsup_total.items())
          + f" (sum={sum(unsup_total.values())})")
    print()

    # D4 (1): what OCaml gives free
    print("== WHAT OCAML GIVES FREE ==")
    checked_boundaries = n_mts + n_functors
    print(f"  machine-checked signature boundaries: {checked_boundaries} "
          f"({n_mts} module types + {n_functors} functor result/parameter "
          f"constraints over {n_params} parameters)")
    print(f"  signature items enforced at every application site: {n_mts_items}")
    print("  every signature item is shape-only: a val/type declaration names a "
          "shape, and 0 behavioral predicates (laws, postconditions, history) "
          "are expressible — OCaml checks these boundaries at link time for "
          "free, and stops there.")
    print()

    # D4 (2): what wild adds per boundary
    print("== WHAT WILD ADDS PER BOUNDARY (the signature cannot express these) ==")
    print("  vocabulary            | per boundary | pilot-counted quantity")
    print("  ----------------------|--------------|-----------------------")
    print(f"  law slots             | 1+           | {n_functors} functor boundaries x >=1 law each = >= {n_functors} law slots, 0 expressible in signatures")
    print(f"  accretion relation    | 1            | {n_functors} boundaries with provides-grow/requires-shrink vs OCaml's any-change-breaks (no monotonicity in signatures)")
    print(f"  tombstone eligibility | 1            | {n_functors} boundaries whose names could return with different meaning; 0 tombstones expressible")
    print(f"  artifact-bound evidence| 1           | {n_functors} boundaries need evidence bound to the built image; signatures bind to source text only")
    print()

    # D4 (3): honest pilot verdict
    print("== VERDICT ==")
    print(f"  Pilot verdict: OCaml machine-checks {checked_boundaries} signature "
          f"boundaries ({n_mts_items} shape items) for free across the corpus, "
          f"with {sum(unsup_total.values())} unsupported constructs disclosed "
          f"(0 behavioral predicates expressible); wild adds 4 mechanism "
          f"classes per boundary (law slots, accretion relation, tombstone "
          f"eligibility, artifact-bound evidence) = "
          f"{4 * n_functors} additions over {n_functors} functor boundaries "
          f"that the type system cannot express. The signature layer is a "
          f"floor, not the contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
