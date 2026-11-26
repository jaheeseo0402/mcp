/* tinyfmt: 연구용 구조 있는 입력 파서. 파일 구조:
   "TFMT" | 버전(1B: 1 또는 2) | 청크 수(1B, 최대 8) | 청크 반복
   청크 = 종류(4B ASCII) | 길이(2B, little endian) | 내용
   종류: HEAD DATA META IDXS TEXT
   일부러 심은 버그 5개(실행 중 [BUG n]을 stderr에 찍어 어떤 버그인지 확인한다. 실제 프로그램에서는 스택 해시로 대신한다)(1 HEAD 플래그 0x80 복사, 2 IDXS 범위, 3 TEXT 길이, 4 META 0으로 나눔, 5 DATA 널)(깊이가 서로 다름)가 있다. 비교 실험용이다. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

static int table[8] = {1,2,3,4,5,6,7,8};

static void parse(const uint8_t *buf, size_t n) {
    if (n < 6 || memcmp(buf, "TFMT", 4)) return;
    int ver = buf[4], cnt = buf[5];
    if (ver != 1 && ver != 2) return;
    if (cnt < 1 || cnt > 8) return;
    size_t pos = 6; int have_head = 0, have_data = 0; int data_len = 0;
    for (int i = 0; i < cnt; i++) {
        if (pos + 6 > n) return;
        const uint8_t *t = buf + pos; unsigned len = buf[pos+4] | (buf[pos+5] << 8);
        pos += 6;
        if (!memcmp(t, "HEAD", 4)) {
            char name[16];
            if (len < 2) return;
            int flags = buf[pos];
            have_head = 1;
            if (flags & 0x80) {            /* 버그 1: 플래그 0x80이면 길이 검사 없이 복사 */
                fprintf(stderr, "[BUG 1]\n");
                memcpy(name, buf + pos + 1, len - 1);
                if (name[0] == 'x') putchar('x');
            }
        } else if (!memcmp(t, "DATA", 4)) {
            if (!have_head) return;        /* HEAD가 먼저 와야 함 */
            if (len < 2) return;
            int comp = buf[pos], size = buf[pos+1];
            have_data = 1; data_len = size;
            if (comp == 3 && size == 0) {  /* 버그 5: 압축 3 + 크기 0이면 널 포인터 사용 */
                fprintf(stderr, "[BUG 5]\n"); volatile char *p = NULL; *p = 1;
            }
        } else if (!memcmp(t, "META", 4)) {
            if (!have_data) return;
            if (len < 1) return;
            int per = buf[pos];
            if (ver == 2) { if (per == 1) fprintf(stderr, "[BUG 4]\n"); printf("%d\n", data_len / (per - 1)); } /* 버그 4: per가 1이면 0으로 나눔 */
        } else if (!memcmp(t, "IDXS", 4)) {
            if (ver != 2) return;          /* 버전 2에서만 */
            if (len < 1) return;
            int idx = buf[pos];
            if (idx >= 8) { fprintf(stderr, "[BUG 2]\n"); __builtin_trap(); }   /* 버그 2: idx 범위 검사 없음(범위 밖 읽기 대신 트랩) */
            printf("%d\n", table[idx]);
        } else if (!memcmp(t, "TEXT", 4)) {
            if (!have_head) return;
            char text[64];
            if (len > 64 && ver == 2 && pos < n && buf[pos] == 'Z') {  /* 버그 3: 64바이트 넘는 TEXT를 검사 없이 복사 */
                fprintf(stderr, "[BUG 3]\n"); memcpy(text, buf + pos, len);
                putchar(text[0]);
            }
        } else return;
        pos += len;
        if (pos > n) return;
    }
}

int main(int argc, char **argv) {
    if (argc < 2) return 1;
    FILE *f = fopen(argv[1], "rb"); if (!f) return 1;
    uint8_t *buf = malloc(65536 + 16); size_t n = fread(buf, 1, 65536, f); fclose(f);
    parse(buf, n); free(buf); return 0;
}
