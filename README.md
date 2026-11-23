# MCP 서버 퍼징 연구 (폴더 구조 기반 경로 입력 생성)

MCP(Model Context Protocol) 서버의 경로 처리 결함(경로 이탈, CWE-22 계열)을 찾기 위해, 서버 폴더 구조를 읽어 경로 입력 4종류(경로 이탈 / 경계값 / 유효 / 준유효, 각 25%)를 만드는 제안 모델과, Random·mcp-fuzzer 0.7.0을 **같은 AFL식 틀**에서 비교한 실험 기록입니다.

> 연구 진행 중인 내용입니다. 논문 투고 전이므로 이 저장소는 비공개(private) 유지를 권장합니다.

| 폴더 | 내용 |
|---|---|
| `kit/` | 재현용 코드 (WSL2/Ubuntu에서 `bash setup.sh` → `bash quick_test.sh`). 자세한 명령은 `kit/README.md` |
| `results/` | 실행별 요약(JSON)과 실행별 지표 표(`per_run_metrics.csv`). 원본 호출 로그(수 GB)는 제외 |
| `docs/RESULTS.md` | 결과 표와 해석, 주의점 |
| `docs/DIFFICULTIES.md` | 어려웠던 점·실수·고친 것 |
| `docs/FEEDBACK_LOG.md` | 교수 피드백 7개 항목과 처리 상태 |
| `docs/ORACLE.md` | 실제 파일시스템 효과 기반 보안 오라클, 오라클 결과(서버 2종, 시드 10개) |
| `docs/INFO_LEVELS.md` | 서버 정보 수준(L0~L4)·생성 방식(four/rand) 비교, 이름 무작위화 결과 |
| `docs/EXTERNAL_REVIEW.md` | 외부 검토(다른 AI)의 조언과 반영·보류 내용 |
| `docs/ITEM4_SUMMARY.md` | 교수님 4번(AFL식 공통 틀) 정리 |
| `docs/OTHER_FUZZERS.md`, `docs/LLM_PLAN.md` | 다른 퍼저 시험, LLM 입력 생성 조건 |
| `docs/ASK_OTHER_AI.md` | 전체 진행 상황 정리(외부 상담용, 2차판) |

## 현재 결론 (2026-11-24, 오라클 기반)
서버 구조 정보를 어디까지 아느냐가 허용 폴더 경계 위반 발견을 가른다. 폴더 내부까지 알면 위반 0, 이웃 폴더 이름까지 알면 목록 노출, 그 안 파일 이름까지 알면 파일 내용 노출·파일 변경(old·agent, 시드 10개, 폴더 이름 무작위화에서도 유지). 같은 정보에서는 4종류 구성이 이름 단순 조합보다 위반을 적게 찾았다(정상 처리율·커버리지는 높음) → "4종류 구성이 필요하다"는 주장은 하지 않는다. 상세는 `docs/ORACLE.md`, `docs/INFO_LEVELS.md`.

## (이전) 한 줄 요약 — 응답 기반 지표, 4종류 구성 가정
서버 폴더 정보를 쓰는(gray-box) 제안 모델만 폴더 밖 경로 성공을 만들었고(old 서버 약 25, agent-infra 약 35~37 / 호출 3000개 규모 실행당), Random·mcp-fuzzer 포트는 거의 0이었다. 단, 이 주장은 **폴더 정보를 알 때**라는 조건부이며 "더 좋은 퍼저"라는 주장이 아니다.

## 한계 (먼저 밝힘)
- `afl_fuzz.py`는 AFL식 **재구현**이며 진짜 AFL/AFL++가 아니다. mcp-fuzzer 조건은 0.7.0 입력 생성기를 가져다 쓴 포트이고, 도구 그대로의 비교는 별도(`kit/run_real_tool.sh`).
- 크래시는 오류 문구 신호만 본다 (프로세스 비정상 종료 감지 없음). 모든 조건에서 크래시 0.
- 대상은 Node.js 파일시스템 계열 서버 3종(old / agent-infra / adpharm-ro).
- 폴더 정보를 모르는 black-box에서는 제안 모델도 0건이었다.
