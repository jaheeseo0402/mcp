#!/bin/bash
# 격리 실행: 서버 폴더의 이웃이 항상 같도록 iso/ 안에서만 실행 (이웃 목록이 실행마다 달라지는 문제 방지)
KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
RUNS=${1:-1000}; SEEDS=${2:-1}
ISO=$KIT/iso; ROOT=$ISO/sandbox
for seed in $SEEDS; do
 for s in ${STRATS:-unified}; do
  rm -rf $ISO; mkdir -p $ISO; cp -a base_orig $ROOT
  mkdir -p $ISO/sandbox_secret $ISO/other_a $ISO/other_b; echo TOP_SECRET_OUTSIDE > $ISO/sandbox_secret/secret.txt
  L=${s}${TAG:-}_s${seed}
  rm -rf proxy_logs_gen_$L gen_$L.jsonl out_$L
  BB=${BB:-0} DISC_CMD="node mcp_proxy_logger_nf.js $ROOT /tmp/disc_$L" STRATEGY=$s ROOT=$ROOT GEN_LOG=gen_$L.jsonl SEED=$seed ABL=${ABL:-} UW=${UW:-1,1,1,1} EDROP=${EDROP:-} timeout 1500 ./venv/bin/python ${WRAP:-mcp_wrap3.py} --mode tools --phase aggressive --protocol-phase realistic --protocol stdio --endpoint "node mcp_proxy_logger_nf.js $ROOT $KIT/proxy_logs_gen_$L" --runs $RUNS --runs-per-type $RUNS --timeout 30.0 --fs-root $KIT/fuzzer_fsroot --seed $seed --output-dir $KIT/out_$L --log-level WARNING --no-safety > /dev/null 2>&1
  echo "$L done"
 done
done
