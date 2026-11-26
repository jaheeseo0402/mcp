#!/bin/bash
# libyaml 0.2.1 + 하네스를 AFL++ 계측(+ASAN)으로 빌드한다. 사용: bash build.sh (afl-cc 필요)
set -e
[ -d libyaml ] || git clone --depth 1 --branch 0.2.1 https://github.com/yaml/libyaml.git
DEF='-DYAML_VERSION_MAJOR=0 -DYAML_VERSION_MINOR=2 -DYAML_VERSION_PATCH=1 -DYAML_VERSION_STRING="0.2.1"'
SRC=$(ls libyaml/src/*.c)
AFL_USE_ASAN=1 afl-cc -O1 -g $DEF -Ilibyaml/include -Ilibyaml/src harness.c $SRC -o libyamlbin
gcc -O1 -g -fsanitize=address $DEF -Ilibyaml/include -Ilibyaml/src harness.c $SRC -o libyamlbin_tri
gcc -O0 -g --coverage $DEF -Ilibyaml/include -Ilibyaml/src harness.c $SRC -o libyamlcov
echo "빌드 완료: ./libyamlbin ./libyamlbin_tri ./libyamlcov"
