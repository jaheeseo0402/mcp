#!/bin/bash
# libexif 0.6.14 + 하네스를 AFL++ 계측으로 빌드한다. 사용: bash build.sh  (afl-cc 필요)
set -e
[ -d libexif ] || git clone --depth 1 --branch libexif-0_6_14-release https://github.com/libexif/libexif.git
echo '#include <stdint.h>' > libexif/_stdint.h
SRC="$(ls libexif/libexif/*.c | grep -vx 'libexif/libexif/exif.c') libexif/libexif/canon/*.c libexif/libexif/olympus/*.c libexif/libexif/pentax/*.c"
afl-cc -O1 -g -D_FORTIFY_SOURCE=2 -DHAVE_CONFIG_H -I. -Ilibexif -include config.h $SRC harness.c -lm -o exifbin
echo "빌드 완료: ./exifbin"
