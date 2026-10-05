import sys, os, json, glob, re
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "prototype"))
import wild_proto as P
from packaging.specifiers import SpecifierSet
from packaging.version import Version
D="/tmp/proj/py"; orc=json.load(open(f"{D}/oracle.json"))
PAIRS={"flask":("werkzeug",{"2.2.5":"2.2.3","2.3.3":"2.3.8","3.0.3":"3.0.6","3.1.1":"3.1.3"},["2.2.3","2.3.8","3.0.6","3.1.3"]),
       "requests":("urllib3",{"2.28.2":"1.26.18","2.31.0":"1.26.18","2.32.3":"2.2.3"},["1.26.18","2.0.7","2.2.3","2.5.0"])}
def declared(c,cv,p):
    md=glob.glob(f"{D}/{c}-{cv}/*.dist-info/METADATA")[0]
    for l in open(md):
        m=re.match(rf"Requires-Dist: {p}\s*(.*)",l,re.I)
        if m: return SpecifierSet(re.sub(r"[()\s]","",m.group(1).split(";")[0]) or "")
    return SpecifierSet("")
rows=[]; cache={}
for c,(p,devmap,pvs) in PAIRS.items():
    prov={v:P.extract_py(f"{D}/{p}-{v}",p) for v in pvs}
    for cv,dv in devmap.items():
        calls={}
        d,u=P.demand_py(f"{D}/{c}-{cv}",c,p,prov[dv],calls)
        spec=declared(c,cv,p)
        print(f"{c}-{cv}: dev={p}-{dv} demand={len(d)} unresolved={len(u)} declared='{spec}'")
        for pv in pvs:
            f=P.scoped_failures(prov[dv],prov[pv],d) if pv!=dv else []
            f2=P.scoped_failures_calls(prov[dv],prov[pv],d,calls) if pv!=dv else []
            tool=not f; tool2=not f2
            decl=Version(pv) in spec
            ok=orc[f"{c}-{cv}|{p}-{pv}"]["ok"]
            rows.append((c,cv,pv,tool,decl,ok,f2[:2],tool2))
print()
print(f"{'cell':<34}{'oracle':<8}{'tool-v1':<12}{'tool-v2':<12}{'declared':<12} notes(v2)")
for c,cv,pv,tool,decl,ok,f,tool2 in rows:
    lab=lambda pred: "correct" if pred==ok else ("FALSE-PASS" if pred else "FALSE-BREAK")
    print(f"{c+'-'+cv+' x '+pv:<34}{'pass' if ok else 'FAIL':<8}{lab(tool):<12}{lab(tool2):<12}{lab(decl):<12}{'; '.join(x[0].split('.',1)[1][:30]+': '+x[1][:34] for x in f)}")
def conf(idx):
    tp=sum(1 for r in rows if r[idx] and r[5]); fp=sum(1 for r in rows if r[idx] and not r[5])
    fn=sum(1 for r in rows if not r[idx] and r[5]); tn=sum(1 for r in rows if not r[idx] and not r[5])
    return dict(true_pass=tp,false_pass=fp,false_break=fn,true_break=tn,accuracy=round((tp+tn)/len(rows),2))
print("\ncells",len(rows),"oracle pass",sum(r[5] for r in rows))
print("tool v1 (symbol demand)       ",conf(3)); print("tool v2 (+call-site arguments)",conf(7)); print("declared range                ",conf(4))
