# Jazzer.js 시험 (old 서버, 서버 수정본 사용)
서버를 같은 프로세스에서 돌려야 계측이 되므로, 서버 진입 파일 사본(`inproc.js`)을 만들어 아래처럼 고쳤다 (원본 서버 그대로가 아님):
1. 맨 위의 `await Promise.all(...)`(폴더 존재 확인)를 `const __chk = Promise.all(...)`로 바꿈
2. 파일 끝 "Start server" 부분을 SDK의 `InMemoryTransport`로 서버·클라이언트를 연결하는 `init()` 함수로 교체, `client` export
3. esbuild로 CJS 번들(`bundle.cjs`) 생성 (Jazzer.js의 ESM 계측이 최상위 await 파일에서 문법 오류를 냈기 때문)
실행: `npx jazzer harness.cjs --sync=false -i bundle --disable_bug_detectors='.*' -- -max_total_time=60 -max_len=200`
`--disable_bug_detectors`를 빼면 Jazzer 내장 Path Traversal 탐지기가 "../../jaz_zer" 입력이 path.resolve에 닿는 순간 크래시로 보고한다. 서버의 폴더 검사 결과와 무관하게 울리므로 우리 지표(폴더 밖에서 성공한 호출)와 다르다.
