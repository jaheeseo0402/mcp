"""crash를 뜯어보는 분석: 단계마다 어떤 버그(ASAN 종류 + 함수 + 소스 줄)를 몇 번의 실행에서 찾았나.
사용: (타깃 폴더에서) python3 ../analyze_bugs.py <이름> <ASAN 빌드>   예: python3 ../analyze_bugs.py cjson ./cjsonbin_tri
출력: <이름>_bugs.csv (버그 × 단계별 찾은 실행 수), 대표 입력 파일 경로와 ASAN 보고서 요약줄
"""
import glob, os, re, subprocess, sys, collections
NAME, TRI = sys.argv[1], sys.argv[2]
LEVELS = ["L0", "L1", "L2", "L3"]
bugs = collections.defaultdict(lambda: {"runs": collections.defaultdict(set), "ex": None, "sum": ""})
for L in LEVELS:
    for r in sorted(glob.glob("out_%s_r*" % L)):
        for f in glob.glob(r + "/default/crashes/id*"):
            try:
                p = subprocess.run([TRI, f], capture_output=True, timeout=10, env=dict(os.environ, ASAN_OPTIONS="detect_leaks=0"))
            except subprocess.TimeoutExpired:
                key, summ = "timeout", ""
            else:
                m = re.search(rb"ERROR: AddressSanitizer: (\S+)", p.stderr)
                if not m:
                    key, summ = ("sig%d" % p.returncode, "") if p.returncode != 0 else (None, "")
                else:
                    fr = [x.decode() for x, _ in re.findall(rb"#\d+ 0x[0-9a-f]+ in (\S+) (\S+)", p.stderr)]
                    fr = [x for x in fr if not x.startswith(("__", "operator", "malloc", "calloc", "realloc", "free", "mem", "str"))]
                    key = "ASAN-%s %s" % (m.group(1).decode(), fr[0] if fr else "?")
                    s = re.search(rb"SUMMARY: AddressSanitizer: (.+)", p.stderr)
                    summ = s.group(1).decode() if s else ""
            if key is None: continue
            b = bugs[key]; b["runs"][L].add(r)
            if b["ex"] is None: b["ex"] = f; b["sum"] = summ
with open("%s_bugs.csv" % NAME, "w") as o:
    o.write("bug,%s,example_input,asan_summary\n" % ",".join("runs_" + L for L in LEVELS))
    for k, b in sorted(bugs.items(), key=lambda t: -sum(len(v) for v in t[1]["runs"].values())):
        o.write('"%s",%s,"%s","%s"\n' % (k, ",".join(str(len(b["runs"].get(L, ()))) for L in LEVELS), b["ex"], b["sum"].replace('"', "'")))
        print("%-45s %s   %s" % (k, " ".join("%s:%d" % (L, len(b["runs"].get(L, ()))) for L in LEVELS), b["sum"]))
if not bugs: print("crash 없음")
