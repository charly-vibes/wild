import sys, json, itertools
sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), "..", "prototype"))
import wild_proto as P
from wild_sim import shape_check
VS=["0.2.0","0.3.0","0.4.0","0.5.0","0.6.0","0.7.0","0.8.0","0.8.1","0.8.2","0.8.3","0.9.0","0.10.0","0.10.1","0.11.0","0.11.1","0.12.0"]
C={v:P.extract_rust(f"/tmp/proj/gv/{v}") for v in VS}
def cargo_ok(a,b):          # Cargo caret rule for 0.x: same 0.minor, b>=a
    pa,pb=[int(x) for x in a.split(".")],[int(x) for x in b.split(".")]
    return pa[:2]==pb[:2] and pb>=pa
print("== consecutive genesis-vibes releases: full accretion vs Cargo caret")
for a,b in zip(VS,VS[1:]):
    ok,why=shape_check(C[a],C[b])
    sa,sb=set(C[a].slots),set(C[b].slots)
    changed=[k for k in sa&sb if C[a].slots[k]!=C[b].slots[k]]
    removed=[k for k in sa-sb]
    print(f"{a:>7}->{b:<7} cargo_compatible={cargo_ok(a,b)!s:<5} accretion={ok!s:<5} +{len(sb-sa):<4} -{len(removed):<3} changed={len(changed):<3} first_break={why[:70] if not ok else ''}")
# pairwise: how often does Cargo say 'incompatible' while the contract says accretion?
tot=fa=fr=0
for i,a in enumerate(VS):
    for b in VS[i+1:]:
        acc=shape_check(C[a],C[b])[0]; cg=cargo_ok(a,b); tot+=1
        fa+= (acc and not cg); fr+= (cg and not acc)
print(f"pairs={tot} cargo_says_incompatible_but_accretion={fa} cargo_says_compatible_but_break={fr}")
