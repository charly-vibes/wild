#!/usr/bin/env python3
"""Extract a CLI contract from a binary by crawling `--help` (clap format), and a JSON-output
contract by running chosen commands on a fixture. Used on specodelic releases."""
import json, os, re, subprocess, sys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "prototype"))
from wild_sim import Slot, Contract, shape_check
import wild_proto  # installs the callable-signature subtyping used for command argument lists

def run(binary, args, cwd=None, timeout=60):
    r = subprocess.run([binary, *args], capture_output=True, text=True, cwd=cwd, timeout=timeout,
                       env=dict(os.environ, NO_COLOR="1", TERM="dumb"))
    return r.returncode, r.stdout, r.stderr

def parse_help(text):
    """-> dict(commands=[names], options=[(long, short, value, possible, default, required?)], args=[(name, required)])"""
    sec, cmds, opts, args, usage = None, [], [], [], ""
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("Usage:"): usage = l[6:].strip()
        m = re.match(r"^(Commands|Options|Arguments):", l)
        if m: sec = m.group(1); continue
        if l and not l.startswith(" "): sec = None; continue
        if sec == "Commands":
            m = re.match(r"^  ([\w-]+)\s{2,}", l) or re.match(r"^  ([\w-]+)\s*$", l)
            if m and m.group(1) != "help": cmds.append(m.group(1))
        elif sec == "Options":
            m = re.match(r"^\s{2,6}(?:(-\w), )?(--[\w-]+)(?:[ =]([<\[][\w.|-]+[>\]]))?", l)
            if m:
                block = l + " " + " ".join(x.strip() for x in lines[i + 1:i + 6] if x.startswith("          "))
                pv = re.search(r"\[possible values: ([^\]]+)\]", block)
                df = re.search(r"\[default: ([^\]]+)\]", block)
                opts.append((m.group(2), m.group(1), m.group(3), tuple(x.strip() for x in pv.group(1).split(",")) if pv else (),
                             df.group(1) if df else None))
        elif sec == "Arguments":
            m = re.match(r"^\s{2}([<\[][\w.-]+[>\]](?:\.\.\.)?)", l)
            if m: args.append(m.group(1))
    req = {a: a.startswith("<") for a in args}
    return dict(commands=cmds, options=opts, args=[(a, req[a]) for a in args], usage=usage)

def crawl(binary, path=()):
    rc, out, err = run(binary, [*path, "--help"])
    h = parse_help(out or err)
    node = dict(path=path, **h, children={})
    for c in h["commands"]: node["children"][c] = crawl(binary, (*path, c))
    return node

def cli_contract(binary):
    root = crawl(binary); slots = {}
    def walk(n):
        p = " ".join(n["path"]) or "<root>"
        slots[f"cmd:{p}"] = Slot("out", "command")
        for long, short, val, pv, df in n["options"]:
            if long in ("--help",): continue
            k = f"flag:{p}:{long}"
            slots[k] = Slot("out", "flag:" + ("value" if val else "bool"))
            if pv: slots[k + "#values"] = Slot("in", "str", frozenset(pv), True, "optional")
            if df is not None: slots[k + "#default"] = Slot("out", "default", default=df)
            if short: slots[f"flag:{p}:{short}"] = Slot("out", "flag:alias")
        pos = [(a.strip("<>[]."), not req) for a, req in n["args"]]      # (name, has_default)
        slots[f"args:{p}"] = Slot("out", "pyfn:" + json.dumps({"pos": pos, "posonly": len(pos), "kwonly": [],
                                  "vararg": any(a.endswith("...") for a, _ in n["args"]), "kwarg": False}, sort_keys=True))
        for c in n["children"].values(): walk(c)
    walk(root)
    return Contract(slots), root

def jshape(v, path, out, cap=40):
    """Key paths with JSON types. Lists are summarised by their first element; value-keyed maps are collapsed."""
    t = {dict: "obj", list: "list", str: "str", bool: "bool", int: "int", float: "num", type(None): "null"}[type(v)]
    out[path] = Slot("out", "json:" + t)
    if isinstance(v, dict):
        keys = list(v)[:cap]
        for k in keys: jshape(v[k], f"{path}.{k}", out)
    elif isinstance(v, list) and v: jshape(v[0], f"{path}[]", out)

def json_contract(binary, cmds, cwd):
    slots, raw = {}, {}
    for name, args in cmds.items():
        rc, out, err = run(binary, args, cwd=cwd)
        try: data = json.loads(out)
        except Exception: slots[f"json:{name}"] = Slot("out", "json:unparsed"); raw[name] = (rc, out[:200], err[:200]); continue
        raw[name] = (rc, data)
        tmp = {}; jshape(data, f"json:{name}", tmp)
        slots.update(tmp)
    return Contract(slots), raw
