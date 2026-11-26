#!/bin/bash
# 사용: bash run_afl.sh <단계 L0~L3> <초> <반복번호> [타깃]
# 결과: out_<단계>_r<반복>/ (AFL++ 출력. default/plot_data 에 시간별 crash 수가 기록됨)
L=$1; T=${2:-60}; R=${3:-1}; BIN=${4:-./tinyfmt}
cd "$(dirname "$0")"
OUT=out_${L}_r${R}; rm -rf $OUT
export AFL_SKIP_CPUFAIL=1 AFL_I_DONT_CARE_ABOUT_MISSING_CRASHES=1 AFL_NO_AFFINITY=1 AFL_AUTORESUME=0
DICT=""; if [ "$L" = "L2" ] || [ "$L" = "L3" ]; then DICT="-x dict.txt"; fi
afl-fuzz -i seeds/$L -o $OUT -V $T $DICT -s $R -- $BIN @@ > /dev/null 2>&1 &
PID=$!
wait $PID
echo "끝: $L r$R"
