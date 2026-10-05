import subprocess, json, sys, os, itertools
D = "/tmp/proj/py"
PAIRS = {"flask": ("werkzeug", ["2.2.5","2.3.3","3.0.3","3.1.1"], ["2.2.3","2.3.8","3.0.6","3.1.3"], "smoke_flask.py"),
         "requests": ("urllib3", ["2.28.2","2.31.0","2.32.3"], ["1.26.18","2.0.7","2.2.3","2.5.0"], "smoke_requests.py")}
res = {}
for c, (p, cvs, pvs, smoke) in PAIRS.items():
    for cv in cvs:
        for pv in pvs:
            env = dict(os.environ, PYTHONPATH=f"{D}/{c}-{cv}:{D}/{p}-{pv}:{D}/shared", PYTHONWARNINGS="ignore")
            r = subprocess.run([sys.executable, f"{D}/{smoke}"], env=env, capture_output=True, text=True, timeout=90)
            ok = r.returncode == 0 and r.stdout.strip().endswith("OK")
            res[f"{c}-{cv}|{p}-{pv}"] = {"ok": ok, "err": "" if ok else (r.stderr.strip().splitlines() or ["?"])[-1][:160]}
json.dump(res, open(f"{D}/oracle.json", "w"), indent=1)
for k, v in res.items(): print(("PASS " if v["ok"] else "FAIL ") + k + ("" if v["ok"] else "  <- " + v["err"]))
