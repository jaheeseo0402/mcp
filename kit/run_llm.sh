#!/bin/bash
# LLM 풀 조건. 사용: bash run_llm.sh "old agent adro" "1 2 3 4 5 6 7 8 9 10"   결과: runs_llm/<서버>_llmblind|llmtree_s<시드>
cd "$(dirname "$0")"; mkdir -p runs_llm
for sd in $2; do for srv in $1; do for v in ${VARS:-blind tree}; do
  [ -f runs_llm/${srv}_llm${v}_s${sd}/summary.json ] || echo "$srv $v $sd"
done; done; done | xargs -P ${P:-2} -L 1 bash -c './venv/bin/python afl_fuzz.py --server $0 --strategy llm --pool llm/pool_$1.json --seed $2 --per-tool ${N:-1000} --out runs_llm/$0_llm$1_s$2 >> runs_llm/log.txt 2>&1; echo "끝: $0 $1 $2"'
