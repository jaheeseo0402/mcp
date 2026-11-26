#!/bin/bash
# lodepng(최신 master) + 하네스를 AFL++ 계측(+ASAN)으로 빌드한다. 사용: bash build.sh (afl-c++ 필요)
set -e
[ -d lodepng ] || git clone --depth 1 https://github.com/lvandeve/lodepng.git
AFL_USE_ASAN=1 afl-c++ -O1 -g -I. harness.cpp lodepng/lodepng.cpp -o lodepngbin
g++ -O1 -g -fsanitize=address -I. harness.cpp lodepng/lodepng.cpp -o lodepngbin_tri
g++ -O0 -g --coverage -I. harness.cpp lodepng/lodepng.cpp -o lodepngcov
echo "빌드 완료: ./lodepngbin ./lodepngbin_tri ./lodepngcov"
