import json, os, sys, glob, statistics as st
from scipy import stats
PATHK = ("path", "source", "destination", "repo_path")
def cls(t, err):
    t = t.lower()
    if "outside allowed directories" in t or "outside the allowed" in t or "access denied" in t: return "folder"
    if "validation" in t or "invalid arguments" in t or "-32602" in t or "invalid input" in t: return "format"
    if "enoent" in t or "no such file" in t or "not found" in t or "does not exist" in t: return "nofile"
    if err: return "err"
    return "ok"
def one(d):
    ROOT = os.path.join(os.path.abspath(d), "iso", "sandbox"); n = out = 0; c = {"folder": 0, "format": 0, "nofile": 0, "err": 0, "ok": 0}; pairs = set()
    for line in open(os.path.join(d, "calls.jsonl")):
        r = json.loads(line); n += 1; k = cls(r["txt"], r["err"]); c[k] += 1
        if r["err"] or r["txt"].lower().startswith("error"): continue
        for kk, v in (r["args"] or {}).items():
            if kk in PATHK and isinstance(v, str) and v:
                ab = os.path.normpath(v if v.startswith("/") else os.path.join(ROOT, v))
                if not (ab == ROOT or ab.startswith(ROOT + "/")): out += 1; pairs.add((r["tool"], ab)); break
    s = json.load(open(os.path.join(d, "summary.json")))
    return dict(out=out, pairs=len(pairs), reach=100 * (n - c["folder"] - c["format"]) / n, ok=100 * c["ok"] / n, cov=s["cov_total"], n=n)
def collect(srv, strat):
    return [one(d) for d in sorted(glob.glob(f"{os.environ.get('RUNS','runs')}/{srv}_{strat}_s*")) if os.path.exists(d + "/summary.json")]
def ci(x):
    m = st.mean(x); k = len(x)
    return m, (stats.t.ppf(.975, k - 1) * st.stdev(x) / k ** .5 if k > 1 else 0)
if __name__ == "__main__":
    for srv in sys.argv[1:]:
        D = {s: collect(srv, s) for s in ("random", "mcpfuzzer", "ours")}
        print(f"== {srv} (시드 수: " + ", ".join(f"{s}={len(D[s])}" for s in D) + ")")
        for met in ("out", "pairs", "reach", "ok", "cov"):
            row = []
            for s in D:
                if D[s]: m, h = ci([r[met] for r in D[s]]); row.append(f"{s} {m:.1f}±{h:.1f}")
            line = f" {met:5s}: " + " | ".join(row)
            if D["ours"] and D["mcpfuzzer"] and len(D["ours"]) > 1:
                try: line += f" | p(ours>mcp)={stats.mannwhitneyu([r[met] for r in D['ours']], [r[met] for r in D['mcpfuzzer']], alternative='greater').pvalue:.4f}"
                except Exception: pass
            print(line)
