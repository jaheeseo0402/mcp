"""경로 이탈 비율 통제 실험 집계. 사용: RUNS=runs_ctl python3 afl_ctl_an.py "old agent" "3 4" "0.25 0.5" """
import sys
from afl_an import collect, ci, paired
MET = ("viol", "leak", "mutate", "vuniq", "ok", "cov")
srvs, lvs, ess = (a.split() for a in sys.argv[1:4])
for srv in srvs:
    print(f"== {srv}")
    for l in lvs:
        for e in ess:
            D = {g: collect(srv, f"{g}L{l}_e{e}") for g in ("four", "rand")}
            print(f" L{l} 이탈비율 {e}")
            for g in ("four", "rand"):
                R = D[g]
                if not R: continue
                cells = []
                for m in MET:
                    v = [r[m] for r in R.values() if m in r]
                    cells.append(f"{m} {ci(v)[0]:.1f}±{ci(v)[1]:.1f}" if v else f"{m} -")
                print(f"   {g:4s} n={len(R):2d} | " + " | ".join(cells))
            for m in ("viol", "leak", "mutate"):
                r = paired(D["four"], D["rand"], m)
                if r: print(f"   four-rand {m:6s} 차 {r[2]:+.1f} [{r[3]:+.1f},{r[4]:+.1f}] p={r[1]:.4f}(n={r[0]})")
