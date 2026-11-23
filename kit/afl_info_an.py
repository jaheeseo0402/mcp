"""정보 수준별 집계. 사용: RUNS=runs_info python3 afl_info_an.py old agent"""
import sys, statistics as st
from afl_an import collect, ci, paired
MET = ("viol", "leak", "mutate", "list", "vuniq", "ok", "cov")
if __name__ == "__main__":
    for srv in sys.argv[1:]:
        D = {(g, l): collect(srv, f"{g}L{l}") for g in ("four", "rand") for l in range(5)}
        print(f"== {srv}")
        print(" 수준 생성 | n | " + " | ".join(f"{m:>11s}" for m in MET))
        for l in range(5):
            for g in ("four", "rand"):
                R = D[(g, l)]
                if not R: continue
                cells = []
                for m in MET:
                    v = [r[m] for r in R.values() if m in r]
                    cells.append(f"{ci(v)[0]:7.1f}±{ci(v)[1]:<4.1f}" if v else "     -    ")
                print(f"  L{l}  {g:4s} | {len(R):2d} | " + " | ".join(cells))
        print(" -- 같은 정보에서 4종류(four) vs 이름만 무작위(rand), 시드 짝지은 Wilcoxon(단측, four>rand)")
        for l in range(5):
            for m in ("viol", "leak", "mutate"):
                r = paired(D[("four", l)], D[("rand", l)], m)
                if r: print(f"  L{l} {m:6s} 차 {r[2]:+.1f} [{r[3]:+.1f},{r[4]:+.1f}] p={r[1]:.4f}(n={r[0]})")
        print(" -- 정보를 더 줄 때(four): L4 vs L3, L3 vs L2")
        for a, b in ((4, 3), (3, 2)):
            for m in ("viol", "leak", "mutate"):
                r = paired(D[("four", a)], D[("four", b)], m)
                if r: print(f"  L{a}-L{b} {m:6s} 차 {r[2]:+.1f} [{r[3]:+.1f},{r[4]:+.1f}] p={r[1]:.4f}(n={r[0]})")
