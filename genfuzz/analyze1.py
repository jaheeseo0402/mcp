"""실험 1 집계와 그래프.
사용: python3 analyze1.py [타깃 실행파일] [출력 접두어] [분류용 실행파일]
읽는 것: out_<단계>_r<반복>/default/plot_data, crashes/
그리는 것(x축 = 시간(초), 선 하나 = 구조정보 단계, 음영 = 반복 최소~최대):
  (a) 고유 crash 수      : AFL++이 저장한 crash 수 (커버리지가 다른 것만 저장). crashes/ 파일 이름의 time으로 시각 복원
  (b) 서로 다른 버그 수  : 저장된 crash를 다시 실행해 버그 번호(또는 신호)로 중복을 합친 값
  (c) edge 수            : 큐 파일을 시각 순서로 afl-showmap에 넣어 누적한 코드 경로 수
  (d) 큐 크기
  전체 crash 수(실행 횟수)는 AFL++이 시간별로 남기지 않아 끝 시점 막대 그래프(_final)에만 넣는다.
"""
import glob, os, re, subprocess, sys, collections
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BIN = sys.argv[1] if len(sys.argv) > 1 else "./tinyfmt"
TRI = sys.argv[3] if len(sys.argv) > 3 else BIN   # crash 분류에 쓸 바이너리(exif는 exifbin_tri)
PRE = sys.argv[2] if len(sys.argv) > 2 else "exp1"
LEVELS = ["L0", "L1", "L2", "L3"]
COL = {"L0": "#9aa5b1", "L1": "#2e75b6", "L2": "#d96a1e", "L3": "#1f3a6e"}


def bug_id(path):
    """crash 파일을 타깃에 다시 넣어 버그 번호를 얻는다. 표시가 없으면 종료 신호로 대신한다."""
    try:
        p = subprocess.run([TRI, path], capture_output=True, timeout=5)
    except subprocess.TimeoutExpired:
        return "timeout"
    m = re.search(rb"\[BUG (\d+)\]", p.stderr)
    if m:
        return f"BUG{m.group(1).decode()}"
    m = re.search(rb"\[CRASH ([^\]]+)\]", p.stderr)          # libexif: 신호 + 호출 스택 앞 3칸
    return m.group(1).decode() if m else f"sig{p.returncode}"


def ftime(path):
    """AFL++ 파일 이름의 time:(밀리초)를 초로. 처음 넣은 시드는 0초."""
    m = re.search(r"time:(\d+)", os.path.basename(path))
    return int(m.group(1)) / 1000 if m else 0.0


def edges_of(path):
    """afl-showmap으로 파일 하나가 밟은 코드 경로(edge) 집합을 얻는다."""
    out = "/tmp/_map_%d" % os.getpid()
    subprocess.run(["afl-showmap", "-q", "-o", out, "-t", "2000", "--", BIN, path],
                   capture_output=True, env=dict(os.environ, AFL_SKIP_BIN_CHECK="1"))
    try:
        return {ln.split(":")[0] for ln in open(out) if ":" in ln}
    except OSError:
        return set()


def step(times, vals, grid):
    """(시각, 값) 기록을 격자 시각마다 '그 시각까지의 마지막 값'으로 바꾼다."""
    out, j, cur = [], 0, 0
    for g in grid:
        while j < len(times) and times[j] <= g:
            cur = vals[j]; j += 1
        out.append(cur)
    return out


def total_crashes(run):
    """실행이 끝날 때 AFL++이 센 전체 crash 수(plot_data 마지막 줄의 total_crashes). 시간별 값은 AFL++이 남기지 않는다."""
    last = [ln for ln in open(f"{run}/default/plot_data") if not ln.startswith("#")][-1].split(",")
    return int(last[13])


def duration(run):
    last = [ln for ln in open(f"{run}/default/plot_data") if not ln.startswith("#")][-1].split(",")
    return float(last[0])


runs = collections.defaultdict(list)
for d in sorted(glob.glob("out_L*_r*")):
    m = re.match(r"out_(L\d)_r(\d+)", d)
    if m and os.path.exists(f"{d}/default/plot_data"):
        runs[m.group(1)].append(d)
if not runs:
    sys.exit("out_L*_r* 폴더가 없다. 먼저 run_afl.sh 를 돌려라.")

T = max(duration(d) for L in runs for d in runs[L])
grid = np.arange(0, T + 1, max(1, T / 120))

series = {k: {} for k in ("saved", "bugs", "edges", "corpus")}
finals = {}
summary = []
for L in LEVELS:
    if L not in runs:
        continue
    A = {k: [] for k in series}; tot = []
    for d in runs[L]:
        crashes = sorted((ftime(f), f) for f in glob.glob(f"{d}/default/crashes/id:*"))
        A["saved"].append(step([c[0] for c in crashes], range(1, len(crashes) + 1), grid))
        ev, seen = [], set()
        for tm, f in crashes:
            b = bug_id(f)
            if b not in seen:
                seen.add(b); ev.append((tm, len(seen)))
        A["bugs"].append(step([e[0] for e in ev], [e[1] for e in ev], grid))
        rows = [ln.split(",") for ln in open(f"{d}/default/plot_data") if not ln.startswith("#")]
        if len(rows) >= 5:   # 긴 실행: AFL++이 시간별로 적은 값을 그대로 쓴다(빠름). 열: 0 시간, 3 큐 크기, 12 edge 수
            rt = [float(r[0]) for r in rows]
            A["corpus"].append(step(rt, [int(r[3]) for r in rows], grid))
            A["edges"].append(step(rt, [int(r[12]) for r in rows], grid))
            cov = range(int(rows[-1][12]))
        else:                # 짧은 실행: 큐 파일을 시각 순서로 afl-showmap에 넣어 누적
            queue = sorted((ftime(f), f) for f in glob.glob(f"{d}/default/queue/id:*"))
            A["corpus"].append(step([q[0] for q in queue], range(1, len(queue) + 1), grid))
            cov, eev = set(), []
            for tm, f in queue:
                cov |= edges_of(f); eev.append((tm, len(cov)))
            A["edges"].append(step([e[0] for e in eev], [e[1] for e in eev], grid))
        tot.append(total_crashes(d))
        summary.append((L, d, tot[-1], len(crashes), len(seen), sorted(seen), len(cov)))
    for k in series:
        series[k][L] = np.array(A[k], float)
    finals[L] = np.array(tot, float)

titles = {"saved": "(a) Unique crashes (saved by AFL++)", "bugs": "(b) Distinct bugs (after triage)",
          "edges": "(c) Edges found (coverage)", "corpus": "(d) Corpus size (queue)"}
fig, ax = plt.subplots(1, 4, figsize=(19, 4.2))
for a, k in zip(ax, ("saved", "bugs", "edges", "corpus")):
    for L, M in series[k].items():
        a.plot(grid, M.mean(0), color=COL[L], lw=2, label=f"{L} (n={len(M)})")
        if len(M) > 1:
            a.fill_between(grid, M.min(0), M.max(0), color=COL[L], alpha=0.15)
    a.set_title(titles[k], fontsize=11); a.set_xlabel("Time (s)"); a.grid(alpha=0.3)
ax[0].set_ylabel("Count"); ax[0].legend(title="Structure info")
plt.tight_layout(); plt.savefig(f"{PRE}_time.png", dpi=170)

# 끝 시점 막대 그래프: 전체 crash, 고유 crash, 서로 다른 버그
fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
data = [("Crashes (all)", finals), ("Unique crashes", {L: series["saved"][L][:, -1] for L in series["saved"]}),
        ("Distinct bugs", {L: series["bugs"][L][:, -1] for L in series["bugs"]})]
for a, (tt, D) in zip(ax, data):
    Ls = list(D)
    a.bar(Ls, [D[L].mean() for L in Ls], yerr=[D[L].std() for L in Ls], color=[COL[L] for L in Ls], capsize=4)
    a.set_title(tt); a.set_xlabel("Structure info level"); a.grid(axis="y", alpha=0.3)
ax[0].set_ylabel(f"Count at {int(T)} s (mean ± sd)")
plt.tight_layout(); plt.savefig(f"{PRE}_final.png", dpi=170)

with open(f"{PRE}_summary.csv", "w") as f:
    f.write("level,run,total_crashes,unique_crashes,distinct_bugs,bugs,edges\n")
    for L, d, tc, sc, nb, bs, ed in summary:
        f.write(f"{L},{d},{tc},{sc},{nb},{'|'.join(bs)},{ed}\n")
print(open(f"{PRE}_summary.csv").read())
print("그림:", f"{PRE}_time.png", f"{PRE}_final.png")
