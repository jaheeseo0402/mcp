# 실험 키트 (WSL2 Ubuntu 기준) — 내가 직접 돌리기

## 0. 준비 (처음 한 번)
```
unzip mcpkit.zip && cd mcpkit
bash setup.sh          # node 없으면 안내가 나옴. 5분 이내
bash quick_test.sh     # 1분 확인. 표가 나오면 성공
```
## 1. 메인 실험 = AFL식 공통 틀 (슬라이드 21~22)
```
bash run_afl.sh generic "old agent adro" "1 2 3 4 5 6 7 8 9 10"   # 일반 시드, 90개 실행, 약 1~2시간
bash run_afl.sh real    "old agent"      "1 2 3 4 5 6 7 8 9 10"   # 실제 경로 시드 (공정성 확인)
bash analyze.sh "old agent adro"                                   # 결과 표
RUNS=runs_real bash analyze.sh "old agent"
```
- 중간에 꺼져도 같은 명령을 다시 치면 안 끝난 것만 이어서 돈다.
- 진행 확인: `ls runs/*/summary.json | wc -l`  (서버수×3×시드수가 되면 끝)
- 빨리 보고 싶으면 `N=100 bash run_afl.sh ...` (도구당 호출 100번)

## 2. 제안 모델 구성요소 빼기 (ablation)
```
bash run_abl.sh "old agent" "1 2 3 4 5 6" "full allstr nameonly noconst"
ls runs_abl/*/summary.json | wc -l   # 완료 개수 확인 (집계 스크립트는 아직 없음)
```
## 3. 진짜 mcp-fuzzer 0.7.0 도구 그대로 (슬라이드 22 아래)
```
for s in 1 2 3 4 5; do bash run_real_tool.sh old $s; bash run_real_tool.sh agent $s; done   # 한 번에 하나씩 순서대로
./venv/bin/python an_real.py old agent
```
## 3-2. LLM 입력 풀 조건 (llm/PROMPTS.md, docs/LLM_PLAN.md 참고)
```
bash run_llm.sh "old agent adro" "1 2 3 4 5 6 7 8 9 10"          # 결과: runs_llm/
RUNS=runs_llm bash analyze_llm.sh
```

## 4. 예전(AFL 틀 이전) 실험 = 슬라이드 17~20, 23~29의 원본
```
bash legacy/iso_all.sh        # 제안/랜덤/구성요소 제거/경로 종류 제거 (시드 6개)
bash legacy/iso_combo.sh  bash legacy/iso_ratio.sh  bash legacy/iso_sweep.sh  bash legacy/iso_rep.sh  bash legacy/iso_new.sh
```
- 각 스크립트가 만드는 결과: gen_*.jsonl (보낸 입력 기록), out_*/, proxy_logs_gen_*/
- 집계: legacy/stats20.py, legacy/table.py, legacy/an6.py, an7.py (옛 스크립트라 경로 수정이 필요할 수 있음 — 시험 안 함)
- 이 폴더의 시험 범위: `legacy/run_iso.sh 10 1` 한 번이 도는 것까지만 확인. 전체는 시험 안 함.

## 5. 한계 (정직하게)
- afl_fuzz.py는 "AFL식 재구현"이지 진짜 AFL/AFL++가 아님. mcp-fuzzer 조건은 0.7.0 입력 생성기를 가져다 쓴 포트.
- 크래시는 오류 문구 신호만 본다 (프로세스 비정상 종료 감지는 아직 없음).
- 서버 버전은 package.json에 ^ 범위로 되어 있고 내가 쓴 버전은 mcp-server-filesystem 0.6.2, @agent-infra 1.2.29, @adpharm 0.1.2. 다르게 설치되면 결과가 달라질 수 있어 npm ls로 확인.
