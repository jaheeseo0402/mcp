#!/bin/bash
cd /root/mcpexp_old2
RUNS=${1:-500}; SEEDS=${2:-1}
ROOT=/root/mcpexp_old2/sandbox
for seed in $SEEDS; do
 for s in ${STRATS:-random semantic structure}; do
  rm -rf $ROOT ${ROOT}_secret && cp -a base_orig $ROOT && mkdir -p ${ROOT}_secret && echo TOP_SECRET_OUTSIDE > ${ROOT}_secret/secret.txt
  L=${s}${TAG:-}_s${seed}
  rm -rf proxy_logs_gen_$L gen_$L.jsonl out_$L
  START=$(date +%s)
  STRATEGY=$s ROOT=$ROOT GEN_LOG=gen_$L.jsonl SEED=$seed ABL=${ABL:-} UW=${UW:-1,1,1,1} EDROP=${EDROP:-} timeout 1500 ./venv/bin/python ${WRAP:-mcp_wrap2.py} --mode tools --phase aggressive --protocol-phase realistic --protocol stdio --endpoint "node mcp_proxy_logger_nf.js $ROOT /root/mcpexp_old2/proxy_logs_gen_$L" --runs $RUNS --runs-per-type $RUNS --timeout 30.0 --fs-root /root/mcpexp_old2/fuzzer_fsroot --seed $seed --output-dir /root/mcpexp_old2/out_$L --log-level WARNING --no-safety > /dev/null 2>&1
  echo "$L done in $(( $(date +%s) - START ))s"
 done
done
