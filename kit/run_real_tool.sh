#!/bin/bash
# 진짜 mcp-fuzzer 0.7.0 도구를 그대로 실행. 사용: bash run_real_tool.sh <old|agent> <시드> [도구당 호출수]
# 한 번에 하나씩만 (iso/ 폴더를 공유). 결과: realtool/<서버>_s<시드>/
export KIT="$(cd "$(dirname "$0")"; pwd)"; cd $KIT
SRV=$1; seed=$2; N=${3:-1000}
case $SRV in
 agent) export SERVER_ENTRY_REAL=$KIT/srv/node_modules/@agent-infra/mcp-server-filesystem/dist/index.cjs SERVER_PRE=--allowed-directories ;;
 old) export SERVER_ENTRY_REAL=$KIT/node_modules/mcp-server-filesystem/dist/index.js SERVER_PRE= ;;
esac
export SERVER_BIN=$KIT/srvwrap.sh
OUT=$KIT/realtool/${SRV}_s${seed}; rm -rf $OUT; mkdir -p $OUT
ISO=$KIT/iso; ROOT=$ISO/sandbox
rm -rf $ISO; mkdir -p $ISO; cp -a base_orig $ROOT
mkdir -p $ISO/sandbox_secret $ISO/other_a $ISO/other_b; echo TOP_SECRET_OUTSIDE > $ISO/sandbox_secret/secret.txt
export COV_FILE=$OUT/cov.txt
timeout 2400 ./venv/bin/mcp-fuzzer --mode tools --phase aggressive --protocol-phase realistic --protocol stdio --endpoint "node mcp_proxy_logger_gen.js $ROOT $OUT/proxy" --runs $N --runs-per-type $N --timeout 30.0 --fs-root $KIT/fuzzer_fsroot --seed $seed --output-dir $OUT/out --log-level WARNING --no-safety > $OUT/stdout.txt 2>&1
echo "끝: $SRV $seed"
