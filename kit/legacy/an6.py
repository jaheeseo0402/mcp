import json,glob,os,sys,statistics,re
ROOT="/root/mcpexp_old2/iso/sandbox"; PATHK=("path","source","destination","repo_path")
def text(res): return " ".join(x.get("text","") for x in (res.get("content") or []) if isinstance(x,dict))
def cls(t,err):
    t=t.lower()
    if "outside allowed directories" in t or "outside the allowed" in t or "access denied" in t: return "folder"
    if "validation" in t or "invalid arguments" in t or "-32602" in t or "invalid input" in t: return "format"
    if "enoent" in t or "no such file" in t or "not found" in t or "does not exist" in t: return "nofile"
    if err: return "err"
    return "ok"
def an(c,s):
    reqs={}; n=0; out=0; cnt={"folder":0,"format":0,"nofile":0,"err":0,"ok":0}
    for f in glob.glob(f"proxy_logs_gen_{c}_s{s}/*.jsonl"):
        for line in open(f,errors="ignore"):
            try: r=json.loads(line); m=json.loads(r["raw"])
            except Exception: continue
            if r.get("dir")=="req" and m.get("method")=="tools/call": reqs[m["id"]]=m["params"]
            elif r.get("dir")=="res" and m.get("id") in reqs:
                p=reqs.pop(m["id"]); n+=1; res=m.get("result") or {}
                t=json.dumps(m["error"]) if m.get("error") else text(res)
                err=bool(m.get("error")) or bool(res.get("isError"))
                k=cls(t,err); cnt[k]+=1
                if err or t.lower().startswith("error"): continue
                for kk,v in (p.get("arguments") or {}).items():
                    if kk in PATHK and isinstance(v,str) and v:
                        ab=os.path.normpath(v if v.startswith("/") else os.path.join(ROOT,v))
                        if not (ab==ROOT or ab.startswith(ROOT+"/")): out+=1; break
    return n,out,cnt
def summ(c,seeds=range(1,7)):
    rs=[an(c,s) for s in seeds]; rs=[r for r in rs if r[0]]
    if not rs: return None
    n=statistics.mean(r[0] for r in rs)
    out=statistics.mean(r[1] for r in rs)
    reach=statistics.mean(100*(r[0]-r[2]["folder"]-r[2]["format"])/r[0] for r in rs)
    ok=statistics.mean(100*r[2]["ok"]/r[0] for r in rs)
    return n,out,reach,ok,[r[1] for r in rs]
if __name__=="__main__":
    for c in sys.argv[1:]:
        r=summ(c)
        print(c, "없음" if not r else f"calls={r[0]:.0f} outside={r[1]:.1f} reach={r[2]:.1f}% ok={r[3]:.1f}% seeds={r[4]}")
