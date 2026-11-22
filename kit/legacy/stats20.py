import statistics as st, sys
from scipy import stats
import an6
SEEDS=range(1,21)
def per(c):
    rs=[an6.an(c,s) for s in SEEDS]; rs=[r for r in rs if r[0]]
    return dict(n=[r[0] for r in rs],
      out=[r[1] for r in rs],
      reach=[100*(r[0]-r[2]["folder"]-r[2]["format"])/r[0] for r in rs],
      ok=[100*r[2]["ok"]/r[0] for r in rs])
def ci(x):
    m=st.mean(x); k=len(x)
    if k<2: return m,0
    h=stats.t.ppf(0.975,k-1)*st.stdev(x)/k**0.5; return m,h
def mw(a,b):
    try: return stats.mannwhitneyu(a,b,alternative="greater").pvalue
    except Exception: return float("nan")
for srv in sys.argv[1:]:
    D={s:per(f"{s}_{srv}") for s in ("unified","mcpfuzzer","random")}
    print(f"== {srv}  (seeds: "+", ".join(f"{s}={len(D[s]['n'])}" for s in D)+")")
    for met in ("out","reach","ok"):
        row=[]
        for s in D:
            m,h=ci(D[s][met]); row.append(f"{s} {m:.1f}±{h:.1f}")
        p1=mw(D["unified"][met],D["mcpfuzzer"][met]); p2=mw(D["unified"][met],D["random"][met])
        print(f" {met:5s}: "+" | ".join(row)+f" | MW p(ours>mcp)={p1:.4f} p(ours>rand)={p2:.4f}")
