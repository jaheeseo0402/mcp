import json, glob, os, statistics
import os; ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),"iso","sandbox")
CONDS=os.environ.get("CONDS","random,mcpfuzzer,mcpfuzzer_reseed,afl,aflg,structure,unified,unified_no_escape,unified_no_boundary,unified_no_valid,unified_no_near_miss").split(",")
PATHK=("path","source","destination")
def text(res): return " ".join(x.get("text","") for x in (res.get("content") or []) if isinstance(x,dict))
def analyze(c,s):
    reqs={}; out=0; secret=0; n=0
    for f in glob.glob(f"proxy_logs_gen_{c}_s{s}/*.jsonl"):
        for line in open(f,errors="ignore"):
            try: r=json.loads(line); m=json.loads(r["raw"])
            except Exception: continue
            if r.get("dir")=="req" and m.get("method")=="tools/call": reqs[m["id"]]=m["params"]
            elif r.get("dir")=="res" and m.get("id") in reqs:
                p=reqs.pop(m["id"]); n+=1
                res=m.get("result") or {}
                if m.get("error") or res.get("isError"): continue
                t=text(res)
                if t.lower().startswith("error"): continue
                hit=False
                for k,v in (p.get("arguments") or {}).items():
                    if k in PATHK and isinstance(v,str) and v:
                        ab=os.path.normpath(v if v.startswith("/") else os.path.join(ROOT,v))
                        if not (ab==ROOT or ab.startswith(ROOT+"/")): hit=True
                if hit:
                    out+=1
                    if "TOP_SECRET_OUTSIDE" in t: secret+=1
    return n,out,secret
print(f"{'조건':<22}{'호출':>7}{'밖으로 성공(평균)':>18}{'비밀 읽음(평균)':>16}   시드별(밖으로 성공)")
for c in CONDS:
    rs=[analyze(c,s) for s in (1,2,3)]; rs=[r for r in rs if r[0]]
    if not rs: print(c,"(없음)"); continue
    print(f"{c:<22}{statistics.mean(r[0] for r in rs):>7.0f}{statistics.mean(r[1] for r in rs):>18.1f}{statistics.mean(r[2] for r in rs):>16.1f}   {[r[1] for r in rs]}")
