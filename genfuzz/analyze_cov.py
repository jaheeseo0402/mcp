"""단계별로 어떤 함수·줄이 처음 열리는지 뜯어보는 분석 (실험 1의 심화).
사용: (타깃 폴더에서) python3 ../analyze_cov.py <이름> <커버리지빌드> <소스폴더이름>
  예: python3 ../analyze_cov.py cjson ./cjsoncov cJSON
준비: build.sh 가 만든 <이름>cov (gcc --coverage -O0 로 빌드한 같은 코드)
읽는 것: out_<단계>_r*/default/queue/ 와 crashes/ 의 모든 입력
하는 일: 단계마다 모든 반복의 입력을 coverage 빌드에 넣어 실행한 줄·함수를 모으고,
         "이 단계에서 처음 열린 함수"와 "단계가 올라가며 늘어난 줄 수"를 표와 그림으로 낸다.
"""
import glob, gzip, json, os, shutil, subprocess, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

NAME, COV, SRC = sys.argv[1], sys.argv[2], sys.argv[3]
LEVELS = ["L0", "L1", "L2", "L3"]
WORK = "/tmp/cov_%s" % NAME


def run_level(L):
    pre = os.path.join(WORK, L)
    shutil.rmtree(pre, ignore_errors=True); os.makedirs(pre)
    env = dict(os.environ, GCOV_PREFIX=pre, GCOV_PREFIX_STRIP="100")
    files = []
    for r in sorted(glob.glob("out_%s_r*" % L)):
        files += glob.glob(r + "/default/queue/id*") + glob.glob(r + "/default/crashes/id*")
    for f in files:
        try:
            subprocess.run([COV, f], env=env, capture_output=True, timeout=5)
        except subprocess.TimeoutExpired:
            pass
    return pre, len(files)


def collect(pre):
    """gcda -> (함수 집합, 줄 집합). 소스 폴더 안의 파일만 센다(하네스 제외)."""
    for g in glob.glob(os.path.join(os.path.dirname(os.path.abspath(COV)), "*.gcno")):
        shutil.copy(g, pre)
    funcs, lines = set(), set()
    for gcda in glob.glob(os.path.join(pre, "*.gcda")):
        p = subprocess.run(["gcov", "-j", "-t", "-m", os.path.basename(gcda)], cwd=pre, capture_output=True)
        try:
            j = json.loads(p.stdout)
        except Exception:
            continue
        for fl in j.get("files", []):
            if SRC not in fl["file"]:
                continue
            fn = os.path.basename(fl["file"])
            for fu in fl.get("functions", []):
                if fu["execution_count"] > 0:
                    funcs.add((fn, fu["demangled_name"] if "demangled_name" in fu else fu["name"]))
            for ln in fl.get("lines", []):
                if ln["count"] > 0:
                    lines.add((fn, ln["line_number"]))
    return funcs, lines


res, tot = {}, {}
for L in LEVELS:
    if not glob.glob("out_%s_r*" % L):
        continue
    pre, n = run_level(L)
    res[L] = collect(pre); tot[L] = n
    print("%s: 입력 %d개, 함수 %d, 줄 %d" % (L, n, len(res[L][0]), len(res[L][1])))

first, rows = {}, []
seen_f, seen_l = set(), set()
for L in LEVELS:
    if L not in res: continue
    f, l = res[L]
    newf, newl = f - seen_f, l - seen_l
    for x in newf: first[x] = L
    rows.append((L, tot[L], len(f), len(newf), len(l), len(newl)))
    seen_f |= f; seen_l |= l
with open("%s_cov_summary.csv" % NAME, "w") as o:
    o.write("level,inputs,functions,new_functions_vs_lower,lines,new_lines_vs_lower\n")
    for r in rows: o.write(",".join(map(str, r)) + "\n")
with open("%s_cov_functions.csv" % NAME, "w") as o:
    o.write("first_level,file,function,levels_reaching\n")
    for x, L in sorted(first.items(), key=lambda t: (t[1], t[0])):
        reach = "+".join(k for k in LEVELS if k in res and x in res[k][0])
        o.write("%s,%s,%s,%s\n" % (L, x[0], x[1], reach))
print("\n단계별 새로 열린 함수(처음 도달한 단계 기준):")
for L in LEVELS:
    fs = sorted(x[1] for x, k in first.items() if k == L)
    print(" %s (%d개): %s" % (L, len(fs), ", ".join(fs[:25]) + (" ..." if len(fs) > 25 else "")))

fig, ax = plt.subplots(1, 2, figsize=(11, 3.8))
Ls = [r[0] for r in rows]
cols = ["#9aa5b1", "#2e75b6", "#d96a1e", "#1f3a6e"]
for i, (title, a, b) in enumerate([("Lines executed (queue+crashes, all runs)", 4, 5), ("Functions executed", 2, 3)]):
    tot_v = [r[a] for r in rows]; new_v = [r[b] for r in rows]
    ax[i].bar(Ls, tot_v, color=[cols[LEVELS.index(L)] for L in Ls])
    for x, v, n in zip(Ls, tot_v, new_v):
        ax[i].text(x, v, "%d\n(+%d new)" % (v, n), ha="center", va="bottom", fontsize=8)
    ax[i].set_title(title, fontsize=10); ax[i].set_xlabel("Structure info level"); ax[i].set_ylim(0, max(tot_v) * 1.25)
plt.tight_layout(); plt.savefig("%s_cov.png" % NAME, dpi=160)
print("저장:", "%s_cov_summary.csv %s_cov_functions.csv %s_cov.png" % (NAME, NAME, NAME))
