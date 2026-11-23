#!/bin/bash
# 정보 수준별 비교 (2단계). 사용: bash run_info.sh "<서버들>" "<시드들>" ["<수준들>"] ["<생성방식들>"]
#  예) bash run_info.sh "old agent" "1 2 3 4 5 6 7 8 9 10"            (수준 0~4, four·rand 모두)
#  수준: 0 정보 없음 / 1 허용 폴더 경로만 / 2 +폴더 내부 구조 / 3 +이웃 폴더 이름 / 4 +이웃 폴더 안 파일 이름
#  생성: four = 4종류(각 25%) / rand = 같은 정보로 이름만 무작위 조합(대조).  결과: runs_info/  (끝난 것은 건너뜀)
#  환경변수 RENAME=1 이면 폴더·파일 이름을 시드마다 무작위로 바꾸고 runs_info_rn/ 에 저장(3단계), N=도구당 호출수(기본 1000), P=동시 실행 수(기본 2)
cd "$(dirname "$0")"; LV=${3:-"0 1 2 3 4"}; GN=${4:-"four rand"}; D=runs_info; EXTRA=""; [ -n "$RENAME" ] && { D=runs_info_rn; EXTRA="--rename"; }
mkdir -p $D
for sd in $2; do for srv in $1; do for g in $GN; do for l in $LV; do
  [ -f $D/${srv}_${g}L${l}_s${sd}/summary.json ] || echo "$srv $g $l $sd"
done; done; done; done | xargs -P ${P:-2} -L 1 bash -c "./venv/bin/python afl_fuzz.py --server \$0 --strategy info --info-gen \$1 --info-level \$2 --seed \$3 --per-tool ${N:-1000} $EXTRA --out $D/\$0_\$1L\$2_s\$3 >> $D/log.txt 2>&1; echo \"끝: \$0 \$1 L\$2 \$3\""
echo "전부 끝. 확인: ls $D/*/summary.json | wc -l"
