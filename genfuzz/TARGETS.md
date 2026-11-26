# 타깃 확장 (libexif 외 3개) — 실행 방법

실험 1(단계 L0~L3 × 10분)을 형식이 다른 타깃으로 늘린다. 타깃마다 폴더가 하나씩 있고 안에 `build.sh`, `harness.c(pp)`, `dict.txt`, `seeds/L0~L3`가 있다.

| 폴더 | 형식 | 버전 | 단계 정의 (L1 = 시그니처만, L2 = 필드 구조, L3 = 유효 샘플) |
|---|---|---|---|
| `cjson/` | JSON(텍스트) | cJSON v1.7.8 | L0 `A` / L1 `{` / L2 `{"k":` + 사전 / L3 유효 JSON 3개 |
| `libyaml/` | YAML(텍스트) | libyaml 0.2.1 | L0 `A` / L1 `---` / L2 `---\nk: ` + 사전 / L3 유효 YAML 3개 |
| `lodepng/` | PNG(바이너리, 청크 구조) | lodepng master | L0 `A` / L1 PNG 시그니처 8바이트 / L2 시그니처 + IHDR 청크 + 사전(청크 이름) / L3 유효 PNG 3개 |

공통: AFL++ 계측 + ASAN(`AFL_USE_ASAN=1`)으로 빌드하고 `-m none`으로 실행한다(ASAN이면 메모리 제한을 끈다). crash 종류와 위치는 ASAN으로만 빌드한 `<이름>bin_tri`로 다시 실행해 `오류 종류 + 맨 위 함수`로 구분한다.
lodepng는 CRC 검사를 끄는 설정(`ignore_crc`)을 넣었다. 끄지 않으면 L2·L3에서도 CRC에서 막혀 단계 차이를 못 본다.

## 실행 (타깃 폴더 안에서, 예: cjson)
```
cd ~/mcp/genfuzz/cjson
bash build.sh
for r in 1 2 3 4 5 6 7 8; do bash ../run_afl.sh L3 600 $r ./cjsonbin & done; wait
```
단계(L0~L3)와 반복 번호만 바꿔 같은 방식으로 돌린다. 한 번에 8개씩.

## 분석
```
python3 ../analyze1.py ./cjsonbin cjson ./cjsonbin_tri         # 시간 그래프 + 요약 (실험 1)
python3 ../analyze_cov.py cjson ./cjsoncov cJSON                # 단계별로 열린 함수·줄 (심화)
python3 ../analyze_bugs.py cjson ./cjsonbin_tri                 # 버그 종류·위치·몇 번 찾았나 (심화)
```

## 샌드박스 예비 확인 (90초, 반복 1번, ASAN 없음 — 논문 결과 아님, 파이프라인 검증용)
| 타깃 | L0 | L1 | L2 | L3 (edge 수, 끝 시점) | 읽는 법 |
|---|---|---|---|---|---|
| cJSON | 252 | 259 | 303 | 318 | 단계가 올라갈수록 완만하게 늘어남 |
| libyaml | 1794 | 1747 | 1860 | 1823 | 거의 차이 없음(YAML은 아무 글자나 문서로 받아들여 시그니처·구조 정보가 필요 없다) |
| lodepng | 39 | 37 | 47 | 924 | L0~L2는 거의 못 들어가고 L3(유효 PNG)에서 한 번에 열림 |
- lodepng에서 `analyze_cov.py`로 본 함수 수: L0 29, L1 29, L2 33, L3 181. L0~L2는 해독기 입구까지만 가고 압축 해제(Huffman)·필터 코드는 L3에서만 열린다.
- crash는 ASAN이 없는 이 검증 빌드에서는 0건이다. ASAN 빌드(`build.sh`)로 돌려야 메모리 오류를 잡는다.
- 형식이 엄격할수록 단계 차이가 크고(lodepng), 느슨할수록 작다(libyaml)는 가설을 세울 수 있다. 10분 × 반복으로 확인해야 한다.
