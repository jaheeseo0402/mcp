#!/bin/bash
# 설치 확인용 (1~2분): 서버 old, 시드 1, 도구당 20번만
cd "$(dirname "$0")"
for st in random mcpfuzzer ours; do
  ./venv/bin/python afl_fuzz.py --server old --strategy $st --seed 1 --per-tool 20 --out test/old_${st}_s1
done
RUNS=test ./venv/bin/python afl_an.py old
