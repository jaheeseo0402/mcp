#!/bin/bash
# 결과 표 만들기. 사용: bash analyze.sh "old agent adro"     (generic)   /  RUNS=runs_real bash analyze.sh "old agent"
cd "$(dirname "$0")"
for s in $1; do ./venv/bin/python afl_an.py $s; done
