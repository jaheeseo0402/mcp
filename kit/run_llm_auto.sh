#!/bin/bash
# LLM 자동 생성 조건 (사람이 쓴 풀 없음). 사용: export ANTHROPIC_API_KEY=sk-...  후  bash run_llm_auto.sh "old agent" "1 2 3 4 5 6 7 8 9 10"
# 실행마다(서버×시드) LLM을 한 번 호출해 풀을 새로 만든다. 결과: runs_llm_auto/<서버>_llmblind|llmtree_s<시드>/ (llm_pool.json에 프롬프트·응답 저장)
cd "$(dirname "$0")"; mkdir -p runs_llm_auto
[ -n "$ANTHROPIC_API_KEY" ] || [ -n "$LLM_STUB" ] || { echo "ANTHROPIC_API_KEY가 필요해"; exit 1; }
for sd in $2; do for srv in $1; do for v in blind tree; do
  [ -f runs_llm_auto/${srv}_llm${v}_s${sd}/summary.json ] || echo "$srv $v $sd"
done; done; done | xargs -P ${P:-2} -L 1 bash -c './venv/bin/python afl_fuzz.py --server $0 --strategy llm --pool auto:$1 --seed $2 --per-tool ${N:-1000} --out runs_llm_auto/$0_llm$1_s$2 >> runs_llm_auto/log.txt 2>&1; echo "끝: $0 $1 $2"'
