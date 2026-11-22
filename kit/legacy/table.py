# 서버별 비교표 출력: python3 table.py
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import an6
names={"random":"Random","mcpfuzzer":"mcp-fuzzer","unified":"제안 모델"}
print(f"{'서버':<7}{'조건':<12}{'호출':>7}{'폴더 밖 성공':>14}{'서버 내부 도달%':>16}{'정상 처리%':>12}  시드별 폴더 밖 성공")
for srv in ("old","agent","adro"):
    for c in ("random","mcpfuzzer","unified"):
        r=an6.summ(f"{c}_{srv}")
        if r: print(f"{srv:<7}{names[c]:<12}{r[0]:>7.0f}{r[1]:>14.1f}{r[2]:>15.1f}%{r[3]:>11.1f}%  {r[4]}")
