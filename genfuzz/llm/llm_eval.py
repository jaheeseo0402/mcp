"""3번 평가: LLM이 만든 입력(in/<태그>/<단계>/)을 타깃에 실행해 지표와 그래프를 만든다.
사용: python3 llm_eval.py <태그> <타깃> <분류용 타깃> [퍼징 결과 폴더(기본 ../exif)]
그리는 것 (1번과 같은 지표, x축 = 입력 개수):
  (a) 누적 edge   : x=LLM 입력 개수, y=누적 코드 경로. 점선 = 같은 단계 퍼저(10분) 평균 edge  <- 같은 축에서 비교
  (b) crash 입력 수, (c) 서로 다른 버그 수(맨 위 함수 기준)
"""
import glob, os, re, sys, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fzlib import edge_maps, bug_of

HERE = os.path.dirname(os.path.abspath(__file__))
TAG, BIN, TRI = sys.argv[1], sys.argv[2], sys.argv[3]
FUZZ = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "..", "exif")
COL = {"L0": "#9aa5b1", "L1": "#2e75b6", "L2": "#d96a1e", "L3": "#1f3a6e"}


def fuzzer_edges(L):
    """같은 단계 퍼저 실행들의 마지막 edge 수(plot_data 12열) 평균. 없으면 None."""
    v = []
    for d in glob.glob(os.path.join(FUZZ, f"out_{L}_r*")):
        try:
            rows = [ln.split(",") for ln in open(f"{d}/default/plot_data") if not ln.startswith("#")]
            v.append(int(rows[-1][12]))
        except (OSError, IndexError):
            pass
    return float(np.mean(v)) if v else None


res = {}
for L in ("L0", "L1", "L2", "L3"):
    d = os.path.join(HERE, "in", TAG, L)
    if not os.path.isdir(d):
        continue
    maps = edge_maps(BIN, d)
    names = sorted(os.listdir(d))
    cum, seen = [], set()
    for n in names:
        seen |= maps.get(n, set()); cum.append(len(seen))
    bugs = collections.Counter()
    ncrash = 0
    for n in names:
        b = bug_of(TRI, os.path.join(d, n))
        if b:
            ncrash += 1; bugs[b] += 1
    res[L] = dict(n=len(names), cum=cum, edges=len(seen), crash=ncrash, bugs=bugs, fz=fuzzer_edges(L))
    print(f"{L}: 입력 {len(names)}개, 누적 edge {len(seen)}, crash 입력 {ncrash}개, 버그 {dict(bugs)}, 퍼저 평균 edge {res[L]['fz']}")

fig, ax = plt.subplots(1, 3, figsize=(15, 4))
for L, r in res.items():
    ax[0].plot(range(1, r["n"] + 1), r["cum"], color=COL[L], lw=2.2, ls="--" if L == "L0" else "-", label=f"{L} (n={r['n']})")
    if r["fz"]:
        ax[0].axhline(r["fz"], color=COL[L], lw=0.9, ls=":")
ax[0].set_title("(a) Cumulative edges of LLM inputs\n(dotted = fuzzer, 10 min, same level)", fontsize=10)
ax[0].set_xlabel("Number of LLM-generated inputs"); ax[0].set_ylabel("Edges"); ax[0].grid(alpha=0.3); ax[0].legend()
Ls = list(res)
for a, key, tt in ((ax[1], "crash", "(b) Crashing inputs"), (ax[2], "bugs", "(c) Distinct bugs (top frame)")):
    vals = [r[key] if key == "crash" else len(r[key]) for r in res.values()]
    a.bar(Ls, vals, color=[COL[L] for L in Ls], alpha=0.8)
    for i, v in enumerate(vals):
        a.text(i, v, str(v), ha="center", va="bottom", fontsize=9)
    a.set_title(tt, fontsize=10); a.set_xlabel("Structure info level"); a.grid(axis="y", alpha=0.3)
plt.tight_layout(); out = f"llm_{TAG}"; plt.savefig(out + ".png", dpi=170)
with open(out + "_summary.csv", "w") as f:
    f.write("level,inputs,edges,crash_inputs,distinct_bugs,bugs,fuzzer_mean_edges\n")
    for L, r in res.items():
        f.write(f"{L},{r['n']},{r['edges']},{r['crash']},{len(r['bugs'])},{'|'.join(r['bugs'])},{r['fz']}\n")
print("그림:", out + ".png", " 표:", out + "_summary.csv")
