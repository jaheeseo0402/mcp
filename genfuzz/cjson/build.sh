#!/bin/bash
# cJSON v1.7.8 + 하네스를 AFL++ 계측(+ASAN)으로 빌드한다. 사용: bash build.sh (afl-cc 필요)
set -e
[ -d cJSON ] || git clone --depth 1 --branch v1.7.8 https://github.com/DaveGamble/cJSON.git
AFL_USE_ASAN=1 afl-cc -O1 -g -I. harness.c cJSON/cJSON.c -lm -o cjsonbin
# crash 위치 분류용: 같은 코드를 ASAN으로만 빌드(오류 보고에서 종류와 맨 위 함수를 읽는다)
gcc -O1 -g -fsanitize=address -I. harness.c cJSON/cJSON.c -lm -o cjsonbin_tri
# 단계별로 어떤 줄·함수가 열리는지 분석하는 커버리지 빌드(analyze_cov.py 용)
gcc -O0 -g --coverage -I. harness.c cJSON/cJSON.c -lm -o cjsoncov
echo "빌드 완료: ./cjsonbin ./cjsonbin_tri ./cjsoncov"
