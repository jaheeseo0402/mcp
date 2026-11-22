#!/bin/bash
# API 없이: llm_raw/blind.txt, llm_raw/tree.txt 에 LLM 응답을 '고치지 않고' 저장해 둔 뒤 실행
# 사용: bash run_llm_raw.sh "old agent" "1 2 3 4 5 6 7 8 9 10"   결과: runs_llm_raw/
cd "$(dirname "$0")"; mkdir -p runs_llm_raw
for f in blind tree; do [ -s llm_raw/$f.txt ] || { echo "llm_raw/$f.txt 가 비어 있어"; exit 1; }; done
for sd in $2; do for srv in $1; do for v in blind tree; do
  [ -f runs_llm_raw/${srv}_llm${v}_s${sd}/summary.json ] || echo "$srv $v $sd"
done; done; done | xargs -P ${P:-2} -L 1 bash -c './venv/bin/python afl_fuzz.py --server $0 --strategy llm --pool raw:llm_raw/$1.txt --seed $2 --per-tool ${N:-1000} --out runs_llm_raw/$0_llm$1_s$2 >> runs_llm_raw/log.txt 2>&1; echo "끝: $0 $1 $2"'
