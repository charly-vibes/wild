import sys
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "prototype"))
import wild_proto as P
from wild_sim import shape_check
VS=["0.2.0","0.3.0","0.4.0","0.5.0","0.6.0","0.7.0","0.8.0","0.8.1","0.8.2","0.8.3","0.9.0","0.10.0","0.10.1","0.11.0","0.11.1","0.12.0"]
C={v:P.extract_rust(f"/tmp/proj/gv/{v}") for v in VS}
TAGS=[("v0.1.0","0.7.0","^0.7"),("v0.2.0","0.8.1","^0.8"),("v0.3.0","0.10.0","^0.10"),("v0.4.0","0.11.1","^0.11"),("v0.5.0","0.11.1","^0.11")]
def cargo_ok(req,v):
    m=req[1:]; return ".".join(v.split(".")[:2])==m
print("specodelic release | demand | genesis versions the CONTRACT allows | genesis versions CARGO allows")
for tag,lock,req in TAGS:
    dev=C[lock]
    d,u=P.demand_rust([f"/tmp/proj/spk-{tag}/src"],"genesis",dev)
    ok=[];bad={}
    for v in VS:
        if v==lock: ok.append(v); continue
        # versions older than dev need provides present; newer need accretion on demand
        f=P.scoped_failures(dev,C[v],d)
        (ok.append(v) if not f else bad.__setitem__(v,f[0]))
    cg=[v for v in VS if cargo_ok(req,v)]
    newer=[v for v in ok if tuple(map(int,v.split(".")))>tuple(map(int,lock.split(".")))]
    print(f"{tag:<7} dev={lock:<7} demand={len(d):<3} unresolved={len(u):<2} contract_ok={ok}")
    print(f"        cargo_ok={cg}  only-contract(newer)={[v for v in newer if v not in cg]}")
    print(f"        blockers: " + "; ".join(f"{v}:{n[0].split('::')[-1] if '::' in n[0] else n[0]} ({n[1][:40]})" for v,(n) in list(bad.items())[:4]))
