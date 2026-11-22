# LLM 입력 풀 생성 기록
생성 모델: Claude Sonnet 5.5, 한 번 생성해 파일로 고정(실험 중 호출 없음, 재현 가능). 두 조건 모두 "경로형 필드에 넣을 입력 문자열 목록"만 생성하게 함. 아래 프롬프트의 폴더 정보 부분만 다름.

## 공통
너는 MCP 파일시스템 서버의 경로 처리 결함(경로 이탈)을 찾는 퍼징 입력을 만든다. 서버는 허용된 폴더 하나 밖의 파일은 거절해야 한다. 경로형 인자(path, source, destination)에 넣을 문자열 60개 안팎을 JSON 배열로만 출력하라. 경로 이탈, 경계값(빈 값·긴 값·없는 파일), 유효 입력, 유효에 가까운 입력을 섞어라.

## pool_blind.json
(추가 정보 없음) 도구: read_file, write_file, list_directory, get_file_info, create_directory, move_file, search_files, directory_tree. 허용 폴더의 위치와 안의 파일 목록은 모른다.

## pool_tree.json
(폴더 정보 제공) 허용 폴더는 `{ROOT}`, 안에 sample.txt, data.json, blob.bin, subdir/nested.txt. 바로 옆(`{PARENT}`)에는 sandbox_secret/secret.txt, other_a, other_b가 있다. 실행 시 `{ROOT}`, `{PARENT}`는 실제 경로로 치환.

## 한계
- 생성 모델이 이 연구의 설계(4종·25%)를 이미 알고 있어 편향됐을 수 있다. 다른 LLM으로 풀을 다시 만들어 보는 것이 남은 일.
- 풀은 1회 생성·고정이라, 생성 때마다 달라지는 LLM의 변동성은 이번 실험에 반영되지 않는다.
