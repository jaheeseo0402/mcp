# 폴더 밖 성공을 "서로 다른 (도구, 대상 폴더) 조합"으로도 센다: 같은 경로 반복으로 부풀려지는 것을 막기 위함
import json,glob,os,statistics,sys
ROOT="/root/mcpexp_old2/iso/sandbox"
KEYS=("path","source","destination","repo_path")
def an(c,s):
    reqs={}; pairs=set(); tools=set(); tg=set(); n=0
    for f in glob.glob(f"proxy_logs_gen_{c}_s{s}/*.jsonl"):
        for line in open(f,errors="ignore"):
            try: r=json.loads(line); m=json.loads(r["raw"])
            except: continue
            if r.get("dir")=="req" and m.get("method")=="tools/call": reqs[m["id"]]=m["params"]
            elif r.get("dir")=="res" and m.get("id") in reqs:
                p=reqs.pop(m["id"]); res=m.get("result") or {}; n+=1
                t=" ".join(x.get("text","") for x in (res.get("content") or []) if isinstance(x,dict))
                if m.get("error") or res.get("isError") or t.lower().startswith("error"): continue
                for k,v in (p.get("arguments") or {}).items():
                    if k in KEYS and isinstance(v,str) and v:
                        ab=os.path.normpath(v if v.startswith("/") else os.path.join(ROOT,v))
                        if not (ab==ROOT or ab.startswith(ROOT+"/")):
                            pairs.add((p["name"],ab)); tools.add(p["name"]); tg.add(ab); break
    return len(pairs),len(tools),len(tg)
def summ(c,seeds=range(1,7)):
    rs=[an(c,s) for s in seeds]
    return [round(statistics.mean(x[i] for x in rs),1) for i in range(3)]
if __name__=="__main__":
    for c in sys.argv[1:]: print(c,"(도구,대상) 조합 / 도구 수 / 대상 폴더 수 =",summ(c))
