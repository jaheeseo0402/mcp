import json,glob,os,sys,statistics as st
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__))); import afl_an as a
from scipy import stats
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'iso','sandbox'); K=("path","source","destination","repo_path")
def real(d):
    reqs={}; n=out=0; pairs=set()
    for f in glob.glob(d+"/proxy/*.jsonl"):
        for line in open(f,errors="ignore"):
            try: r=json.loads(line); m=json.loads(r["raw"])
            except: continue
            if r.get("dir")=="req" and m.get("method")=="tools/call": reqs[m["id"]]=m["params"]
            elif r.get("dir")=="res" and m.get("id") in reqs:
                p=reqs.pop(m["id"]); n+=1; res=m.get("result") or {}
                t=" ".join(x.get("text","") for x in (res.get("content") or []) if isinstance(x,dict))
                if m.get("error") or res.get("isError") or t.lower().startswith("error"): continue
                for k,v in (p.get("arguments") or {}).items():
                    if k in K and isinstance(v,str) and v:
                        ab=os.path.normpath(v if v.startswith("/") else os.path.join(ROOT,v))
                        if not (ab==ROOT or ab.startswith(ROOT+"/")): out+=1; pairs.add((p["name"],ab)); break
    keys=set()
    for l in open(d+"/cov.txt"):
        try: keys.update(json.loads(l).get("k",[]))
        except: pass
    return dict(out=out,pairs=len(pairs),cov=len(keys),n=n)
for srv in sys.argv[1:]:
    R=[real(d) for d in sorted(glob.glob(f"realtool/{srv}_s*")) if os.path.exists(d+"/cov.txt")]
    P=a.collect(srv,"mcpfuzzer"); O=a.collect(srv,"ours")
    print(f"== {srv}  도구 그대로 n={len(R)}, 포트 n={len(P)}, 제안 n={len(O)}; 도구 호출 수 평균 {st.mean(r['n'] for r in R):.0f}")
    for met in ("out","pairs","cov"):
        row=[]
        for nm,D in (("도구 그대로",R),("포트",P),("제안",O)):
            m,h=a.ci([r[met] for r in D]); row.append(f"{nm} {m:.1f}±{h:.1f}")
        p=stats.mannwhitneyu([r[met] for r in O],[r[met] for r in R],alternative='greater').pvalue
        print(f" {met:5s}: "+" | ".join(row)+f" | p(제안>도구)={p:.4f}")
