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
