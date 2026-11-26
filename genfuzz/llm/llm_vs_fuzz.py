"""2번: 퍼저 결과와 LLM 입력을 같은 단계끼리 나란히 놓고, 코드 경로(커버리지) 기준으로 중복을 제거한 뒤 남은 것만 분석한다.
사용: python3 llm_vs_fuzz.py <태그> <타깃> <분류용 타깃> [퍼징 결과 폴더(기본 ../exif)] [사용할 반복 번호들(기본 "1 2 3")]
중복 판단: 파일 내용이 아니라 '밟은 edge 집합'이 같으면 중복. (내용이 달라도 같은 경로면 같은 것으로 본다)
단계: 1) LLM 입력끼리 중복 제거  2) 퍼저가 이미 가진 것과 같은 경로인 것 제거  3) 남은 것만 새 경로·crash 분석
그림: (a) edge를 퍼저만/겹침/LLM만으로 나눈 막대  (b) 입력 수가 줄어드는 과정  (c) 남은 입력 중 퍼저에 없던 경로를 여는 것
"""
import os, sys, collections
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fzlib import edge_maps, bug_of

HERE = os.path.dirname(os.path.abspath(__file__))
TAG, BIN, TRI = sys.argv[1], sys.argv[2], sys.argv[3]
FUZZ = sys.argv[4] if len(sys.argv) > 4 else os.path.join(HERE, "..", "exif")
RUNS = (sys.argv[5] if len(sys.argv) > 5 else "1 2 3").split()
LV = [L for L in ("L0", "L1", "L2", "L3") if os.path.isdir(os.path.join(HERE, "in", TAG, L))]

rows = []
for L in LV:
    F = {}
    for r in RUNS:
        for sub in ("queue", "crashes"):
            d = os.path.join(FUZZ, f"out_{L}_r{r}", "default", sub)
            if os.path.isdir(d):
                for n, s in edge_maps(BIN, d).items():
                    F[f"r{r}/{sub}/{n}"] = s
    ld = os.path.join(HERE, "in", TAG, L)
    M = edge_maps(BIN, ld)
    Fu = set().union(*F.values()) if F else set()
    Mu = set().union(*M.values()) if M else set()
    # 1) LLM 입력끼리 중복 제거 (경로 집합이 같은 것은 첫 번째만 남김)
    groups = collections.OrderedDict()
    for n in sorted(M):
        groups.setdefault(frozenset(M[n]), n)
    # 2) 퍼저가 이미 가진 경로 집합과 같은 것 제거
    Fsig = {frozenset(s) for s in F.values()}
    remain = [n for sig, n in groups.items() if sig not in Fsig]
    # 3) 남은 것 분석
    new_edge_inputs = [n for n in remain if M[n] - Fu]
    bugs = collections.Counter()
    for n in remain:
        b = bug_of(TRI, os.path.join(ld, n))
        if b:
            bugs[b] += 1
    row = dict(level=L, fuzz_files=len(F), llm_files=len(M), llm_self_unique=len(groups), llm_remaining=len(remain),
               remaining_new_edge=len(new_edge_inputs), remaining_crash=sum(bugs.values()), bugs="|".join(bugs),
               fuzz_only=len(Fu - Mu), overlap=len(Fu & Mu), llm_only=len(Mu - Fu))
    rows.append(row)
    print({k: v for k, v in row.items()})

COL = {"fuzz_only": "#d96a1e", "overlap": "#9aa5b1", "llm_only": "#1f3a6e"}
fig, ax = plt.subplots(1, 3, figsize=(15, 4))
bot = [0] * len(rows)
for k, lab in (("fuzz_only", "fuzzer only"), ("overlap", "both"), ("llm_only", "LLM only")):
    v = [r[k] for r in rows]
    ax[0].bar([r["level"] for r in rows], v, bottom=bot, color=COL[k], label=lab)
    bot = [b + x for b, x in zip(bot, v)]
ax[0].set_title("(a) Edges: fuzzer vs LLM (same level)", fontsize=10); ax[0].set_ylabel("Edges"); ax[0].legend(); ax[0].set_xlabel("Structure info level")
w = 0.26; xs = range(len(rows))
for j, (k, lab, c) in enumerate((("llm_files", "LLM inputs", "#9aa5b1"), ("llm_self_unique", "after self-dedup", "#2e75b6"), ("llm_remaining", "after fuzzer-dedup", "#1f3a6e"))):
    ax[1].bar([x + (j - 1) * w for x in xs], [r[k] for r in rows], w, color=c, label=lab)
ax[1].set_xticks(list(xs)); ax[1].set_xticklabels([r["level"] for r in rows]); ax[1].legend(fontsize=8)
ax[1].set_title("(b) LLM inputs left after coverage dedup", fontsize=10); ax[1].set_xlabel("Structure info level")
ax[2].bar([r["level"] for r in rows], [r["remaining_new_edge"] for r in rows], color="#1f3a6e", label="open edges fuzzer lacks")
ax[2].bar([r["level"] for r in rows], [r["remaining_crash"] for r in rows], color="#d96a1e", width=0.4, label="crashing")
ax[2].set_title("(c) Remaining inputs: new edges / crashes", fontsize=10); ax[2].legend(fontsize=8); ax[2].set_xlabel("Structure info level")
for a in ax:
    a.grid(axis="y", alpha=0.3)
plt.tight_layout(); out = f"cmp_{TAG}"; plt.savefig(out + ".png", dpi=170)
with open(out + "_summary.csv", "w") as f:
    keys = list(rows[0]); f.write(",".join(keys) + "\n")
    for r in rows:
        f.write(",".join(str(r[k]) for k in keys) + "\n")
print("그림:", out + ".png", " 표:", out + "_summary.csv")
