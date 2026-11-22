#!/bin/bash
# 사용: ./run_srv.sh <서버이름: agent|adro> [시드목록] [호출수]
# 서버 폴더 이웃(sandbox_secret, other_a, other_b)을 고정한 iso/ 에서만 실행 → 재현 가능
KIT="$(cd "$(dirname "$0")/.."; pwd)"; cd $KIT
SRV=$1; SEEDS=${2:-"1 2 3 4 5 6"}; N=${3:-1000}
case $SRV in
 agent) export SERVER_ENTRY=$KIT/srv/node_modules/@agent-infra/mcp-server-filesystem/dist/index.cjs SERVER_PRE=--allowed-directories ;;
 gitold) export SERVER_BIN=$KIT/srv/gv_old/bin/mcp-server-git SERVER_PRE=--repository ;;
 gitnew) export SERVER_BIN=$KIT/srv/gv/bin/mcp-server-git SERVER_PRE=--repository ;;
 old) export SERVER_ENTRY=$KIT/node_modules/mcp-server-filesystem/dist/index.js SERVER_PRE= ;;
 adro)  export SERVER_ENTRY=$KIT/srv/node_modules/@adpharm/mcp-server-filesystem-ro/dist/index.js SERVER_PRE= ;;
esac
ISO=$KIT/iso; ROOT=$ISO/sandbox
for seed in $SEEDS; do
 for s in ${STRATS:-random mcpfuzzer unified}; do
  rm -rf $ISO; mkdir -p $ISO; cp -a base_orig $ROOT
  if [[ $SRV == git* ]]; then mkdir -p $ISO/sandbox_secret $ISO/other_a $ISO/other_b; for d in $ROOT $ISO/sandbox_secret $ISO/other_a $ISO/other_b; do (cd $d && git init -q && git config user.email a@b && git config user.name n && echo x>.keep && git add -A && git commit -qm init); done; fi
  mkdir -p $ISO/sandbox_secret $ISO/other_a $ISO/other_b; echo TOP_SECRET_OUTSIDE > $ISO/sandbox_secret/secret.txt
  L=${s}_${SRV}_s${seed}
  rm -rf proxy_logs_gen_$L gen_$L.jsonl out_$L
  STRATEGY=$s ROOT=$ROOT GEN_LOG=gen_$L.jsonl SEED=$seed timeout 1500 ./venv/bin/python mcp_wrap3.py --mode tools --phase aggressive --protocol-phase realistic --protocol stdio --endpoint "node mcp_proxy_logger_gen.js $ROOT $KIT/proxy_logs_gen_$L" --runs $N --runs-per-type $N --timeout 30.0 --fs-root $KIT/fuzzer_fsroot --seed $seed --output-dir $KIT/out_$L --log-level WARNING --no-safety > /dev/null 2>&1
  echo "$L done"
 done
done
