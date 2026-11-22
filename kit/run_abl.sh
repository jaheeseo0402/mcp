#!/bin/bash
# 제안 모델의 구성요소를 하나씩 뺀 비교(ablation). 사용: bash run_abl.sh "old agent" "1 2 3 4 5 6" "full allstr nameonly noconst"
cd "$(dirname "$0")"; mkdir -p runs_abl
for sd in $2; do for srv in $1; do for v in $3; do
  [ -f runs_abl/${srv}_${v}_s${sd}/summary.json ] || echo "$srv $v $sd"
done; done; done | xargs -P ${P:-2} -L 1 bash -c './venv/bin/python afl_fuzz.py --server $0 --strategy ours --variant $1 --seed $2 --out runs_abl/$0_$1_s$2 >> runs_abl/log.txt 2>&1; echo "끝: $0 $1 $2"'
