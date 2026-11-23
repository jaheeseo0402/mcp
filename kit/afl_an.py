"""집계기. 지표 두 종류를 분리해서 보고한다.
  out   = [응답 기반] 오류 없이 응답했고 경로 인자가 허용 폴더 밖 -> '실제 접근'을 증명하지 못함 (예전 지표)
  viol  = [오라클 기반] 실제 파일시스템에서 확인된 위반 호출 수 (leak: 비밀 토큰이 응답에 나옴,
          mutate: 허용 폴더 밖 파일/폴더가 실제로 생기거나 바뀜, list: 밖에만 있는 파일 이름이 목록에 나옴)
통계: 시드 번호가 같은 조건끼리 짝지어 Wilcoxon 부호순위(단측) + 평균 차이의 95% 부트스트랩 구간."""
import json, os, sys, glob, re, statistics as st
import numpy as np
from scipy import stats
from common import is_path_name
def cls(t, err):
    t = t.lower()
    if "outside allowed directories" in t or "outside the allowed" in t or "access denied" in t: return "folder"
    if "validation" in t or "invalid arguments" in t or "-32602" in t or "invalid input" in t: return "format"
    if "enoent" in t or "no such file" in t or "not found" in t or "does not exist" in t: return "nofile"
    if err: return "err"
    return "ok"
def one(d):
    ROOT = os.path.join(os.path.abspath(d), "iso", "sandbox"); n = out = 0; c = {"folder": 0, "format": 0, "nofile": 0, "err": 0, "ok": 0}
    pairs = set(); vcalls = 0; kinds = {"leak": 0, "mutate": 0, "list": 0}; vpairs = set(); first = None; has = False
    for line in open(os.path.join(d, "calls.jsonl")):
        r = json.loads(line); n += 1; k = cls(r["txt"], r["err"]); c[k] += 1
        if "viol" in r:
            has = True
            if r["viol"]:
                vcalls += 1; first = n if first is None else first
                for v in r["viol"]: kinds[v] += 1; vpairs.add((r["tool"], v))
        if r["err"] or r["txt"].lower().startswith("error"): continue
        for kk, v in (r["args"] or {}).items():
            if is_path_name(kk) and isinstance(v, str) and v:
                ab = os.path.normpath(v if v.startswith("/") else os.path.join(ROOT, v))
                if not (ab == ROOT or ab.startswith(ROOT + "/")): out += 1; pairs.add((r["tool"], ab)); break
    s = json.load(open(os.path.join(d, "summary.json")))
    m = dict(out=out, pairs=len(pairs), reach=100 * (n - c["folder"] - c["format"]) / n, ok=100 * c["ok"] / n, cov=s["cov_total"], n=n)
    if has: m.update(viol=vcalls, vuniq=len(vpairs), leak=kinds["leak"], mutate=kinds["mutate"], list=kinds["list"], first=first if first else n + 1)
    return m
def collect(srv, strat):
    R = {}
    for d in sorted(glob.glob(f"{os.environ.get('RUNS','runs')}/{srv}_{strat}_s*")):
        mm = re.search(r"_s(\d+)$", d)
        if mm and os.path.exists(d + "/summary.json"): R[int(mm.group(1))] = one(d)
    return R
def ci(x):
    m = st.mean(x); k = len(x)
    return m, (stats.t.ppf(.975, k - 1) * st.stdev(x) / k ** .5 if k > 1 else 0)
def paired(A, B, met):
    seeds = sorted(set(A) & set(B))
    if len(seeds) < 3 or any(met not in A[s] or met not in B[s] for s in seeds): return None
    x = np.array([A[s][met] for s in seeds], float); y = np.array([B[s][met] for s in seeds], float); d = x - y
    try: p = stats.wilcoxon(x, y, alternative="greater", zero_method="zsplit").pvalue
    except ValueError: p = 1.0
    rng = np.random.default_rng(0); bs = [rng.choice(d, len(d)).mean() for _ in range(5000)]
    return len(seeds), p, d.mean(), np.percentile(bs, 2.5), np.percentile(bs, 97.5)
if __name__ == "__main__":
    for srv in sys.argv[1:]:
        D = {s: collect(srv, s) for s in ("random", "mcpfuzzer", "ours")}
        print(f"== {srv} (시드 수: " + ", ".join(f"{s}={len(D[s])}" for s in D) + ")")
        for met in ("viol", "vuniq", "leak", "mutate", "list", "first", "out", "pairs", "reach", "ok", "cov"):
            row = []
            for s in D:
                v = [r[met] for r in D[s].values() if met in r]
                if v: m, h = ci(v); row.append(f"{s} {m:.1f}±{h:.1f} (중앙 {st.median(v):.1f})")
            if not row: continue
            line = f" {met:6s}: " + " | ".join(row)
            for other in ("mcpfuzzer", "random"):
                r = paired(D["ours"], D[other], met)
                if r: line += f" | ours-{other[:3]} 차 {r[2]:+.1f} [{r[3]:+.1f},{r[4]:+.1f}] p={r[1]:.4f}(n={r[0]})"
            print(line)
