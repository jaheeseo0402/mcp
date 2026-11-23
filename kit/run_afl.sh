#!/bin/bash
# 사용: bash run_afl.sh <모드> "<서버들>" "<시드들>"
#  모드: generic = 일반 시드(기본 실험) / real = 실제 경로 시드 / 
#  서버: old agent adro      예) bash run_afl.sh generic "old agent adro" "1 2 3 4 5 6 7 8 9 10"
#  결과: runs/ (generic), runs_real/ (real).  이미 끝난 것은 건너뜀 -> 중간에 꺼져도 다시 실행하면 이어서 함
#  환경변수 OUTD=결과 폴더 이름(기본 runs), N=도구당 호출수(기본 1000), P=동시 실행 수(기본 2)
cd "$(dirname "$0")"; MODE=$1; D=${OUTD:-runs}; EXTRA=""
[ "$MODE" = real ] && { D=${OUTD:-runs_real}; EXTRA="--seedmode real"; }
mkdir -p $D
for sd in $3; do for srv in $2; do for st in random mcpfuzzer ours; do
  [ -f $D/${srv}_${st}_s${sd}/summary.json ] || echo "$srv $st $sd"
done; done; done | xargs -P ${P:-2} -L 1 bash -c "./venv/bin/python afl_fuzz.py --server \$0 --strategy \$1 --seed \$2 --per-tool ${N:-1000} $EXTRA --out $D/\$0_\$1_s\$2 >> $D/log.txt 2>&1; echo \"끝: \$0 \$1 \$2\""
echo "전부 끝. 진행 확인: ls $D/*/summary.json | wc -l  (서버수×3×시드수 개가 되면 완료)"
