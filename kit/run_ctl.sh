#!/bin/bash
# 경로 이탈 비율 통제 실험. 사용: bash run_ctl.sh "<서버들>" "<시드들>" "<수준들>" "<이탈비율들>"
#  예) bash run_ctl.sh "old agent" "1 2 3 4 5 6 7 8 9 10" "3 4" "0.25 0.5"
#  four와 rand 모두 같은 이탈 비율로 생성. 결과: runs_ctl/ (끝난 것은 건너뜀). N=도구당 호출수(기본 1000), P=동시 실행 수(기본 2)
cd "$(dirname "$0")"; D=runs_ctl; mkdir -p $D
for sd in $2; do for srv in $1; do for g in four rand; do for l in $3; do for e in $4; do
  [ -f $D/${srv}_${g}L${l}_e${e}_s${sd}/summary.json ] || echo "$srv $g $l $sd $e"
done; done; done; done; done | xargs -P ${P:-2} -L 1 bash -c "./venv/bin/python afl_fuzz.py --server \$0 --strategy info --info-gen \$1 --info-level \$2 --seed \$3 --esc-share \$4 --per-tool ${N:-1000} --out $D/\$0_\$1L\$2_e\$4_s\$3 >> $D/log.txt 2>&1; echo \"끝: \$0 \$1 L\$2 e\$4 s\$3\""
echo "전부 끝. 확인: ls $D/*/summary.json | wc -l"
