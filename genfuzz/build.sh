#!/bin/bash
# 타깃을 AFL++ 계측으로 컴파일한다. (afl-cc 가 있어야 한다: sudo apt install afl++ clang llvm)
cd "$(dirname "$0")"
afl-cc -O1 -g -D_FORTIFY_SOURCE=2 target/tinyfmt.c -o tinyfmt && echo "빌드 완료: ./tinyfmt"
